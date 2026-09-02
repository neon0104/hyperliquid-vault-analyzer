#!/usr/bin/env python3
"""
quant_master_dip_combination.py — 샤프모멘텀 #1위 전략 + 회복탄력성 우량볼트 눌림목 추매 결합 백테스트
=============================================================================================
"""

import os, sys, json, glob
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR      = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

files = sorted(SNAPSHOTS_DIR.glob("*.json"))
snapshots_cache = {}
for f in files:
    date_str = f.stem
    with open(f, "r", encoding="utf-8") as fd:
        snapshots_cache[date_str] = json.load(fd)

dates = sorted(snapshots_cache.keys())
start_date = "2026-04-09"
sim_dates = [d for d in dates if d >= start_date]

def get_vault_snapshot_pnl_tvl(v: dict):
    pnl_arr = v.get("alltime_pnl", [])
    if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
        pnl_val = float(pnl_arr[-1])
    else:
        pnl_val = float(v.get("pnl_alltime", 0.0) or v.get("alltime_pnl", 0.0) or 0.0)
    tvl_val = float(v.get("tvl", 1.0) or 1.0)
    apr_30d = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    return pnl_val, max(tvl_val, 1.0), apr_30d

def compute_sharpe_momentum_score(v: dict):
    apr = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    robustness = float(v.get("robustness_score", 0.0) or 0.0)
    sharpe = float(v.get("sharpe_ratio", 0.0) or 0.0)
    if apr <= 0: return -100.0
    return (sharpe * 20.0) + (apr * 0.5) + (robustness * 30.0)

def select_sharpe_momentum_vaults(snapshot: list):
    filtered = []
    for v in snapshot:
        allow_dep = bool(v.get("allow_deposits", True))
        robustness = float(v.get("robustness_score", 0) or 0)
        mdd = float(v.get("max_drawdown", 0) or 0)
        apr = float(v.get("apr_30d", 0) or v.get("apr_pct", 0) or 0)

        if allow_dep and (robustness >= 0.15) and (mdd <= 35.0) and apr > 0:
            v_copy = dict(v)
            v_copy["sm_score"] = compute_sharpe_momentum_score(v)
            filtered.append(v_copy)

    if not filtered:
        filtered = [dict(v) for v in snapshot[:4]]
        for v in filtered: v["sm_score"] = compute_sharpe_momentum_score(v)

    filtered.sort(key=lambda x: x["sm_score"], reverse=True)
    return filtered[:2], filtered[2:4]

def run_combined_simulation(enable_dip_buy=True):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005
    last_rebalance_date = sim_dates[0]
    daily_values = []
    dip_events = []

    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_sharpe_momentum_vaults(first_snap)

    c_alloc = (total_capital * 0.80) / (len(core_v) or 1)
    s_alloc = (total_capital * 0.20) / (len(sat_v) or 1) if sat_v else 0.0

    for v in core_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": c_alloc, "amount": c_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": c_alloc / (tvl_s + c_alloc),
            "peak_amount": c_alloc, "invest_date": sim_dates[0],
            "type": "CORE", "mdd_tol": 15.0
        }

    for v in sat_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": s_alloc, "amount": s_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": s_alloc / (tvl_s + s_alloc),
            "peak_amount": s_alloc, "invest_date": sim_dates[0],
            "type": "SATELLITE", "mdd_tol": 15.0
        }

    for curr_date in sim_dates:
        snap = snapshots_cache[curr_date]
        snap_map = {v["address"]: v for v in snap}

        if curr_date == sim_dates[0]:
            daily_values.append(total_capital)
            continue

        current_holdings_total = 0.0
        ejected_today = []

        for addr, h in list(active_holdings.items()):
            v_curr = snap_map.get(addr)
            if v_curr:
                pnl_c, _, _ = get_vault_snapshot_pnl_tvl(v_curr)
                pnl_diff = pnl_c - h["pnl_start"]
                my_pnl = pnl_diff * h["share"]
            else:
                daily_r = h["apr_start"] / 100.0 / 365.0
                my_pnl = h["cost"] * ((1.0 + daily_r) ** 1 - 1.0)

            h["amount"] = max(h["cost"] + my_pnl, 0.0)
            if h["amount"] > h["peak_amount"]:
                h["peak_amount"] = h["amount"]

            drawdown_pct = ((h["peak_amount"] - h["amount"]) / h["peak_amount"]) * 100.0 if h["peak_amount"] > 0 else 0.0
            loss_pct = ((h["cost"] - h["amount"]) / h["cost"]) * 100.0 if h["cost"] > 0 else 0.0

            # 💡 눌림목 저가 추매
            rob = float(v_curr.get("robustness_score", 0.5) if v_curr else 0.5)
            if enable_dip_buy and rob >= 0.45 and (8.0 <= drawdown_pct <= 14.0) and not h.get("dip_bought", False):
                boost = total_capital * 0.05
                h["cost"] += boost
                h["amount"] += boost
                tvl_c = float(v_curr.get("tvl", 1.0) or 1.0) if v_curr else h["tvl_start"]
                h["share"] = h["amount"] / (tvl_c + h["amount"])
                h["dip_bought"] = True
                dip_events.append((curr_date, h["name"], drawdown_pct, boost))
                cumulative_fees += boost * 0.0005

            if drawdown_pct >= h["mdd_tol"] or loss_pct >= h["mdd_tol"]:
                realized_p = h["amount"] - h["cost"]
                v_fee = max(0.0, realized_p) * 0.10 + h["amount"] * 0.0005
                cumulative_fees += v_fee
                net_amount = max(0.0, h["amount"] - v_fee)
                cash += net_amount
                ejected_today.append(addr)
            else:
                current_holdings_total += h["amount"]

        for addr in ejected_today:
            del active_holdings[addr]

        if cash > 100.0 and len(active_holdings) > 0:
            reinvest_fee = cash * 0.0005
            cumulative_fees += reinvest_fee
            add_per = (cash - reinvest_fee) / len(active_holdings)
            for addr, h in active_holdings.items():
                h["amount"] += add_per
                h["cost"] += add_per
                v_c = snap_map.get(addr, {})
                tvl_c = float(v_c.get("tvl", 1.0) or 1.0)
                h["share"] = h["amount"] / (tvl_c + h["amount"])
            current_holdings_total += (cash - reinvest_fee)
            cash = 0.0

        days_since = (np.datetime64(curr_date) - np.datetime64(last_rebalance_date)).astype(int)
        if days_since >= 30:
            port_total = current_holdings_total + cash
            reb_fee = 0.0
            for addr, h in active_holdings.items():
                p = h["amount"] - h["cost"]
                if p > 0: reb_fee += p * 0.10
            reb_fee += port_total * 0.0005
            cumulative_fees += reb_fee
            port_total -= reb_fee

            core_v, sat_v = select_sharpe_momentum_vaults(snap)
            active_holdings.clear()
            cash = 0.0
            last_rebalance_date = curr_date

            c_alloc = (port_total * 0.80) / (len(core_v) or 1)
            s_alloc = (port_total * 0.20) / (len(sat_v) or 1) if sat_v else 0.0

            for v in core_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": c_alloc, "amount": c_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": c_alloc / (tvl_s + c_alloc),
                    "peak_amount": c_alloc, "invest_date": curr_date,
                    "type": "CORE", "mdd_tol": 15.0
                }
            for v in sat_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": s_alloc, "amount": s_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": s_alloc / (tvl_s + s_alloc),
                    "peak_amount": s_alloc, "invest_date": curr_date,
                    "type": "SATELLITE", "mdd_tol": 15.0
                }
            current_holdings_total = port_total

        total_today = current_holdings_total + cash
        daily_values.append(total_today)

    total_days = len(sim_dates) - 1
    final_val = daily_values[-1]
    tot_ret = (final_val / INITIAL_CAPITAL - 1.0) * 100.0
    cagr = ((final_val / INITIAL_CAPITAL) ** (365.0 / (total_days or 1)) - 1.0) * 100.0

    peaks = np.maximum.accumulate(daily_values)
    dds = (peaks - daily_values) / peaks * 100.0
    mdd = -float(dds.max())

    rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = float(np.mean(rets) / (np.std(rets) + 1e-9) * np.sqrt(365))

    return {
        "final_val": round(final_val, 2),
        "tot_ret": round(tot_ret, 2),
        "cagr": round(cagr, 2),
        "mdd": round(mdd, 2),
        "sharpe": round(sharpe, 2),
        "fees": round(cumulative_fees, 2),
        "dip_buys": len(dip_events),
        "events": dip_events
    }

if __name__ == "__main__":
    r_off = run_combined_simulation(enable_dip_buy=False)
    r_on  = run_combined_simulation(enable_dip_buy=True)

    print("🏆 [Master Strategy + Dip Buying Combination Results]")
    print(f"  - 일반 80:20 (Dip Buy OFF): Net Return +{r_off['tot_ret']:.2f}% | Net CAGR {r_off['cagr']:.2f}% | Final: ${r_off['final_val']:,.2f} | Fees: ${r_off['fees']:,.2f}")
    print(f"  - 🔥 눌림목 추매 결합 (Dip Buy ON): Net Return +{r_on['tot_ret']:.2f}% | Net CAGR {r_on['cagr']:.2f}% | Final: ${r_on['final_val']:,.2f} | Fees: ${r_on['fees']:,.2f}")
    print(f"  - 눌림목 저점 추매 횟수: {r_on['dip_buys']} 회")
    for dt, name, mdd, amt in r_on['events']:
        print(f"    * [{dt}] {name[:25]:25s} | MDD: -{mdd:.1f}% 할인 구간 $5,000 추매")
