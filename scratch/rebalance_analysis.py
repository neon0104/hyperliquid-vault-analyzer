#!/usr/bin/env python3
"""
scratch/rebalance_analysis.py — Hyperliquid Vault Rebalancing & Portfolio Strategy Backtester
==============================================================================================
Analyzes:
  1. Vault Selection Criteria (Leader Equity, Robustness Score, Age, Sharpe Ratio, MDD)
  2. Portfolio Construction Rules (Equal Weighting vs Risk Parity vs Barbell Strategy)
  3. Rebalancing Cadence & Triggers (7-day, 14-day, 30-day, and Threshold-Based when MDD > 10% or score drops 20%)

Dataset: 134 snapshot files in vault_data/snapshots/*.json
Initial Capital: $100,000
Friction / Slippage: 0.15% per trade turnover
"""

import os
import sys
import json
import glob
import math
from datetime import datetime
from pathlib import Path
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── Base Directory Setup ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
SNAPSHOTS_DIR = BASE_DIR / "vault_data" / "snapshots"
OUTPUT_DIR = BASE_DIR / "vault_data" / "analysis_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load Snapshot Dataset ─────────────────────────────────────────────────────
def load_all_snapshots():
    """Load all 134 snapshot files ordered by date."""
    snapshot_files = sorted(SNAPSHOTS_DIR.glob("*.json"))
    print(f"[DATA] Found {len(snapshot_files)} snapshot files in {SNAPSHOTS_DIR}")
    
    snapshots = {}
    dates = []
    
    for p in snapshot_files:
        date_str = p.stem  # YYYY-MM-DD
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                vmap = {}
                for v in data:
                    addr = v.get("address")
                    if addr:
                        vmap[addr] = v
                snapshots[date_str] = vmap
                dates.append(date_str)
        except Exception as e:
            print(f"[WARN] Error reading {p.name}: {e}")
            
    dates.sort()
    print(f"[DATA] Successfully loaded {len(dates)} valid snapshot dates: {dates[0]} to {dates[-1]}")
    return snapshots, dates


# ── Vault Filter Functions ───────────────────────────────────────────────────
def filter_vaults(vmap, criteria_name="balanced"):
    """
    Filters vaults in a snapshot based on selection criteria:
      - leader_equity_ratio
      - robustness_score
      - age_days
      - sharpe_ratio
      - max_drawdown
    """
    eligible = []
    
    # Define Filter Presets
    if criteria_name == "loose":
        min_leader_eq = 0.05
        min_robust = 0.30
        min_age = 14
        min_sharpe = 0.5
        max_mdd = 35.0
    elif criteria_name == "strict":
        min_leader_eq = 0.30
        min_robust = 0.65
        min_age = 60
        min_sharpe = 2.0
        max_mdd = 15.0
    elif criteria_name == "institutional": # Skin-in-the-game focus
        min_leader_eq = 0.40
        min_robust = 0.60
        min_age = 90
        min_sharpe = 1.8
        max_mdd = 12.0
    else:  # "balanced" (Recommended default)
        min_leader_eq = 0.20
        min_robust = 0.50
        min_age = 30
        min_sharpe = 1.2
        max_mdd = 20.0

    for addr, v in vmap.items():
        # Basic operational status
        if not v.get("allow_deposits", True):
            continue
            
        leader_eq = float(v.get("leader_equity_ratio", 0.0) or 0.0)
        robust = float(v.get("robustness_score", 0.0) or 0.0)
        age = int(v.get("age_days", 0) or 0)
        sharpe = float(v.get("sharpe_ratio", 0.0) or 0.0)
        mdd = float(v.get("max_drawdown", 0.0) or 0.0)
        tvl = float(v.get("tvl", 0.0) or 0.0)
        
        if tvl < 1000:
            continue
            
        if (leader_eq >= min_leader_eq and 
            robust >= min_robust and 
            age >= min_age and 
            sharpe >= min_sharpe and 
            mdd <= max_mdd):
            
            # Compute composite ranking score
            score = (
                robust * 0.35 +
                min(sharpe / 5.0, 1.0) * 0.25 +
                min(leader_eq, 1.0) * 0.20 +
                min(age / 180.0, 1.0) * 0.10 +
                max(0, 1.0 - mdd / 30.0) * 0.10
            )
            v_copy = dict(v)
            v_copy["composite_score"] = score
            eligible.append(v_copy)
            
    # Sort eligible vaults by composite score descending
    eligible.sort(key=lambda x: x["composite_score"], reverse=True)
    return eligible


# ── Portfolio Weighting Construction ──────────────────────────────────────────
def construct_portfolio_weights(vaults, method="risk_parity", top_k=5):
    """
    Constructs target weights for top_k vaults using:
      - equal_weight
      - risk_parity (Inverse Volatility)
      - barbell (70% Core robust / 30% High Sharpe growth)
    """
    selected = vaults[:top_k]
    n = len(selected)
    if n == 0:
        return {}
        
    weights = {}
    
    if method == "equal_weight":
        w_val = 1.0 / n
        for v in selected:
            weights[v["address"]] = w_val
            
    elif method == "risk_parity": # Inverse Volatility weighting
        vols = []
        for v in selected:
            vol = float(v.get("vol_score", 30.0) or 30.0)
            vol = max(vol, 5.0)  # Floor volatility to prevent division by zero
            vols.append(1.0 / vol)
        total_inv_vol = sum(vols)
        for i, v in enumerate(selected):
            weights[v["address"]] = vols[i] / total_inv_vol
            
    elif method == "barbell":
        # Sort into Core (lowest MDD / highest robustness) and Growth (highest Sharpe / APR)
        if n >= 2:
            n_core = max(1, int(n * 0.6))
            # Sort selected by robustness for core
            core_candidates = sorted(selected, key=lambda x: float(x.get("robustness_score", 0)), reverse=True)[:n_core]
            growth_candidates = [v for v in selected if v["address"] not in {c["address"] for c in core_candidates}]
            if not growth_candidates:
                growth_candidates = core_candidates
                
            core_weight_budget = 0.70
            growth_weight_budget = 0.30
            
            # Equal or Inverse Vol within tiers
            for v in core_candidates:
                weights[v["address"]] = weights.get(v["address"], 0) + (core_weight_budget / len(core_candidates))
            for v in growth_candidates:
                weights[v["address"]] = weights.get(v["address"], 0) + (growth_weight_budget / len(growth_candidates))
        else:
            weights[selected[0]["address"]] = 1.0
    else:
        # Fallback Equal Weight
        for v in selected:
            weights[v["address"]] = 1.0 / n
            
    return weights


# ── Backtest Simulator ────────────────────────────────────────────────────────
def run_backtest(snapshots, dates, filter_criteria="balanced", weighting_method="risk_parity", rebalance_rule="30d", top_k=5, friction_pct=0.0015):
    """
    Backtests portfolio performance across snapshot dates.
    
    rebalance_rule:
      - '7d' : Rebalance every ~7 days
      - '14d': Rebalance every ~14 days
      - '30d': Rebalance every ~30 days
      - 'threshold': Rebalance when MDD > 10% or individual vault score drops > 20% or weight drift > 10%
      - 'buy_and_hold': Rebalance only on day 0
    """
    initial_capital = 100000.0
    current_capital = initial_capital
    
    positions = {} # {addr: allocated_usd}
    last_rebalance_date = None
    last_selection_scores = {} # {addr: initial_composite_score}
    
    equity_curve = []
    rebalance_events = []
    total_turnover = 0.0
    total_friction_paid = 0.0
    peak_value = initial_capital
    max_drawdown = 0.0
    
    daily_returns = []
    
    for i, date_str in enumerate(dates):
        vmap = snapshots[date_str]
        current_dt = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 1. Update valuation of existing positions from previous date
        if i > 0:
            prev_date_str = dates[i-1]
            prev_vmap = snapshots[prev_date_str]
            
            portfolio_val_before = 0.0
            updated_positions = {}
            
            for addr, pos_usd in positions.items():
                v_curr = vmap.get(addr)
                v_prev = prev_vmap.get(addr)
                
                if v_curr and v_prev:
                    # Calculate period return using alltime_pnl difference relative to TVL
                    pnl_curr = v_curr.get("alltime_pnl", [])
                    pnl_prev = v_prev.get("alltime_pnl", [])
                    tvl_prev = float(v_prev.get("tvl", 1.0) or 1.0)
                    
                    if pnl_curr and pnl_prev and len(pnl_curr) > 0 and len(pnl_prev) > 0:
                        diff_pnl = float(pnl_curr[-1]) - float(pnl_prev[-1])
                        # Normalize by vault TVL + previous PnL magnitude
                        denom = max(tvl_prev, 1000.0)
                        ret = diff_pnl / denom
                        # Clip extreme single-day outliers
                        ret = float(np.clip(ret, -0.30, 0.30))
                    else:
                        # Fallback using apr_30d
                        apr = float(v_curr.get("apr_30d", 0.0) or 0.0)
                        days_diff = (current_dt - datetime.strptime(prev_date_str, "%Y-%m-%d")).days
                        ret = (apr / 100.0) * (days_diff / 365.0)
                elif v_curr:
                    ret = 0.0
                else:
                    # Vault delisted or unavailable in current snapshot -> assume -5% loss or exit
                    ret = -0.05
                    
                new_pos_usd = pos_usd * (1.0 + ret)
                updated_positions[addr] = max(new_pos_usd, 0.0)
                portfolio_val_before += updated_positions[addr]
                
            current_capital = portfolio_val_before
            daily_ret = (current_capital - equity_curve[-1]["value"]) / equity_curve[-1]["value"] if equity_curve else 0.0
            daily_returns.append(daily_ret)
        else:
            updated_positions = {}
            daily_returns.append(0.0)

        # Track Drawdown
        if current_capital > peak_value:
            peak_value = current_capital
        dd = (peak_value - current_capital) / peak_value if peak_value > 0 else 0.0
        if dd > max_drawdown:
            max_drawdown = dd

        # 2. Check Rebalance Trigger
        should_rebalance = False
        rebalance_reason = ""
        
        if i == 0:
            should_rebalance = True
            rebalance_reason = "Initial Portfolio Setup"
        elif rebalance_rule == "buy_and_hold":
            should_rebalance = False
        else:
            days_since_last = (current_dt - datetime.strptime(last_rebalance_date, "%Y-%m-%d")).days
            
            if rebalance_rule == "7d" and days_since_last >= 7:
                should_rebalance = True
                rebalance_reason = f"7-day calendar interval ({days_since_last} days elapsed)"
            elif rebalance_rule == "14d" and days_since_last >= 14:
                should_rebalance = True
                rebalance_reason = f"14-day calendar interval ({days_since_last} days elapsed)"
            elif rebalance_rule == "30d" and days_since_last >= 30:
                should_rebalance = True
                rebalance_reason = f"30-day calendar interval ({days_since_last} days elapsed)"
            elif rebalance_rule == "threshold":
                # Check MDD trigger (> 10%)
                if dd >= 0.10:
                    should_rebalance = True
                    rebalance_reason = f"Portfolio Drawdown Trigger ({dd*100:.1f}% >= 10.0%)"
                # Check Score Drop trigger (> 20% drop for any active vault)
                elif any(
                    addr in vmap and (
                        (last_selection_scores.get(addr, 0) - vmap[addr].get("robustness_score", 0)) / max(last_selection_scores.get(addr, 1), 1e-5) > 0.20
                    ) for addr in positions
                ):
                    should_rebalance = True
                    rebalance_reason = "Vault Robustness Score drop > 20%"
                # Check Weight Drift (> 10% weight drift)
                elif current_capital > 0:
                    target_w = 1.0 / max(len(positions), 1)
                    drift_exceeded = any(
                        abs((pos_usd / current_capital) - target_w) > 0.10 for pos_usd in positions.values()
                    )
                    if drift_exceeded:
                        should_rebalance = True
                        rebalance_reason = "Asset Weight Drift > 10%"
                # Guardrail: Rebalance if 45 days elapsed regardless
                if not should_rebalance and days_since_last >= 45:
                    should_rebalance = True
                    rebalance_reason = f"Maximum Time Guardrail reached ({days_since_last} days)"

        # 3. Execute Rebalancing
        if should_rebalance:
            eligible_vaults = filter_vaults(vmap, filter_criteria)
            
            if eligible_vaults:
                target_weights = construct_portfolio_weights(eligible_vaults, weighting_method, top_k)
                
                # Calculate turnover
                old_weights = {addr: pos / current_capital for addr, pos in updated_positions.items()} if current_capital > 0 else {}
                all_addrs = set(old_weights.keys()).union(set(target_weights.keys()))
                
                turnover = 0.5 * sum(abs(target_weights.get(a, 0.0) - old_weights.get(a, 0.0)) for a in all_addrs)
                friction_cost = current_capital * (2.0 * turnover) * friction_pct
                
                current_capital -= friction_cost
                total_friction_paid += friction_cost
                total_turnover += turnover
                
                # Allocate new positions
                new_positions = {}
                last_selection_scores = {}
                for v in eligible_vaults[:top_k]:
                    addr = v["address"]
                    w = target_weights.get(addr, 0.0)
                    new_positions[addr] = current_capital * w
                    last_selection_scores[addr] = float(v.get("robustness_score", 0.5))
                    
                positions = new_positions
                last_rebalance_date = date_str
                
                rebalance_events.append({
                    "date": date_str,
                    "reason": rebalance_reason,
                    "portfolio_value": current_capital,
                    "turnover_pct": turnover * 100,
                    "friction_cost": friction_cost,
                    "vault_count": len(positions)
                })
            else:
                # If no vaults pass filter, hold cash/existing positions
                positions = updated_positions
        else:
            positions = updated_positions

        equity_curve.append({
            "date": date_str,
            "value": current_capital,
            "drawdown": dd
        })

    # 4. Compute Performance Metrics
    total_days = (datetime.strptime(dates[-1], "%Y-%m-%d") - datetime.strptime(dates[0], "%Y-%m-%d")).days
    total_return_pct = ((current_capital - initial_capital) / initial_capital) * 100.0
    cagr_pct = (((current_capital / initial_capital) ** (365.0 / max(total_days, 1))) - 1.0) * 100.0
    
    daily_rets_arr = np.array(daily_returns[1:]) if len(daily_returns) > 1 else np.array([0.0])
    ann_vol_pct = np.std(daily_rets_arr) * np.sqrt(365) * 100.0
    
    mean_daily_ret = np.mean(daily_rets_arr)
    sharpe = (mean_daily_ret / (np.std(daily_rets_arr) + 1e-9)) * np.sqrt(365) if np.std(daily_rets_arr) > 0 else 0.0
    
    downside_returns = daily_rets_arr[daily_rets_arr < 0]
    downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 1e-9
    sortino = (mean_daily_ret / downside_std) * np.sqrt(365) if downside_std > 0 else 0.0
    
    calmar = (cagr_pct / (max_drawdown * 100.0)) if max_drawdown > 0 else 0.0

    return {
        "filter_criteria": filter_criteria,
        "weighting_method": weighting_method,
        "rebalance_rule": rebalance_rule,
        "top_k": top_k,
        "initial_capital": initial_capital,
        "final_capital": current_capital,
        "total_return_pct": total_return_pct,
        "cagr_pct": cagr_pct,
        "ann_vol_pct": ann_vol_pct,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown_pct": max_drawdown * 100.0,
        "calmar": calmar,
        "rebalance_count": len(rebalance_events),
        "total_turnover_pct": total_turnover * 100.0,
        "total_friction_paid": total_friction_paid,
        "equity_curve": equity_curve,
        "rebalance_events": rebalance_events
    }


# ── Run Full Grid Experiments ─────────────────────────────────────────────────
def run_all_experiments():
    snapshots, dates = load_all_snapshots()
    if not dates:
        print("[ERROR] No snapshots found!")
        return

    print("\n" + "="*80)
    print("      HYPERLIQUID VAULT REBALANCING & PORTFOLIO STRATEGY GRID BACKTEST")
    print("="*80)
    
    # Experiment 1: Compare Rebalancing Frequencies (7d vs 14d vs 30d vs Threshold vs Buy&Hold)
    rebalance_rules = ["7d", "14d", "30d", "threshold", "buy_and_hold"]
    filter_criteria_list = ["loose", "balanced", "strict", "institutional"]
    weighting_methods = ["equal_weight", "risk_parity", "barbell"]
    
    cadence_results = []
    
    # 1. Main Rebalancing Cadence Test (using recommended 'balanced' filter + 'risk_parity' weighting)
    print("\n[TEST 1] Rebalancing Cadence Comparison (Filter: balanced, Weighting: risk_parity, Top K: 5)")
    for rule in rebalance_rules:
        res = run_backtest(snapshots, dates, filter_criteria="balanced", weighting_method="risk_parity", rebalance_rule=rule, top_k=5)
        cadence_results.append(res)
        print(f"  Rule: {rule:<12} | Return: {res['total_return_pct']:>6.2f}% | CAGR: {res['cagr_pct']:>6.2f}% | Sharpe: {res['sharpe']:>5.2f} | MDD: {res['max_drawdown_pct']:>5.2f}% | Trades: {res['rebalance_count']:>2} | Turnover: {res['total_turnover_pct']:>6.1f}% | Friction: ${res['total_friction_paid']:>6.2f}")

    # 2. Portfolio Construction Test (Barbell vs Risk Parity vs Equal Weighting)
    print("\n[TEST 2] Portfolio Construction Comparison (Filter: balanced, Cadence: threshold, Top K: 5)")
    construction_results = []
    for w_method in weighting_methods:
        res = run_backtest(snapshots, dates, filter_criteria="balanced", weighting_method=w_method, rebalance_rule="threshold", top_k=5)
        construction_results.append(res)
        print(f"  Method: {w_method:<14} | Return: {res['total_return_pct']:>6.2f}% | Vol: {res['ann_vol_pct']:>5.2f}% | Sharpe: {res['sharpe']:>5.2f} | MDD: {res['max_drawdown_pct']:>5.2f}% | Calmar: {res['calmar']:>5.2f}")

    # 3. Vault Selection Filtering Criteria Test
    print("\n[TEST 3] Vault Selection Criteria Comparison (Weighting: risk_parity, Cadence: threshold, Top K: 5)")
    filter_results = []
    for f_crit in filter_criteria_list:
        res = run_backtest(snapshots, dates, filter_criteria=f_crit, weighting_method="risk_parity", rebalance_rule="threshold", top_k=5)
        filter_results.append(res)
        print(f"  Filter: {f_crit:<14} | Return: {res['total_return_pct']:>6.2f}% | Sharpe: {res['sharpe']:>5.2f} | MDD: {res['max_drawdown_pct']:>5.2f}% | Calmar: {res['calmar']:>5.2f}")

    # Save summary report to JSON
    summary_data = {
        "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "snapshot_count": len(dates),
        "start_date": dates[0],
        "end_date": dates[-1],
        "cadence_comparison": cadence_results,
        "construction_comparison": construction_results,
        "filter_comparison": filter_results
    }
    
    summary_file = OUTPUT_DIR / "rebalance_analysis_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, default=float)
    print(f"\n[OUTPUT] Saved backtest summary to {summary_file}")
    
    return summary_data


if __name__ == "__main__":
    run_all_experiments()
