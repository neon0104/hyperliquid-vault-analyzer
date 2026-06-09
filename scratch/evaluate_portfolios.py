import os
import json
import sys
sys.path.append(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
import portfolio_tracker

snapshots = portfolio_tracker.load_snapshots_all()
portfolios = portfolio_tracker.load_virtual_portfolios()

results = []
for p in portfolios:
    perf = portfolio_tracker.calc_portfolio_performance(p.get("positions", {}), p.get("invest_date"), p.get("total_capital", 100000.0), snapshots)
    results.append({
        "name": p["name"],
        "invest_date": p["invest_date"],
        "total_capital": p["total_capital"],
        "total_value": perf["total_value"],
        "total_pnl": perf["total_pnl"],
        "total_pnl_pct": perf["total_pnl_pct"],
        "days_held": perf["days_held"]
    })

os.makedirs(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer\scratch", exist_ok=True)
with open(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer\scratch\eval_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
