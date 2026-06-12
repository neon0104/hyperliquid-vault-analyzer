"""
Protocol Vault filtering: keep only User Vaults.

Hyperliquid hosts two flavors of vaults:

  * Protocol vaults  - operated by the protocol itself (e.g. HLP and its
                       child strategies/liquidators). These are NOT user-
                       operated and we MUST exclude them from the analysis
                       per product requirement.
  * User vaults      - vaults created by ordinary users via the vault UI.

This module performs the exclusion using three independent signals (any
match -> the vault is treated as a Protocol Vault and removed):

  1. The vault's own address is in `exclude_vault_addresses`.
  2. The vault's leader address is in `exclude_leader_addresses`.
  3. (Optional) the vault is a relationship 'child' (e.g. an HLP strategy
     vault), which is essentially never a user-operated vault.
  4. The vault's name contains any blacklisted substring (case-insensitive),
     such as "HLP", "Hyperliquidity Provider", or "Liquidator".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass
class FilterStats:
    total_in: int = 0
    excluded_closed: int = 0
    excluded_address: int = 0
    excluded_leader: int = 0
    excluded_child: int = 0
    excluded_name: int = 0

    @property
    def total_excluded_protocol(self) -> int:
        return (
            self.excluded_address
            + self.excluded_leader
            + self.excluded_child
            + self.excluded_name
        )

    def as_dict(self) -> Dict[str, int]:
        return {
            "total_in": self.total_in,
            "excluded_closed": self.excluded_closed,
            "excluded_address": self.excluded_address,
            "excluded_leader": self.excluded_leader,
            "excluded_child": self.excluded_child,
            "excluded_name": self.excluded_name,
            "total_excluded_protocol": self.total_excluded_protocol,
        }


def _norm_addr(a: str | None) -> str:
    return (a or "").strip().lower()


def filter_user_vaults(
    records: Iterable[Dict],
    *,
    exclude_protocol: bool = True,
    exclude_child: bool = True,
    exclude_addresses: Sequence[str] = (),
    exclude_leaders: Sequence[str] = (),
    exclude_name_substrings: Sequence[str] = (),
    only_open: bool = True,
) -> Tuple[List[Dict], FilterStats]:
    """Return (filtered_records, stats).

    `records` is the normalized output of HyperliquidClient.normalize_summaries.
    Each record is expected to have keys:
        address, name, leader, tvl, is_closed, relationship, created_time_ms
    """
    stats = FilterStats()
    addr_block = {_norm_addr(a) for a in exclude_addresses if a}
    leader_block = {_norm_addr(a) for a in exclude_leaders if a}
    name_block_lower = [s.lower() for s in exclude_name_substrings if s]

    out: List[Dict] = []
    for r in records:
        stats.total_in += 1
        if only_open and r.get("is_closed"):
            stats.excluded_closed += 1
            continue
        if exclude_protocol and _norm_addr(r.get("address")) in addr_block:
            stats.excluded_address += 1
            continue
        if exclude_protocol and _norm_addr(r.get("leader")) in leader_block:
            stats.excluded_leader += 1
            continue
        if exclude_child and (r.get("relationship") == "child"):
            stats.excluded_child += 1
            continue
        if exclude_protocol and name_block_lower:
            name_l = (r.get("name") or "").lower()
            if any(sub in name_l for sub in name_block_lower):
                stats.excluded_name += 1
                continue
        out.append(r)
    return out, stats
