"""
Hyperliquid API client.

Two endpoints are used:

1) Vault summary list (single GET, returns ~9000+ vaults):
   GET https://stats-data.hyperliquid.xyz/Mainnet/vaults

2) Per-vault detailed time series:
   POST https://api.hyperliquid.xyz/info
        body = {"type":"vaultDetails","vaultAddress":"0x..."}

Bulk fetching uses asyncio + aiohttp with:
  - bounded concurrency (default 5),
  - jittered exponential backoff,
  - explicit handling of HTTP 429 (Too Many Requests) with Retry-After
    if the server provides it,
  - a small inter-request gap to keep average request rate well under
    Hyperliquid's published per-IP limits.
"""
from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import requests


LOG = logging.getLogger(__name__)

INFO_URL = "https://api.hyperliquid.xyz/info"
STATS_URL = "https://stats-data.hyperliquid.xyz/Mainnet/vaults"


class HyperliquidClient:
    def __init__(
        self,
        timeout: int = 20,
        concurrency: int = 5,
        retry_max: int = 4,
        retry_base_sec: float = 0.6,
        request_gap_sec: float = 0.05,
    ) -> None:
        self.timeout = timeout
        self.concurrency = max(1, int(concurrency))
        self.retry_max = max(1, int(retry_max))
        self.retry_base_sec = float(retry_base_sec)
        self.request_gap_sec = float(request_gap_sec)

    # ---- 1) Vault summaries ------------------------------------------------
    def fetch_vault_summaries(self) -> List[Dict[str, Any]]:
        """Return the raw stats-data list (each item has 'summary' and 'pnls')."""
        last_err: Optional[Exception] = None
        for attempt in range(self.retry_max):
            try:
                r = requests.get(STATS_URL, timeout=self.timeout)
                r.raise_for_status()
                data = r.json()
                if not isinstance(data, list):
                    raise ValueError("Unexpected vault summaries payload shape")
                return data
            except Exception as e:  # noqa: BLE001
                last_err = e
                sleep = self.retry_base_sec * (2 ** attempt) + random.uniform(0, 0.3)
                LOG.warning("Vault summaries fetch failed (try %d): %s; sleeping %.1fs",
                            attempt + 1, e, sleep)
                __import__("time").sleep(sleep)
        raise RuntimeError(f"Failed to fetch vault summaries after retries: {last_err}")

    @staticmethod
    def normalize_summaries(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Flatten the raw stats-data items to a uniform record."""
        out: List[Dict[str, Any]] = []
        for it in raw:
            s = it.get("summary") or {}
            try:
                tvl = float(s.get("tvl", 0.0) or 0.0)
            except (TypeError, ValueError):
                tvl = 0.0
            rel = (s.get("relationship") or {}).get("type") if isinstance(s.get("relationship"), dict) else None
            out.append(
                {
                    "address": s.get("vaultAddress"),
                    "name": s.get("name"),
                    "leader": s.get("leader"),
                    "tvl": tvl,
                    "is_closed": bool(s.get("isClosed", False)),
                    "relationship": rel,
                    "created_time_ms": int(s.get("createTimeMillis") or 0),
                }
            )
        return [x for x in out if x["address"]]

    @staticmethod
    def top_n_by_tvl(records: List[Dict[str, Any]], n: int = 200, only_open: bool = True) -> List[Dict[str, Any]]:
        rows = [r for r in records if (not only_open or not r["is_closed"])]
        rows.sort(key=lambda r: r["tvl"], reverse=True)
        return rows[:n]

    # ---- 2) Vault details --------------------------------------------------
    def fetch_vault_details(self, address: str) -> Dict[str, Any]:
        body = {"type": "vaultDetails", "vaultAddress": address}
        r = requests.post(INFO_URL, json=body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    async def _fetch_one_async(
        self,
        session: aiohttp.ClientSession,
        sem: asyncio.Semaphore,
        address: str,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        body = {"type": "vaultDetails", "vaultAddress": address}
        async with sem:
            for attempt in range(self.retry_max):
                try:
                    async with session.post(INFO_URL, json=body, timeout=self.timeout) as resp:
                        if resp.status == 429:
                            retry_after = resp.headers.get("Retry-After")
                            try:
                                wait = float(retry_after) if retry_after else self.retry_base_sec * (2 ** attempt)
                            except ValueError:
                                wait = self.retry_base_sec * (2 ** attempt)
                            wait += random.uniform(0, 0.4)
                            LOG.warning("429 for %s (try %d) -> sleeping %.2fs", address, attempt + 1, wait)
                            await asyncio.sleep(wait)
                            continue
                        if 500 <= resp.status < 600:
                            wait = self.retry_base_sec * (2 ** attempt) + random.uniform(0, 0.4)
                            LOG.warning("HTTP %d for %s (try %d) -> sleeping %.2fs",
                                        resp.status, address, attempt + 1, wait)
                            await asyncio.sleep(wait)
                            continue
                        resp.raise_for_status()
                        data = await resp.json()
                        # gentle pacing between successful calls inside the same worker slot
                        if self.request_gap_sec > 0:
                            await asyncio.sleep(self.request_gap_sec)
                        return address, data
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    wait = self.retry_base_sec * (2 ** attempt) + random.uniform(0, 0.4)
                    LOG.warning("vaultDetails network error for %s (try %d): %s; sleep %.2fs",
                                address, attempt + 1, e, wait)
                    await asyncio.sleep(wait)
                except Exception as e:  # noqa: BLE001
                    LOG.exception("vaultDetails unexpected error for %s: %s", address, e)
                    break
            return address, None

    async def _fetch_many_async(self, addresses: List[str]) -> List[Tuple[str, Optional[Dict[str, Any]]]]:
        sem = asyncio.Semaphore(self.concurrency)
        timeout = aiohttp.ClientTimeout(total=self.timeout * 6)
        connector = aiohttp.TCPConnector(limit=self.concurrency, ttl_dns_cache=300)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            tasks = [self._fetch_one_async(session, sem, a) for a in addresses]
            return await asyncio.gather(*tasks)

    def fetch_vault_details_bulk(self, addresses: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch details for many vaults concurrently. Returns address -> details."""
        results = asyncio.run(self._fetch_many_async(addresses))
        return {addr: data for addr, data in results if data is not None}

    # ---- helpers -----------------------------------------------------------
    @staticmethod
    def extract_alltime_history(details: Dict[str, Any]) -> List[Tuple[int, float, float]]:
        """Return (ts_ms, account_value, pnl) tuples from the 'allTime' portfolio period.

        Falls back to 'month' or 'week' if 'allTime' is absent or empty.
        """
        portfolio = details.get("portfolio") or []
        priority = ["allTime", "month", "week", "day"]
        period_map: Dict[str, Dict[str, Any]] = {}
        for entry in portfolio:
            if isinstance(entry, list) and len(entry) >= 2:
                period_map[entry[0]] = entry[1] or {}
        chosen = None
        for p in priority:
            d = period_map.get(p) or {}
            if d.get("accountValueHistory"):
                chosen = d
                break
        if not chosen:
            return []
        avh = chosen.get("accountValueHistory") or []
        ph = {int(ts): float(v) for ts, v in (chosen.get("pnlHistory") or [])}
        out: List[Tuple[int, float, float]] = []
        for item in avh:
            try:
                ts = int(item[0])
                av = float(item[1])
                pnl = float(ph.get(ts, 0.0))
                out.append((ts, av, pnl))
            except Exception:  # noqa: BLE001
                continue
        return out
