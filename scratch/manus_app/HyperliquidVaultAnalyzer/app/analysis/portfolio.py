"""
Barbell portfolio construction.

Inputs : list of per-vault metric records (dicts with at least
         address, name, tvl, return_all, mdd, recovery_factor,
         drawdown_now, score_stable, score_recovery).

Output : portfolio dict with two legs ("stable", "recovery"), each
         containing selected vaults and their weights, plus a combined
         "holdings" view summing to 1.0.

Design rules (from user spec):
- Stable leg     : 50% of total capital, populated by vaults with high
                   return / low MDD; weights inside the leg are inverse-
                   risk weighted (1/MDD), normalized.
- Recovery leg   : 50% of total capital, populated by vaults that are
                   currently deep in drawdown but have historically high
                   recovery factors; weights inside the leg are
                   recovery_factor weighted, normalized.
- Total selected vaults across both legs MUST be <= 20.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

EPS = 1e-9


@dataclass
class BarbellParams:
    max_total: int = 20
    stable_ratio: float = 0.5
    recovery_ratio: float = 0.5
    # Filters
    min_history_age_ms: int = 0  # placeholder for future use
    min_tvl: float = 50_000.0  # ignore very small vaults
    # Recovery leg specific
    min_drawdown_now: float = 0.05  # vault must currently be down at least 5%
    min_recovery_factor: float = 0.2  # historically resilient


def _normalize(weights: List[float]) -> List[float]:
    s = sum(w for w in weights if w > 0)
    if s <= EPS:
        n = len(weights)
        return [1.0 / n] * n if n > 0 else []
    return [max(w, 0.0) / s for w in weights]


def build_barbell_portfolio(
    metrics: List[Dict[str, Any]],
    params: Optional[BarbellParams] = None,
) -> Dict[str, Any]:
    p = params or BarbellParams()
    if not metrics:
        return {"params": p.__dict__, "stable": [], "recovery": [], "holdings": []}

    # Pre-filter: ignore vaults with no usable history (mdd==0 and return_all==0)
    # and below min TVL.
    base = [m for m in metrics if (m.get("tvl") or 0) >= p.min_tvl]

    # Split target counts (50/50 by default)
    stable_target = max(1, int(round(p.max_total * p.stable_ratio)))
    recovery_target = max(1, p.max_total - stable_target)

    # ---- Stable leg ------------------------------------------------------
    stable_pool = [
        m for m in base
        if m.get("mdd", 0.0) > 0 and m.get("return_all", 0.0) > 0
    ]
    stable_pool.sort(key=lambda m: m.get("score_stable", 0.0), reverse=True)
    stable_sel = stable_pool[:stable_target]
    inv_risk = [1.0 / max(m.get("mdd", EPS), EPS) for m in stable_sel]
    stable_weights = _normalize(inv_risk)

    # ---- Recovery leg ----------------------------------------------------
    recovery_pool = [
        m for m in base
        if m.get("drawdown_now", 0.0) >= p.min_drawdown_now
        and m.get("recovery_factor", 0.0) >= p.min_recovery_factor
    ]
    recovery_pool.sort(key=lambda m: m.get("score_recovery", 0.0), reverse=True)
    recovery_sel = recovery_pool[:recovery_target]
    rec_weights = _normalize([max(m.get("recovery_factor", 0.0), 0.0) for m in recovery_sel])

    # If one of the legs is empty, give all capital to the other leg so we
    # always return a usable portfolio.
    actual_stable_ratio = p.stable_ratio
    actual_recovery_ratio = p.recovery_ratio
    if not stable_sel and recovery_sel:
        actual_recovery_ratio = 1.0
        actual_stable_ratio = 0.0
    elif not recovery_sel and stable_sel:
        actual_stable_ratio = 1.0
        actual_recovery_ratio = 0.0

    def _to_rows(sel, weights, leg, leg_ratio):
        rows = []
        for m, w in zip(sel, weights):
            rows.append(
                {
                    "leg": leg,
                    "address": m.get("address"),
                    "name": m.get("name"),
                    "tvl": m.get("tvl"),
                    "return_all": m.get("return_all"),
                    "mdd": m.get("mdd"),
                    "drawdown_now": m.get("drawdown_now"),
                    "recovery_factor": m.get("recovery_factor"),
                    "leg_weight": w,                          # within the leg
                    "weight": w * leg_ratio,                  # within the full portfolio
                }
            )
        return rows

    stable_rows = _to_rows(stable_sel, stable_weights, "stable", actual_stable_ratio)
    recovery_rows = _to_rows(recovery_sel, rec_weights, "recovery", actual_recovery_ratio)
    holdings = stable_rows + recovery_rows

    # Final safety renormalization (in case both legs are empty)
    s = sum(h["weight"] for h in holdings)
    if s > EPS:
        for h in holdings:
            h["weight"] = h["weight"] / s

    return {
        "params": {
            "max_total": p.max_total,
            "stable_ratio": actual_stable_ratio,
            "recovery_ratio": actual_recovery_ratio,
            "min_tvl": p.min_tvl,
            "min_drawdown_now": p.min_drawdown_now,
            "min_recovery_factor": p.min_recovery_factor,
        },
        "stable": stable_rows,
        "recovery": recovery_rows,
        "holdings": holdings,
    }


def diff_portfolios(prev: Optional[Dict[str, Any]], curr: Dict[str, Any]) -> Dict[str, Any]:
    """Return added/removed/weight-changed vaults between two portfolios.

    A vault is considered weight-changed if absolute weight diff > 1%.
    """
    def _addr_set(p: Optional[Dict[str, Any]]):
        if not p:
            return {}, set()
        m = {h["address"]: h for h in p.get("holdings", [])}
        return m, set(m.keys())

    prev_map, prev_set = _addr_set(prev)
    curr_map, curr_set = _addr_set(curr)

    added = sorted(curr_set - prev_set)
    removed = sorted(prev_set - curr_set)
    weight_changes = []
    for a in sorted(curr_set & prev_set):
        if abs(curr_map[a]["weight"] - prev_map[a]["weight"]) > 0.01:
            weight_changes.append(
                {
                    "address": a,
                    "name": curr_map[a].get("name"),
                    "prev_weight": prev_map[a]["weight"],
                    "curr_weight": curr_map[a]["weight"],
                }
            )
    return {
        "added": [curr_map[a] for a in added],
        "removed": [prev_map[a] for a in removed],
        "weight_changes": weight_changes,
        "changed": bool(added or removed or weight_changes),
    }
