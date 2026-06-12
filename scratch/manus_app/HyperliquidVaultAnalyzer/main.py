"""
Entry point for the Hyperliquid Vault Analyzer desktop application.

Usage:
  python main.py            # launch GUI
  python main.py --once     # headless: run pipeline once and print result
  python main.py --report   # headless: send a daily report and exit
"""
from __future__ import annotations

import argparse
import json
import logging
import sys


def _headless_once() -> int:
    from app.core.config import ConfigManager
    from app.scheduler.scheduler import AppScheduler

    cm = ConfigManager()
    cm.ensure_data_dir()
    sched = AppScheduler(cm)
    payload = sched.run_pipeline_once()
    portfolio = payload.get("portfolio", {})
    print(json.dumps({
        "ok": payload.get("ok"),
        "collection_stats": payload.get("collection_stats"),
        "metrics_count": payload.get("metrics_count"),
        "stable_picks": len(portfolio.get("stable", [])),
        "recovery_picks": len(portfolio.get("recovery", [])),
        "holdings": [
            {
                "leg": h.get("leg"),
                "name": h.get("name"),
                "address": h.get("address"),
                "weight": round(h.get("weight", 0.0), 4),
                "return_all": round(h.get("return_all", 0.0), 4),
                "mdd": round(h.get("mdd", 0.0), 4),
                "drawdown_now": round(h.get("drawdown_now", 0.0), 4),
                "recovery_factor": round(h.get("recovery_factor", 0.0), 4),
            }
            for h in portfolio.get("holdings", [])
        ],
    }, indent=2, ensure_ascii=False))
    return 0 if payload.get("ok") else 1


def _headless_report() -> int:
    from app.core.config import ConfigManager
    from app.scheduler.scheduler import AppScheduler

    cm = ConfigManager()
    cm.ensure_data_dir()
    sched = AppScheduler(cm)
    ok = sched.send_daily_report()
    print(json.dumps({"sent": bool(ok)}))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Hyperliquid Vault Analyzer")
    parser.add_argument("--once", action="store_true", help="Run pipeline once (no GUI).")
    parser.add_argument("--report", action="store_true", help="Send a daily report and exit.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.once:
        return _headless_once()
    if args.report:
        return _headless_report()

    # GUI path
    from app.ui.main_window import main as ui_main
    return ui_main()


if __name__ == "__main__":
    sys.exit(main())
