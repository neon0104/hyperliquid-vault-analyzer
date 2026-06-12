"""
Background scheduler for periodic data collection, analysis and alerts.

Three trigger types are scheduled:
  - 'collect_and_analyze' : every N minutes (config.collection_interval_minutes).
                            Runs the full pipeline and triggers (a) and (b)
                            alerts based on results.
  - 'daily_report'        : if enabled, fires at HH:MM every day.
  - 'weekly_report'       : if enabled, fires at HH:MM every requested weekday.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.analysis.engine import AnalysisEngine
from app.analysis.portfolio import BarbellParams
from app.core.config import AppConfig, ConfigManager
from app.data.collector import Collector
from app.data.storage import Storage
from app.notifications.alert_manager import AlertManager
from app.notifications.base import build_provider


LOG = logging.getLogger(__name__)


def _hhmm(s: str):
    try:
        h, m = s.split(":")
        return int(h), int(m)
    except Exception:  # noqa: BLE001
        return 9, 0


class AppScheduler:
    """Wraps APScheduler with the three required triggers."""

    def __init__(
        self,
        config_manager: ConfigManager,
        on_pipeline_done: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self.cm = config_manager
        self.scheduler = BackgroundScheduler()
        self.on_pipeline_done = on_pipeline_done
        self._jobs_installed = False

    # ------------------------------------------------------------------
    def _make_components(self):
        cfg: AppConfig = self.cm.config
        data_dir = self.cm.ensure_data_dir()
        storage = Storage(data_dir)
        collector = Collector(
            storage,
            top_n=cfg.top_n_vaults,
            concurrency=cfg.request_concurrency,
            timeout=cfg.request_timeout_sec,
            retry_max=cfg.request_retry_max,
            retry_base_sec=cfg.request_retry_base_sec,
            exclude_protocol_vaults=cfg.exclude_protocol_vaults,
            exclude_child_vaults=cfg.exclude_child_vaults,
            exclude_vault_addresses=cfg.exclude_vault_addresses,
            exclude_leader_addresses=cfg.exclude_leader_addresses,
            exclude_name_substrings=cfg.exclude_name_substrings,
        )
        engine = AnalysisEngine(
            storage,
            params=BarbellParams(
                max_total=cfg.max_portfolio_size,
                stable_ratio=cfg.stable_group_ratio,
                recovery_ratio=cfg.recovery_group_ratio,
            ),
        )
        provider = build_provider(cfg.to_dict())
        alerts = AlertManager(provider)
        return cfg, storage, collector, engine, alerts

    # ------------------------------------------------------------------
    def run_pipeline_once(self) -> dict:
        cfg, storage, collector, engine, alerts = self._make_components()
        prev_portfolio = storage.latest_portfolio_snapshot()
        try:
            collection = collector.run()
        except Exception as e:  # noqa: BLE001
            LOG.exception("Collection failed: %s", e)
            return {"ok": False, "error": str(e)}
        result = engine.run(top_n=cfg.top_n_vaults)
        portfolio = result.portfolio
        # Attach collection stats for visibility downstream
        portfolio["collection_stats"] = {
            "total_vaults_seen": collection.total_vaults_seen,
            "user_vault_pool_size": collection.user_vault_pool_size,
            "top_n_selected": collection.top_n_selected,
            "details_fetched": collection.details_fetched,
            "details_failed": collection.details_failed,
            "history_points_total": collection.history_points_total,
            "elapsed_seconds": collection.elapsed_seconds,
            "filter_stats": collection.filter_stats,
        }

        # (a) portfolio change alert
        if cfg.alert_on_portfolio_change:
            try:
                alerts.alert_portfolio_change(prev_portfolio, portfolio)
            except Exception as e:  # noqa: BLE001
                LOG.warning("Portfolio change alert failed: %s", e)

        # (b) big move alerts
        try:
            alerts.alert_big_moves(portfolio.get("holdings", []), cfg.big_move_threshold_pct)
        except Exception as e:  # noqa: BLE001
            LOG.warning("Big move alerts failed: %s", e)

        payload = {
            "ok": True,
            "portfolio": portfolio,
            "metrics_count": result.metrics_count,
            "collection_stats": portfolio["collection_stats"],
        }
        if self.on_pipeline_done:
            try:
                self.on_pipeline_done(payload)
            except Exception:  # noqa: BLE001
                pass
        return payload

    def send_daily_report(self) -> bool:
        cfg, storage, _, _, alerts = self._make_components()
        portfolio = storage.latest_portfolio_snapshot() or {}
        return alerts.send_periodic_report(portfolio, period_label="Daily")

    def send_weekly_report(self) -> bool:
        cfg, storage, _, _, alerts = self._make_components()
        portfolio = storage.latest_portfolio_snapshot() or {}
        return alerts.send_periodic_report(portfolio, period_label="Weekly")

    # ------------------------------------------------------------------
    def install_jobs(self) -> None:
        cfg = self.cm.config
        # Clear any previous jobs (when settings change at runtime)
        self.scheduler.remove_all_jobs()
        self.scheduler.add_job(
            self.run_pipeline_once,
            IntervalTrigger(minutes=max(5, int(cfg.collection_interval_minutes))),
            id="collect_and_analyze",
            replace_existing=True,
        )
        if cfg.daily_report_enabled:
            h, m = _hhmm(cfg.daily_report_time)
            self.scheduler.add_job(
                self.send_daily_report,
                CronTrigger(hour=h, minute=m),
                id="daily_report",
                replace_existing=True,
            )
        if cfg.weekly_report_enabled:
            h, m = _hhmm(cfg.daily_report_time)
            self.scheduler.add_job(
                self.send_weekly_report,
                CronTrigger(day_of_week=cfg.weekly_report_day.lower(), hour=h, minute=m),
                id="weekly_report",
                replace_existing=True,
            )
        self._jobs_installed = True

    def start(self) -> None:
        if not self._jobs_installed:
            self.install_jobs()
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def reload(self) -> None:
        """Re-install jobs after config changes."""
        self.install_jobs()
