#!/usr/bin/env python3
"""
quant_dip_buyer.py — 회복 탄력성 우수 볼트 눌림목(MDD 발생시) 역발상 저점 매수 퀀트 검증
======================================================================================
1. High Resilience Vaults (로버스트니스 >= 0.50) 선별
2. 해당 우량 볼트가 일시적 시장 조정으로 MDD 10%~20% 구간에 진입 시 "저가 매수(Dip Buying)" 캐치
3. 전고점 회복 시 차익 실현 및 알파 극대화 효과 백테스트
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

def compute_resilience_dip_score(v: dict, curr_mdd: float):
    apr = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    robustness = float(v.get("robustness_score", 0.0) or 0.0)
    l_usd = float(v.get("leader_equity_usd", 0.0) or v.get("leader_equity", 0.0) or 0.0)

    if robustness < 0.40 or apr <= 0:
        return -100.0

    # 회복 탄력성 점수 = 로버스트니스 x (1 + MDD 할인율 가중치)
    # MDD가 10%~20% 일시 조정일 때 저가 매수 매력도 극대화!
    dip_bonus = (curr_mdd / 100.0) * 2.5 if (10.0 <= curr_mdd <= 22.0) else 0.0
    score = (robustness * 50.0) + (np.log1p(l_usd) * 5.0) + (dip_bonus * 30.0)
    return score

def run_dip_buying_simulation(enable_dip_buying=True):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005

    last_rebalance_date = sim_dates[0]
    daily_values = []
    ejection_events = []
    dip_buy_events = []

    def select_initial_vaults(snap):
        filtered = []
        for v in snap:
            if not bool(v.get("allow_deposits", True)): continue
            rob = float(v.get("robustness_score", 0) or 0)
            apr = float(v.get("apr_30d", 0) or 0)
            if rob >= 0.35 and apr > 0:
                filtered.append(v)
        filtered.sort(key=lambda x: float(x.get("robustness_score", 0) or 0), reverse=True)
        return filtered[:3], filtered[3:6]

    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_initial_vaults(first_snap)

    c_alloc = (total_capital * 0.70) / (len(core_v) or 1)
    s_alloc = (total_capital * 0.30) / (len(sat_v) or 1) if sat_v else 0.0

    for v in core_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": c_alloc, "amount": c_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": c_alloc / (tvl_s + c_alloc),
            "peak_amount": c_alloc, "invest_date": sim_dates[0],
            "type": "HIGH_RESILIENCE_CORE", "mdd_tol": 25.0
        }

    for v in sat_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": s_alloc, "amount": s_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": s_alloc / (tvl_s + s_alloc),
            "peak_amount": s_alloc, "invest_date": sim_dates[0],
            "type": "SATELLITE", "mdd_tol": 18.0
        }

    for curr_date in sim_dates:
        snap = snapshots_cache[curr_date]
        snap_map = {v["address"]: v for v in snap}

        if curr_date == sim_dates[0]:
            daily_values.append(total_capital)
            continue

        current_holdings_total = 0.0
        ejected_today = []

        # 1. 보유 볼트 가치 평가 및 눌림목(Dip) 감지
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

            # 💡 저점 매수 (Dip Buying) 조건 감지:
            # 회복 탄력성이 뛰어난 (Robustness >= 0.50) 우량 볼트가 10%~20% 눌림목 조정 중일 때!
            rob = float(v_curr.get("robustness_score", 0.5) if v_curr else 0.5)
            if enable_dip_buying and rob >= 0.50 and (10.0 <= drawdown_pct <= 20.0) and not h.get("dip_bought", False):
                # 눌림목 추가 가중 매수 (Dip Buy Boost)
                boost_amount = min(total_capital * 0.05, 5000.0) # $5,000 저점 추가 매수
                h["cost"] += boost_amount
                h["amount"] += boost_amount
                tvl_c = float(v_curr.get("tvl", 1.0) or 1.0) if v_curr else h["tvl_start"]
                h["share"] = h["amount"] / (tvl_c + h["amount"])
                h["dip_bought"] = True # 1회 저점 매수 실행 플래그
                dip_buy_events.append((curr_date, h["name"], drawdown_pct, boost_amount))
                cumulative_fees += boost_amount * 0.0005

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

        # 현금 즉시 우량 볼트 재투입
        if cash > 100.0 and len(active_holdings) > 0:
            add_per = (cash * 0.9995) / len(active_holdings)
            cumulative_fees += cash * 0.0005
            for addr, h in active_holdings.items():
                h["amount"] += add_per
                h["cost"] += add_per
                v_c = snap_map.get(addr, {})
                tvl_c = float(v_c.get("tvl", 1.0) or 1.0)
                h["share"] = h["amount"] / (tvl_c + h["amount"])
            current_holdings_total += (cash * 0.9995)
            cash = 0.0

        # 30일 정기 리밸런싱
        days_since = (np.datetime64(curr_date) - np.datetime64(last_rebalance_date)).astype(int)
        if days_since >= 30:
            port_total = current_holdings_total + cash
            core_v, sat_v = select_initial_vaults(snap)

            active_holdings.clear()
            cash = 0.0
            last_rebalance_date = curr_date

            c_alloc = (port_total * 0.70) / (len(core_v) or 1)
            s_alloc = (port_total * 0.30) / (len(sat_v) or 1) if sat_v else 0.0

            for v in core_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": c_alloc, "amount": c_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": c_alloc / (tvl_s + c_alloc),
                    "peak_amount": c_alloc, "invest_date": curr_date,
                    "type": "HIGH_RESILIENCE_CORE", "mdd_tol": 25.0
                }
            for v in sat_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
                active_holdings[addr] = {
                    "name": v["name"], "cost": s_alloc, "amount": s_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": s_alloc / (tvl_s + s_alloc),
                    "peak_amount": s_alloc, "invest_date": curr_date,
                    "type": "SATELLITE", "mdd_tol": 18.0
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
        "dip_buys": len(dip_buy_events),
        "events": dip_buy_events
    }

if __name__ == "__main__":
    print("=" * 75)
    print("🧪 [High Resilience Dip Buying Experiment] 퀀트 시뮬레이션...")
    print("=" * 75)

    res_off = run_dip_buying_simulation(enable_dip_buying=False)
    res_on  = run_dip_buying_simulation(enable_dip_buying=True)

    print(f"\n1. 기존 일반 매수 (Dip Buying OFF):")
    print(f"   최종자산: ${res_off['final_val']:,.2f} | 수익률: +{res_off['tot_ret']:.2f}% | CAGR: {res_off['cagr']:.2f}% | MDD: {res_off['mdd']:.2f}% | Sharpe: {res_off['sharpe']:.2f}")

    print(f"\n2. 🔥 회복탄력성 우량볼트 눌림목 저가매수 (Dip Buying ON):")
    print(f"   최종자산: ${res_on['final_val']:,.2f} | 수익률: +{res_on['tot_ret']:.2f}% | CAGR: {res_on['cagr']:.2f}% | MDD: {res_on['mdd']:.2f}% | Sharpe: {res_on['sharpe']:.2f}")
    print(f"   저가 추매 실행 횟수: {res_on['dip_buys']} 회")

    if res_on['events']:
        print("\n📍 눌림목(Dip Buy) 실행 내역 샘플:")
        for dt, name, mdd, amt in res_on['events'][:5]:
            print(f"   - [{dt}] {name[:25]:25s} | MDD: -{mdd:.1f}% 할인 조정 구간에서 ${amt:,.0f} 저점 추매!")
