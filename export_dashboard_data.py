#!/usr/bin/env python3
"""
export_dashboard_data.py
최신 볼트 분석 결과를 GitHub Pages 대시보드용 JSON으로 내보내기
"""
import json, os, glob, sys
from datetime import datetime
from pathlib import Path

BASE_DIR      = Path(__file__).parent
SNAPSHOTS_DIR = BASE_DIR / "vault_data" / "snapshots"
PORTFOLIO_FILE= BASE_DIR / "vault_data" / "my_portfolio.json"
OUT_FILE      = BASE_DIR / "docs" / "data.json"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_latest_snapshot():
    files = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")), reverse=True)
    if not files:
        print("No snapshots found")
        return [], ""
    with open(files[0], encoding="utf-8") as f:
        return json.load(f), Path(files[0]).stem

def load_portfolio():
    if PORTFOLIO_FILE.exists():
        with open(PORTFOLIO_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    vaults, date_str = load_latest_snapshot()
    portfolio = load_portfolio()

    # 볼트 맵
    vault_map = {v["address"]: v for v in vaults}

    # 포트폴리오 계산
    holdings = []
    total_invested = 0.0
    total_monthly = 0.0

    for addr, usd in portfolio.items():
        v = vault_map.get(addr, {})
        apr = v.get("apr_30d", 0)
        monthly = usd * apr / 100 / 12
        total_invested += usd
        total_monthly += monthly
        holdings.append({
            "address":      addr,
            "name":         v.get("name", addr[:12] + "..."),
            "invested_usd": round(usd, 2),
            "apr_30d":      round(apr, 2),
            "mdd":          round(v.get("max_drawdown", 0), 2),
            "monthly_est":  round(monthly, 2),
            "robustness":   round(v.get("robustness_score", 0), 3),
            "grade":        v.get("equity_curve_grade", "-"),
            "allow_deposits": v.get("allow_deposits", True),
            "danger": v.get("max_drawdown", 0) > 20 or apr < 0,
        })

    for h in holdings:
        h["pct"] = round(h["invested_usd"] / total_invested * 100, 1) if total_invested else 0

    # 추천 (상위 15개, APR > 0)
    recommendations = [
        {
            "name":         v.get("name","")[:35],
            "address":      v["address"],
            "apr_30d":      round(v.get("apr_30d", 0), 2),
            "mdd":          round(v.get("max_drawdown", 0), 2),
            "robustness":   round(v.get("robustness_score", 0), 3),
            "grade":        v.get("equity_curve_grade", "-"),
            "sharpe":       round(v.get("sharpe_ratio", 0), 3),
            "tvl":          round(v.get("tvl", 0), 0),
            "allocation":   round(v.get("suggested_allocation", 0), 1),
            "leader_equity": round(v.get("leader_equity_ratio", 0) * 100, 1),
            "age_days":     v.get("age_days", 0),
        }
        for v in vaults
        if v.get("apr_30d", 0) > 0
           and v.get("allow_deposits", True)
           and v.get("leader_equity_ratio", 0) >= 0.4
    ][:15]

    # 시장 현황
    valid = [v for v in vaults if v.get("data_points", 0) >= 3]
    import numpy as np
    market = {}
    if valid:
        market = {
            "avg_apr":    round(float(np.mean([v["apr_30d"] for v in valid])), 1),
            "median_apr": round(float(np.median([v["apr_30d"] for v in valid])), 1),
            "avg_sharpe": round(float(np.mean([v["sharpe_ratio"] for v in valid])), 2),
            "avg_mdd":    round(float(np.mean([v["max_drawdown"] for v in valid])), 1),
            "vault_count": len(vaults),
        }

    out = {
        "generated_at":       datetime.now().isoformat(),
        "analysis_date":      date_str,
        "total_invested":     round(total_invested, 2),
        "estimated_monthly":  round(total_monthly, 2),
        "estimated_annual":   round(total_monthly * 12, 2),
        "holdings":           holdings,
        "recommendations":    recommendations,
        "market":             market,
        "needs_rebalance":    any(h["danger"] for h in holdings),
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=float)

    print(f"Dashboard data exported → {OUT_FILE}")
    print(f"  Holdings: {len(holdings)}, Recommendations: {len(recommendations)}")
    print(f"  Total invested: ${total_invested:,.0f}")

if __name__ == "__main__":
    main()
