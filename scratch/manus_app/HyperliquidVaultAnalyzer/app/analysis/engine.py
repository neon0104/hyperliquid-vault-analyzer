"""
Analysis engine: read history from Storage, compute metrics for each
top-N vault, persist the metrics, and build the Barbell portfolio.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.analysis.metrics import compute_metrics
from app.analysis.portfolio import BarbellParams, build_barbell_portfolio
from app.data.storage import Storage


LOG = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    metrics_count: int
    portfolio: Dict[str, Any]


class AnalysisEngine:
    def __init__(self, storage: Storage, params: Optional[BarbellParams] = None) -> None:
        self.storage = storage
        self.params = params or BarbellParams()

    def run(self, top_n: int = 200) -> AnalysisResult:
        vaults = self.storage.get_top_vaults_by_tvl(n=top_n, only_open=True)
        all_metrics: List[Dict[str, Any]] = []
        for v in vaults:
            history = self.storage.get_vault_history(v["address"])
            m = compute_metrics(history)
            self.storage.upsert_metrics(v["address"], m)
            row = {**v, **m}
            all_metrics.append(row)
        portfolio = build_barbell_portfolio(all_metrics, self.params)
        self.storage.save_portfolio_snapshot(portfolio)
        return AnalysisResult(metrics_count=len(all_metrics), portfolio=portfolio)
