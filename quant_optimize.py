#!/usr/bin/env python3
"""
quant_optimize.py — 초고속 수익률 극대화 퀀트 시뮬레이션
======================================================
"""

import os, sys, json
import numpy as np
from pathlib import Path

BASE_DIR = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

sys.path.insert(0, str(BASE_DIR))
from smart_scorer import compute_smart_scores, get_smart_recommendations

def get_vault_pnl_tvl(v: dict):
    pnl_arr = v.get("alltime_pnl", [])
    if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
        pnl_val = float(pnl_arr[-1])
    else:
        pnl_val = float(v.get("pnl_alltime", 0.0) or v.get("alltime_pnl", 0.0) or 0.0)
    tvl_val = float(v.get("tvl", 1.0) or 1.0)
    apr_30d = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    return pnl_val, max(tvl_val, 1.0), apr_30d

# 1. Preload & Pre-score Snapshots once
files = sorted(SNAPSHOTS_DIR.glob("*.json"))
snapshots_cache = {}
scored_cache = {}

print("📂 스냅샷 캐싱 중...")
for f in files:
    date_str = f.stem
    with open(f, "r", encoding="utf-8") as fd:
        data = json.load(fd)
        snapshots_cache[date_str] = data
        scored_cache[date_str] = compute_smart_scores([dict(v) for v in data])

dates = sorted(snapshots_cache.keys())
start_date = "2026-04-09"
sim_dates = [d for d in dates if d >= start_date]

def run_simulation(
    core_ratio=0.50,
    sat_ratio=0.50,
    mdd_cutoff=12.0,
    immediate_reinvest=True,
    top_k_core=3,
    top_k_sat=5,
    min_leader_usd=20000.0,
    min_robustness=0.30,
    alpha_weight=0.7 # APR 모멘텀 가중치
):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    last_rebalance_date = sim_dates[0]

    daily_values = []
    ejection_count = 0
    rebalance_count = 0

    def select_vaults(date_str):
        scored = scored_cache[date_str]
        recs = get_smart_recommendations(scored, top_k=25)
        
        filtered = []
        for v in recs:
            l_rat = float(v.get("leader_equity_ratio", 0) or 0)
            l_usd = float(v.get("leader_equity_usd", 0) or 0)
            robust = float(v.get("robustness_score", 0) or 0)
            allow = bool(v.get("allow_deposits", True))

            if allow and (l_rat >= 0.15 or l_usd >= min_leader_usd) and (robust >= min_robustness):
                filtered.append(v)
        
        if not filtered:
            filtered = recs[:8]
        
        # 알파 모멘텀 가중 정렬: 30d APR x alpha_weight + 로버스트니스 점수
        sorted_alpha = sorted(filtered, key=lambda x: (float(x.get("apr_30d", 0) or 0) * alpha_weight + float(x.get("robustness_score", 0) or 0) * 50), reverse=True)
        
        core_v = sorted_alpha[:top_k_core]
        remains = [v for v in filtered if v not in core_v]
        sorted_sat = sorted(remains, key=lambda x: float(x.get("apr_30d", 0) or 0), reverse=True)
        sat_v = sorted_sat[:top_k_sat]
        
        return core_v, sat_v

    core_v, sat_v = select_vaults(sim_dates[0])

    c_alloc = (total_capital * core_ratio) / (len(core_v) or 1)
    s_alloc = (total_capital * sat_ratio) / (len(sat_v) or 1) if sat_v else 0.0

    for v in core_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": c_alloc, "amount": c_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": c_alloc / (tvl_s + c_alloc),
            "peak_amount": c_alloc, "type": "CORE"
        }
    for v in sat_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": s_alloc, "amount": s_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": s_alloc / (tvl_s + s_alloc),
            "peak_amount": s_alloc, "type": "SATELLITE"
        }

    rebalance_count += 1

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
                pnl_c, _, _ = get_vault_pnl_tvl(v_curr)
                pnl_diff = pnl_c - h["pnl_start"]
                my_pnl = pnl_diff * h["share"]
            else:
                daily_r = h.get("apr_start", 0) / 100.0 / 365.0
                my_pnl = h["cost"] * ((1.0 + daily_r) ** 1 - 1.0)

            h["amount"] = max(h["cost"] + my_pnl, 0.0)
            if h["amount"] > h["peak_amount"]:
                h["peak_amount"] = h["amount"]

            drawdown_pct = ((h["peak_amount"] - h["amount"]) / h["peak_amount"]) * 100.0 if h["peak_amount"] > 0 else 0.0
            loss_pct = ((h["cost"] - h["amount"]) / h["cost"]) * 100.0 if h["cost"] > 0 else 0.0

            if drawdown_pct >= mdd_cutoff or loss_pct >= mdd_cutoff:
                cash += h["amount"]
                ejected_today.append(addr)
                ejection_count += 1
            else:
                current_holdings_total += h["amount"]

        for addr in ejected_today:
            del active_holdings[addr]

        # 즉시 재투자 로직 (Immediate Reinvestment into active holdings)
        if immediate_reinvest and cash > 100.0 and len(active_holdings) > 0:
            add_alloc = cash / len(active_holdings)
            for addr, h in active_holdings.items():
                h["amount"] += add_alloc
                h["cost"] += add_alloc
                v_curr = snap_map.get(addr, {})
                tvl_curr = float(v_curr.get("tvl", 1.0) or 1.0)
                h["share"] = h["amount"] / (tvl_curr + h["amount"])
            current_holdings_total += cash
            cash = 0.0

        # 30일 정기 리밸런싱
        days_since = (np.datetime64(curr_date) - np.datetime64(last_rebalance_date)).astype(int)
        if days_since >= 30:
            port_total = current_holdings_total + cash
            core_v, sat_v = select_vaults(curr_date)

            active_holdings.clear()
            cash = 0.0
            last_rebalance_date = curr_date
            rebalance_count += 1

            if sat_v:
                c_alloc = (port_total * core_ratio) / (len(core_v) or 1)
                s_alloc = (port_total * sat_ratio) / (len(sat_v) or 1)
            else:
                c_alloc = port_total / (len(core_v) or 1)
                s_alloc = 0.0

            for v in core_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": c_alloc, "amount": c_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": c_alloc / (tvl_s + c_alloc),
                    "peak_amount": c_alloc, "type": "CORE"
                }
            for v in sat_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": s_alloc, "amount": s_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": s_alloc / (tvl_s + s_alloc),
                    "peak_amount": s_alloc, "type": "SATELLITE"
                }
            current_holdings_total = port_total

        tot_today = current_holdings_total + cash
        daily_values.append(tot_today)

    final_val = daily_values[-1]
    tot_ret = (final_val / INITIAL_CAPITAL - 1.0) * 100.0
    total_days = len(sim_dates) - 1
    cagr = ((final_val / INITIAL_CAPITAL) ** (365.0 / (total_days or 1)) - 1.0) * 100.0

    peaks = np.maximum.accumulate(daily_values)
    dds = (peaks - daily_values) / peaks * 100.0
    mdd = -float(dds.max())

    rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = float(np.mean(rets) / (np.std(rets) + 1e-9) * np.sqrt(365))

    return {
        "final_val": final_val,
        "tot_ret": tot_ret,
        "cagr": cagr,
        "mdd": mdd,
        "sharpe": sharpe,
        "ejections": ejection_count,
        "rebalances": rebalance_count
    }

if __name__ == "__main__":
    print("⚡ 수익률 극대화 퀀트 시뮬레이션 파라미터 그리드 탐색...")
    
    configs = [
        ("기존 70:30 (현금 방치형)", 0.70, 0.30, 15.0, False, 5, 3, 30000.0, 0.35, 0.2),
        ("전략 1: 현금 즉시 재투자 (Immediate Reinvest)", 0.70, 0.30, 15.0, True, 5, 3, 30000.0, 0.35, 0.3),
        ("전략 2: 50:50 알파 균형 + 즉시 재투자", 0.50, 0.50, 15.0, True, 4, 4, 25000.0, 0.35, 0.5),
        ("전략 3: 40:60 하이-알파 모멘텀 집중", 0.40, 0.60, 12.0, True, 3, 5, 20000.0, 0.30, 0.8),
        ("전략 4: 30:70 수퍼-알파 모멘텀 + 트레일링 10% 손절", 0.30, 0.70, 10.0, True, 3, 5, 15000.0, 0.25, 1.2),
        ("전략 5: 20:80 하이-레버리지 모멘텀 킹", 0.20, 0.80, 10.0, True, 2, 6, 10000.0, 0.20, 1.5),
    ]

    for name, c_r, s_r, mdd_c, imm, k_c, k_s, l_usd, rob, a_w in configs:
        res = run_simulation(
            core_ratio=c_r, sat_ratio=s_r, mdd_cutoff=mdd_c,
            immediate_reinvest=imm, top_k_core=k_c, top_k_sat=k_s,
            min_leader_usd=l_usd, min_robustness=rob, alpha_weight=a_w
        )
        print(f"\n🔹 {name}:")
        print(f"   최종자산: ${res['final_val']:,.2f} | 누적수익률: +{res['tot_ret']:.2f}% | CAGR: {res['cagr']:.2f}% | MDD: {res['mdd']:.2f}% | Sharpe: {res['sharpe']:.2f} | Ejections: {res['ejections']}")
