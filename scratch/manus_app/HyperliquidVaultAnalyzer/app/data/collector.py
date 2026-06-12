"""
Data collector: orchestrates fetching the top-N USER vault summaries and
their detailed time series, then persists everything via Storage.

Pipeline:
  1. Fetch all vault summaries (single GET).
  2. Normalize -> records.
  3. Apply Protocol Vault exclusion filter -> User Vault candidates.
  4. Take TVL top-N (default 200) of User Vaults.
  5. For each, fetch vault details (concurrent, with backoff/retry).
  6. Persist summaries, history, and a compact details snapshot.
"""
from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.data.filters import FilterStats, filter_user_vaults
from app.data.hyperliquid_client import HyperliquidClient
from app.data.storage import Storage


LOG = logging.getLogger(__name__)


@dataclass
class CollectionResult:
    total_vaults_seen: int
    user_vault_pool_size: int
    top_n_selected: int
    details_fetched: int
    details_failed: int
    history_points_total: int
    elapsed_seconds: float
    filter_stats: Dict[str, int] = field(default_factory=dict)


class Collector:
    def __init__(
        self,
        storage: Storage,
        client: Optional[HyperliquidClient] = None,
        top_n: int = 200,
        concurrency: int = 5,
        timeout: int = 20,
        retry_max: int = 4,
        retry_base_sec: float = 0.6,
        # Protocol vault exclusion (User Vault only)
        exclude_protocol_vaults: bool = True,
        exclude_child_vaults: bool = True,
        exclude_vault_addresses: Optional[List[str]] = None,
        exclude_leader_addresses: Optional[List[str]] = None,
        exclude_name_substrings: Optional[List[str]] = None,
    ) -> None:
        self.storage = storage
        self.client = client or HyperliquidClient(
            timeout=timeout,
            concurrency=concurrency,
            retry_max=retry_max,
            retry_base_sec=retry_base_sec,
        )
        self.top_n = top_n
        self.exclude_protocol_vaults = exclude_protocol_vaults
        self.exclude_child_vaults = exclude_child_vaults
        self.exclude_vault_addresses = exclude_vault_addresses or []
        self.exclude_leader_addresses = exclude_leader_addresses or []
        self.exclude_name_substrings = exclude_name_substrings or []

    def run(self, progress_cb: Optional[Callable[[str, float], None]] = None) -> CollectionResult:
        def report(msg: str, frac: float) -> None:
            if progress_cb is not None:
                try:
                    progress_cb(msg, frac)
                except Exception:  # noqa: BLE001
                    pass

        t0 = time.time()
        report("Fetching vault summaries...", 0.05)
        raw = self.client.fetch_vault_summaries()
        self.storage.write_json_snapshot("vault_summaries_raw", raw)
        records = self.client.normalize_summaries(raw)
        total_seen = len(records)
        LOG.info("Fetched %d vault summaries", total_seen)

        # ---- User Vault filter (excludes Protocol Vaults like HLP) -----
        report("Filtering Protocol Vaults out (User Vaults only)...", 0.10)
        user_records, fstats = filter_user_vaults(
            records,
            exclude_protocol=self.exclude_protocol_vaults,
            exclude_child=self.exclude_child_vaults,
            exclude_addresses=self.exclude_vault_addresses,
            exclude_leaders=self.exclude_leader_addresses,
            exclude_name_substrings=self.exclude_name_substrings,
            only_open=True,
        )
        LOG.info(
            "Protocol filter: in=%d, user_pool=%d, excluded=%s",
            fstats.total_in, len(user_records), fstats.as_dict(),
        )

        report("Selecting top %d USER vaults by TVL..." % self.top_n, 0.15)
        # `top_n_by_tvl` already sorts and slices; only_open already enforced.
        top = self.client.top_n_by_tvl(user_records, n=self.top_n, only_open=True)
        self.storage.upsert_vault_summaries(top)
        addresses = [r["address"] for r in top]

        report("Fetching vault details (%d items)..." % len(addresses), 0.25)
        details_map = self.client.fetch_vault_details_bulk(addresses)
        details_failed = len(addresses) - len(details_map)
        report("Persisting time series...", 0.75)

        history_points = 0
        n = max(1, len(addresses))
        for i, addr in enumerate(addresses):
            details = details_map.get(addr)
            if not details:
                continue
            history = self.client.extract_alltime_history(details)
            if history:
                self.storage.replace_vault_history(addr, history)
                history_points += len(history)
            if i % 25 == 0:
                report(
                    "Persisting time series (%d/%d)..." % (i + 1, n),
                    0.75 + 0.2 * (i / n),
                )

        compact = {
            addr: {
                "name": d.get("name"),
                "apr": d.get("apr"),
                "leader": d.get("leader"),
                "isClosed": d.get("isClosed"),
            }
            for addr, d in details_map.items()
        }
        self.storage.write_json_snapshot("vault_details_compact", compact)
        # Also persist the filter stats for transparency.
        self.storage.write_json_snapshot("filter_stats", fstats.as_dict())

        elapsed = time.time() - t0
        report("Collection complete (%.1fs)." % elapsed, 1.0)
        return CollectionResult(
            total_vaults_seen=total_seen,
            user_vault_pool_size=len(user_records),
            top_n_selected=len(top),
            details_fetched=len(details_map),
            details_failed=details_failed,
            history_points_total=history_points,
            elapsed_seconds=round(elapsed, 2),
            filter_stats=fstats.as_dict(),
        )
