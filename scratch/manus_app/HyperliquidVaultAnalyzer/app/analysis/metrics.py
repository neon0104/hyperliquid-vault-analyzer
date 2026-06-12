"""
Per-vault metric computation.

Given a list of (ts_ms, account_value, pnl) points, compute:
- return_all      : total return ratio over the available window
- mdd             : maximum drawdown (positive number, e.g. 0.42 = 42%)
- recovery_factor : cumulative_return / mdd (capped to a large finite value
                    when mdd ~= 0)
- drawdown_now    : current drawdown from the all-time peak (positive)
- score_stable    : ranking score for the "stable" Barbell leg
                    = max(return_all, 0) / max(mdd, eps)
- score_recovery  : ranking score for the "recovery" Barbell leg
                    = drawdown_now * recovery_factor
                    (high when currently down a lot and historically resilient)

All inputs are plain floats; no pandas required at runtime so the bundle
stays small.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple


EPS = 1e-9


def compute_metrics(history: List[Tuple[int, float, float]]) -> Dict[str, float]:
    """Compute metrics from (ts_ms, account_value, pnl) tuples."""
    if not history or len(history) < 2:
        return {
            "return_all": 0.0,
            "mdd": 0.0,
            "recovery_factor": 0.0,
            "drawdown_now": 0.0,
            "score_stable": 0.0,
            "score_recovery": 0.0,
        }

    # Sort defensively
    h = sorted(history, key=lambda r: r[0])
    values = [v for _, v, _ in h if v > 0]
    if len(values) < 2:
        return {
            "return_all": 0.0,
            "mdd": 0.0,
            "recovery_factor": 0.0,
            "drawdown_now": 0.0,
            "score_stable": 0.0,
            "score_recovery": 0.0,
        }

    initial = values[0]
    current = values[-1]
    return_all = (current - initial) / max(initial, EPS)

    # MDD using running peak
    peak = values[0]
    mdd = 0.0
    for v in values:
        if v > peak:
            peak = v
        dd = (peak - v) / max(peak, EPS)
        if dd > mdd:
            mdd = dd

    # Current drawdown from all-time peak
    all_time_peak = max(values)
    drawdown_now = (all_time_peak - current) / max(all_time_peak, EPS)

    # Recovery factor (cumulative return divided by MDD)
    if mdd <= EPS:
        recovery_factor = max(return_all, 0.0) * 100.0  # very small MDD -> very high
    else:
        recovery_factor = return_all / mdd

    # Scoring
    score_stable = max(return_all, 0.0) / max(mdd, EPS)
    score_recovery = drawdown_now * max(recovery_factor, 0.0)

    # Guard against NaN/inf
    def _clean(x: float) -> float:
        if x is None or math.isnan(x) or math.isinf(x):
            return 0.0
        return float(x)

    return {
        "return_all": _clean(return_all),
        "mdd": _clean(mdd),
        "recovery_factor": _clean(recovery_factor),
        "drawdown_now": _clean(drawdown_now),
        "score_stable": _clean(score_stable),
        "score_recovery": _clean(score_recovery),
    }
