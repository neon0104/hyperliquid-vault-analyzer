#!/usr/bin/env python3
"""
quant_super_alpha.py — 초고수익 & 리더 자본 연동 퀀트 엔진
======================================================
1. Leader Equity >= $30,000 이상 자진 투입 우량 볼트에 60~70% 집중 배분
2. 대형 리더 볼트는 변동성 내성(MDD 25% 수용) 적용하여 휘프소(Whipsaw) 손절 방지
3. 소형 새틀라이트 볼트는 12% 딜레이 손절 적용
4. 실시간 현금 즉시 우량 볼트 재투입
"""

import os, sys, json
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR      = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

def get_vault_pnl_tvl(v: dict):
    pnl_arr = v.get("alltime_pnl", [])
    if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
        pnl_val = float(pnl_arr[-1])
    else:
        pnl_val = float(v.get("pnl_alltime", 0.0) or v.get("alltime_pnl", 0.0) or 0.0)
    tvl_val = float(v.get("tvl", 1.0) or 1.0)
    apr_30d = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    return pnl_val, max(tvl_val, 1.0), apr_30d

def run_super_alpha():
    files = sorted(SNAPSHOTS_DIR.glob("*.json"))
    snapshots_cache = {}
    for f in files:
        date_str = f.stem
        with open(f, "r", encoding="utf-8") as fd:
            snapshots_cache[date_str] = json.load(fd)

    dates = sorted(snapshots_cache.keys())
    start_date = "2026-04-09"
    sim_dates = [d for d in dates if d >= start_date]

    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    last_rebalance_date = sim_dates[0]

    daily_values = []
    ejection_events = []
    rebalance_events = []

    def select_super_alpha_vaults(snap):
        # 1. Skin-in-the-game Leader Vaults (Leader Equity >= $30k)
        leaders = []
        satellites = []
        for v in snap:
            if not bool(v.get("allow_deposits", True)):
                continue
            l_usd = float(v.get("leader_equity_usd", 0) or 0)
            l_rat = float(v.get("leader_equity_ratio", 0) or 0)
            robust = float(v.get("robustness_score", 0) or 0)
            apr = float(v.get("apr_30d", 0) or 0)

            if (l_usd >= 30000.0 or l_rat >= 0.35) and robust >= 0.30:
                leaders.append(v)
            elif (l_usd >= 5000.0 or l_rat >= 0.15) and robust >= 0.25 and apr > 0:
                satellites.append(v)

        # Sort leaders by (Leader Equity USD * Robustness)
        sorted_leaders = sorted(leaders, key=lambda x: float(x.get("leader_equity_usd", 0) or 0) * float(x.get("robustness_score", 0) or 0), reverse=True)
        top_leaders = sorted_leaders[:4]

        # Sort satellites by APR 30d
        sorted_sat = sorted(satellites, key=lambda x: float(x.get("apr_30d", 0) or 0), reverse=True)
        top_satellites = sorted_sat[:3]

        return top_leaders, top_satellites

    first_snap = snapshots_cache[sim_dates[0]]
    leaders, satellites = select_super_alpha_vaults(first_snap)

    lead_alloc = (total_capital * 0.75) / (len(leaders) or 1)
    sat_alloc  = (total_capital * 0.25) / (len(satellites) or 1) if satellites else 0.0

    for v in leaders:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": lead_alloc, "amount": lead_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": lead_alloc / (tvl_s + lead_alloc),
            "peak_amount": lead_alloc, "type": "LEADER_CORE",
            "mdd_cutoff": 28.0  # 대형 리더 볼트는 28% MDD 수용 (휘프소 방지)
        }

    for v in satellites:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": sat_alloc, "amount": sat_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": sat_alloc / (tvl_s + sat_alloc),
            "peak_amount": sat_alloc, "type": "MOMENTUM_SAT",
            "mdd_cutoff": 12.0  # 소형 새틀라이트는 12% 칼손절
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

            if drawdown_pct >= h["mdd_cutoff"] or loss_pct >= h["mdd_cutoff"]:
                cash += h["amount"]
                ejected_today.append(addr)
                ejection_events.append((curr_date, h["name"], h["type"], drawdown_pct))
            else:
                current_holdings_total += h["amount"]

        for addr in ejected_today:
            del active_holdings[addr]

        # 🔥 현금 발생 시 즉시 살아남은 대형 리더 볼트들에 즉시 재투자!
        if cash > 500.0 and len(active_holdings) > 0:
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
            leaders, satellites = select_super_alpha_vaults(snap)

            active_holdings.clear()
            cash = 0.0
            last_rebalance_date = curr_date

            if satellites:
                lead_alloc = (port_total * 0.75) / (len(leaders) or 1)
                sat_alloc  = (port_total * 0.25) / (len(satellites) or 1)
            else:
                lead_alloc = port_total / (len(leaders) or 1)
                sat_alloc  = 0.0

            for v in leaders:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": lead_alloc, "amount": lead_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": lead_alloc / (tvl_s + lead_alloc),
                    "peak_amount": lead_alloc, "type": "LEADER_CORE",
                    "mdd_cutoff": 28.0
                }

            for v in satellites:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": sat_alloc, "amount": sat_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": sat_alloc / (tvl_s + sat_alloc),
                    "peak_amount": sat_alloc, "type": "MOMENTUM_SAT",
                    "mdd_cutoff": 12.0
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

    print(f"🚀 [Super-Alpha Leader Engine] 백테스트 결과:")
    print(f"  - 기간: {sim_dates[0]} ~ {sim_dates[-1]} ({total_days} 일)")
    print(f"  - 최종 자산: ${final_val:,.2f}")
    print(f"  - 누적 수익률: +{tot_ret:.2f}% (CAGR: {cagr:.2f}%)")
    print(f"  - 최대 낙폭(MDD): {mdd:.2f}%")
    print(f"  - 샤프지수: {sharpe:.2f}")
    print(f"  - 방출 횟수: {len(ejection_events)} 회")

if __name__ == "__main__":
    run_super_alpha()
