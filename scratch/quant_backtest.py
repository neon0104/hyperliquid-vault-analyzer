#!/usr/bin/env python3
"""
quant_backtest.py — Hyperliquid Vault Backtest Engine
=====================================================
Analyzes historical performance of AI 추천 1, 2, 3, 4 from virtual_portfolios.json
using snapshot data in vault_data/snapshots/*.json and vault_data/pnl_history.db
from 2026-06-08 to 2026-08-11.

Compares:
- Equal-Weighting (동일 비중: Top 5~10 vaults equally allocated)
- Concentrated Weighting (집중 투자: Top 1~3 vaults 50~70% allocated)

Metrics:
- Total Return (%)
- Max Drawdown (MDD %)
- Annualized Volatility (%)
- Annualized Sharpe Ratio (Rf=0)
- Daily Win Rate (%)
"""

import os
import sys
import glob
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
DB_PATH = DATA_DIR / "pnl_history.db"
VIRTUAL_PORTFOLIOS_PATH = DATA_DIR / "virtual_portfolios.json"

START_DATE = "2026-06-08"
END_DATE = "2026-08-11"
INITIAL_CAPITAL = 100_000.0


def load_virtual_portfolios():
    with open(VIRTUAL_PORTFOLIOS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {p["name"]: p for p in data if p.get("id") != "default"}


def load_snapshots():
    snapshots = {}
    pattern = str(SNAPSHOTS_DIR / "*.json")
    for fp in sorted(glob.glob(pattern)):
        date_str = Path(fp).stem
        if START_DATE <= date_str <= END_DATE:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    snapshots[date_str] = {v["address"]: v for v in raw if "address" in v}
            except Exception as e:
                print(f"Warning loading snapshot {fp}: {e}")
    return snapshots


def load_db_pnl_history():
    if not DB_PATH.exists():
        return {}
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT vault_address, collected_at, tvl, alltime_pnl 
        FROM daily_pnl 
        WHERE collected_at >= ? AND collected_at <= ?
        ORDER BY collected_at ASC
    """, (START_DATE, END_DATE))
    rows = cursor.fetchall()
    conn.close()

    db_data = {}
    for addr, date_str, tvl, alltime_pnl in rows:
        if date_str not in db_data:
            db_data[date_str] = {}
        db_data[date_str][addr] = {
            "address": addr,
            "tvl": float(tvl or 1.0),
            "alltime_pnl": alltime_pnl
        }
    return db_data


def compute_portfolio_series(positions, total_capital, sorted_dates, snapshots, db_data):
    """
    Computes daily equity values for a portfolio from START_DATE to END_DATE.
    Positions can be USD amounts or percentage weights.
    """
    raw_sum = sum(float(v) for v in positions.values())
    scaled_positions = {}
    if raw_sum <= 1.05:
        scaled_positions = {addr: float(w) * total_capital for addr, w in positions.items()}
    elif raw_sum <= 100.5 and raw_sum > 1.05:
        scaled_positions = {addr: (float(w) / 100.0) * total_capital for addr, w in positions.items()}
    else:
        scaled_positions = {addr: float(w) for addr, w in positions.items()}

    # Base snapshot on start date
    start_date = sorted_dates[0]
    base_snap = snapshots.get(start_date, {})
    if not base_snap and start_date in db_data:
        base_snap = db_data[start_date]

    vault_base_info = {}
    for addr, invested_usd in scaled_positions.items():
        # Get start TVL and PnL
        v_start = base_snap.get(addr)
        if not v_start:
            # Search first available snapshot
            for d in sorted_dates:
                s = snapshots.get(d, {}).get(addr) or db_data.get(d, {}).get(addr)
                if s:
                    v_start = s
                    break
        
        if v_start:
            tvl_start = float(v_start.get("tvl", 1.0) or 1.0)
            pnl_arr = v_start.get("alltime_pnl", [])
            if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
                pnl_start = float(pnl_arr[-1])
            else:
                pnl_start = float(v_start.get("alltime_pnl", 0.0) or 0.0)
        else:
            tvl_start = 1.0
            pnl_start = 0.0

        share = invested_usd / max(tvl_start, 1.0)
        vault_base_info[addr] = {
            "invested_usd": invested_usd,
            "tvl_start": tvl_start,
            "pnl_start": pnl_start,
            "share": share
        }

    daily_values = []

    for d in sorted_dates:
        d_snap = snapshots.get(d, {})
        d_db = db_data.get(d, {})
        
        day_total_val = 0.0
        for addr, base_info in vault_base_info.items():
            amt = base_info["invested_usd"]
            pnl_start = base_info["pnl_start"]
            share = base_info["share"]
            
            v_curr = d_snap.get(addr) or d_db.get(addr)
            if v_curr:
                pnl_arr = v_curr.get("alltime_pnl", [])
                if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
                    pnl_curr = float(pnl_arr[-1])
                else:
                    pnl_curr = float(v_curr.get("alltime_pnl", 0.0) or 0.0)
                
                delta_pnl = pnl_curr - pnl_start
                val = amt + (delta_pnl * share)
            else:
                # If data missing for this day, assume last known value or invested amount
                val = amt
            day_total_val += val
        
        daily_values.append(day_total_val)

    return daily_values


def calculate_metrics(daily_values):
    values = np.array(daily_values, dtype=float)
    if len(values) < 2:
        return {}

    initial_val = values[0]
    final_val = values[-1]
    total_return_pct = (final_val / initial_val - 1.0) * 100.0

    # Drawdown
    peaks = np.maximum.accumulate(values)
    drawdowns = (peaks - values) / peaks * 100.0
    mdd_pct = float(np.max(drawdowns))

    # Daily returns
    daily_rets = values[1:] / values[:-1] - 1.0

    # Volatility (Annualized using 365 crypto days)
    daily_vol = np.std(daily_rets, ddof=1) if len(daily_rets) > 1 else 0.0
    ann_vol_pct = daily_vol * np.sqrt(365) * 100.0

    # Sharpe Ratio (Annualized, Rf=0)
    mean_ret = np.mean(daily_rets) if len(daily_rets) > 0 else 0.0
    ann_return = mean_ret * 365.0
    sharpe_ratio = (ann_return / (daily_vol * np.sqrt(365))) if daily_vol > 1e-9 else 0.0

    # Win Rate
    positive_days = np.sum(daily_rets > 0)
    total_days = len(daily_rets)
    win_rate_pct = (positive_days / total_days * 100.0) if total_days > 0 else 0.0

    return {
        "initial_capital": round(initial_val, 2),
        "final_value": round(final_val, 2),
        "total_profit": round(final_val - initial_val, 2),
        "total_return_pct": round(total_return_pct, 2),
        "mdd_pct": round(mdd_pct, 2),
        "ann_volatility_pct": round(ann_vol_pct, 2),
        "sharpe_ratio": round(sharpe_ratio, 3),
        "win_rate_pct": round(win_rate_pct, 2),
        "total_days": total_days,
        "daily_returns": daily_rets,
        "equity_curve": values
    }


def run_backtest():
    print("=" * 80)
    print(f" Hyperliquid Vault Backtest Analysis ({START_DATE} to {END_DATE})")
    print("=" * 80)

    snapshots = load_snapshots()
    db_data = load_db_pnl_history()

    sorted_dates = sorted(set(snapshots.keys()) | set(db_data.keys()))
    sorted_dates = [d for d in sorted_dates if START_DATE <= d <= END_DATE]

    print(f"Total Snapshot/DB Dates Loaded: {len(sorted_dates)} days")
    if not sorted_dates:
        print("[ERROR] No data available for requested date range.")
        return

    ai_portfolios = load_virtual_portfolios()

    # Define portfolios to test
    portfolios_to_test = {}

    # 1. AI 추천 1 (Max Sharpe / Equal Weight 13 vaults)
    p1 = ai_portfolios.get("AI 추천 1")
    if p1:
        portfolios_to_test["AI 추천 1 (Max Sharpe - Equal Wt 13)"] = p1["positions"]

    # 2. AI 추천 2 (Min Variance / Broad Allocation)
    p2 = ai_portfolios.get("AI 추천 2(분산)")
    if p2:
        portfolios_to_test["AI 추천 2 (Min Variance - Broad 9)"] = p2["positions"]

    # 3. AI 추천 3 (Risk Parity / Mixed Weights)
    p3 = ai_portfolios.get("AI 추천 3(위험평균)")
    if p3:
        portfolios_to_test["AI 추천 3 (Risk Parity - Mixed 13)"] = p3["positions"]

    # 4. AI 추천 4 (Min CVaR / Concentrated 7 vaults - Top 2 vaults 65.7%)
    p4 = ai_portfolios.get("AI 추천 4(원금보호형)")
    if p4:
        portfolios_to_test["AI 추천 4 (Min CVaR - Concentrated 7)"] = p4["positions"]

    # 5. Pure Equal Weight Benchmark (Top 10 active vaults equal weight 10% each)
    # Extract top 10 vaults by TVL on START_DATE
    start_snap = snapshots.get(sorted_dates[0], {})
    sorted_vaults_by_tvl = sorted(
        start_snap.values(), 
        key=lambda x: float(x.get("tvl", 0) or 0), 
        reverse=True
    )
    top_10_addrs = [v["address"] for v in sorted_vaults_by_tvl[:10] if "address" in v]
    pure_equal_positions = {addr: 10.0 for addr in top_10_addrs}
    portfolios_to_test["Benchmark: Pure Equal Wt (Top 10 - 10% each)"] = pure_equal_positions

    # 6. Pure Concentrated Benchmark (Top 3 active vaults: 50% #1, 25% #2, 25% #3)
    top_3_addrs = [v["address"] for v in sorted_vaults_by_tvl[:3] if "address" in v]
    if len(top_3_addrs) >= 3:
        pure_conc_positions = {
            top_3_addrs[0]: 50.0,
            top_3_addrs[1]: 25.0,
            top_3_addrs[2]: 25.0
        }
        portfolios_to_test["Benchmark: Pure Concentrated (Top 3: 50/25/25)"] = pure_conc_positions

    # Execute backtest for each portfolio
    results = {}
    for p_name, pos in portfolios_to_test.items():
        series = compute_portfolio_series(pos, INITIAL_CAPITAL, sorted_dates, snapshots, db_data)
        metrics = calculate_metrics(series)
        results[p_name] = metrics

    # Display Results Summary Table
    print("\n" + "-" * 105)
    print(f"{'Portfolio Strategy':<45} | {'Return':>8} | {'MDD':>7} | {'Sharpe':>7} | {'Vol':>7} | {'WinRate':>7}")
    print("-" * 105)

    for name, m in results.items():
        ret_str = f"{m['total_return_pct']:+.2f}%"
        mdd_str = f"{m['mdd_pct']:.2f}%"
        sh_str = f"{m['sharpe_ratio']:.2f}"
        vol_str = f"{m['ann_volatility_pct']:.2f}%"
        win_str = f"{m['win_rate_pct']:.1f}%"
        print(f"{name:<45} | {ret_str:>8} | {mdd_str:>7} | {sh_str:>7} | {vol_str:>7} | {win_str:>7}")

    print("-" * 105)

    # Save detailed JSON output for further synthesis and inspection
    output_path = BASE_DIR / "scratch" / "quant_backtest_results.json"
    save_data = {}
    for k, v in results.items():
        save_data[k] = {
            "initial_capital": v["initial_capital"],
            "final_value": v["final_value"],
            "total_profit": v["total_profit"],
            "total_return_pct": v["total_return_pct"],
            "mdd_pct": v["mdd_pct"],
            "ann_volatility_pct": v["ann_volatility_pct"],
            "sharpe_ratio": v["sharpe_ratio"],
            "win_rate_pct": v["win_rate_pct"],
            "total_days": v["total_days"]
        }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    print(f"\n[SUCCESS] Backtest results saved to: {output_path}")

    # Analyze Vault Volatility & Failure Risks across all individual vaults in AI 추천 portfolios
    print("\n" + "=" * 80)
    print(" Vault Risk & Performance Decomposition")
    print("=" * 80)

    all_positions_addrs = set()
    for pos in portfolios_to_test.values():
        all_positions_addrs.update(pos.keys())

    vault_stats = {}
    for addr in all_positions_addrs:
        # compute single vault series with $10,000 capital
        s_series = compute_portfolio_series({addr: 10000.0}, 10000.0, sorted_dates, snapshots, db_data)
        s_m = calculate_metrics(s_series)
        
        # Get vault name from latest snapshot
        latest_s = snapshots.get(sorted_dates[-1], {}).get(addr) or snapshots.get(sorted_dates[0], {}).get(addr) or {}
        v_name = latest_s.get("name", addr[:10])
        
        vault_stats[addr] = {
            "name": v_name,
            "return": s_m.get("total_return_pct", 0),
            "mdd": s_m.get("mdd_pct", 0),
            "vol": s_m.get("ann_volatility_pct", 0),
            "sharpe": s_m.get("sharpe_ratio", 0)
        }

    print(f"{'Vault Address':<44} | {'Name':<20} | {'Return':>8} | {'MDD':>7} | {'Vol':>7}")
    print("-" * 90)
    for addr, vs in sorted(vault_stats.items(), key=lambda x: x[1]["return"], reverse=True):
        print(f"{addr:<44} | {vs['name'][:20]:<20} | {vs['return']:+.2f}% | {vs['mdd']:.2f}% | {vs['vol']:.2f}%")

    print("=" * 80)

if __name__ == "__main__":
    run_backtest()
