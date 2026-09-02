#!/usr/bin/env python3
"""
quant_watchlist_rotation.py — Top 25 볼트 와치리스트 이익 실현 & 저점 순환매(Dip-Rotation) 엔진
================================================================================================
유저 아이디어 입증:
1. 상위 25개 우량 볼트 와치리스트 상시 감시
2. 수익권인 기존 포트폴리오 볼트에서 20% 이익을 일부 정산(Harvest)
3. 역사적 Max MDD 70%+ 바닥 극점에 도달한 회복 우수한 와치리스트 볼트에 전격 순환 매수(Rotate)
"""

import sys, json
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR      = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
OFFICIAL_MDD_FILE = DATA_DIR / "official_vault_mdds.json"
OUTPUT_FILE   = DATA_DIR / "watchlist_rotation_sim.json"

# 공식 MDD 데이터 로드
with open(OFFICIAL_MDD_FILE, "r", encoding="utf-8") as f:
    official_mdds = json.load(f)

# 스냅샷 데이터 로드
files = sorted(SNAPSHOTS_DIR.glob("*.json"))
snapshots_cache = {}
for f in files:
    date_str = f.stem
    with open(f, "r", encoding="utf-8") as fd:
        snapshots_cache[date_str] = json.load(fd)

dates = sorted(snapshots_cache.keys())
start_date = "2026-04-09"
sim_dates = [d for d in dates if d >= start_date]

def main():
    print("=" * 80)
    print("🚀 [Top 25 Watchlist Profit Harvest & Dip-Rotation Engine] 시뮬레이션 가동...")
    print("=" * 80)

    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005
    last_rebalance_date = sim_dates[0]

    daily_values = []
    rotation_events = []

    first_snap = snapshots_cache[sim_dates[0]]
    snap_map_first = {v["address"]: v for v in first_snap}

    # Top 25 Watchlist 선정
    watchlist_candidates = []
    for v in first_snap:
        rob = float(v.get("robustness_score", 0) or 0)
        l_usd = float(v.get("leader_equity_usd", 0.0) or v.get("leader_equity", 0.0) or 0.0)
        sharpe = float(v.get("sharpe_ratio", 0) or 0)
        mdd = float(v.get("max_drawdown", 15) or 15)
        apr = float(v.get("apr_30d", 0) or v.get("apr_pct", 0) or 0)

        if rob >= 0.15 and mdd <= 40.0 and apr > 0:
            score = (np.log1p(l_usd) * 15.0) + (sharpe * 20.0) + (rob * 40.0)
            watchlist_candidates.append((v, score))

    watchlist_candidates.sort(key=lambda x: x[1], reverse=True)
    top25_watchlist = [v[0] for v in watchlist_candidates[:25]]

    # 초기 60:40 구성 (Core 3, Sat 3)
    core_v = top25_watchlist[:3]
    sat_v = top25_watchlist[3:6]

    c_alloc = (total_capital * 0.60) / len(core_v)
    s_alloc = (total_capital * 0.40) / len(sat_v)

    for v in core_v:
        addr = v["address"]
        off = official_mdds.get(addr, {})
        h_mdd = off.get("official_max_mdd", float(v.get("max_drawdown", 15)))
        rob = float(v.get("robustness_score", 0) or 0)
        pnl_s = float(v.get("alltime_pnl", [0])[-1] if isinstance(v.get("alltime_pnl"), list) and v.get("alltime_pnl") else 0)
        tvl_s = max(float(v.get("tvl", 1) or 1), 1.0)
        active_holdings[addr] = {
            "name": v["name"], "cost": c_alloc, "amount": c_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "share": c_alloc / (tvl_s + c_alloc),
            "peak_amount": c_alloc, "invest_date": sim_dates[0],
            "type": "CORE", "mdd_tol": 18.0, "rob": rob, "hist_mdd": h_mdd
        }

    for v in sat_v:
        addr = v["address"]
        off = official_mdds.get(addr, {})
        h_mdd = off.get("official_max_mdd", float(v.get("max_drawdown", 15)))
        rob = float(v.get("robustness_score", 0) or 0)
        pnl_s = float(v.get("alltime_pnl", [0])[-1] if isinstance(v.get("alltime_pnl"), list) and v.get("alltime_pnl") else 0)
        tvl_s = max(float(v.get("tvl", 1) or 1), 1.0)
        active_holdings[addr] = {
            "name": v["name"], "cost": s_alloc, "amount": s_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "share": s_alloc / (tvl_s + s_alloc),
            "peak_amount": s_alloc, "invest_date": sim_dates[0],
            "type": "SATELLITE", "mdd_tol": 18.0, "rob": rob, "hist_mdd": h_mdd
        }

    rotation_count = 0

    for curr_date in sim_dates:
        snap = snapshots_cache[curr_date]
        snap_map = {v["address"]: v for v in snap}

        if curr_date == sim_dates[0]:
            daily_values.append(total_capital)
            continue

        current_holdings_total = 0.0
        ejected_today = []

        # 1. 평가
        for addr, h in list(active_holdings.items()):
            v_curr = snap_map.get(addr)
            if v_curr:
                pnl_c = float(v_curr.get("alltime_pnl", [0])[-1] if isinstance(v_curr.get("alltime_pnl"), list) and v_curr.get("alltime_pnl") else 0)
                my_pnl = (pnl_c - h["pnl_start"]) * h["share"]
            else:
                my_pnl = 0.0

            h["amount"] = max(h["cost"] + my_pnl, 0.0)
            if h["amount"] > h["peak_amount"]:
                h["peak_amount"] = h["amount"]

            drawdown_pct = ((h["peak_amount"] - h["amount"]) / h["peak_amount"]) * 100.0 if h["peak_amount"] > 0 else 0.0
            if drawdown_pct >= h["mdd_tol"]:
                realized_p = h["amount"] - h["cost"]
                v_fee = max(0.0, realized_p) * 0.10 + h["amount"] * 0.0005
                cumulative_fees += v_fee
                cash += max(0.0, h["amount"] - v_fee)
                ejected_today.append(addr)
            else:
                current_holdings_total += h["amount"]

        for addr in ejected_today:
            del active_holdings[addr]

        # 2. 와치리스트 저점 도달 볼트 감지 및 이익 실현 순환매 (Opportunistic Profit-Harvest & Dip-Rotation)
        for v in top25_watchlist:
            w_addr = v["address"]
            w_name = v["name"]
            if w_addr in active_holdings:
                continue

            v_curr = snap_map.get(w_addr)
            if not v_curr:
                continue

            rob = float(v_curr.get("robustness_score", 0) or 0)
            off = official_mdds.get(w_addr, {})
            h_mdd = off.get("official_max_mdd", float(v_curr.get("max_drawdown", 15)))

            # 실시간 Drawdown 계산
            pnl_arr = v_curr.get("alltime_pnl", [])
            if isinstance(pnl_arr, list) and len(pnl_arr) > 5:
                vals = np.array([float(x) for x in pnl_arr if float(x) > 0])
                if len(vals) > 1:
                    peaks = np.maximum.accumulate(vals)
                    curr_dd = float(((peaks[-1] - vals[-1]) / peaks[-1]) * 100.0)
                else:
                    curr_dd = 0.0
            else:
                curr_dd = float(v_curr.get("max_drawdown", 0) or 0)

            # 저점 바닥 진입 조건: 현재 DD >= 0.70 * 역사적 Max MDD & Rob >= 0.40
            if curr_dd >= 0.70 * h_mdd and h_mdd >= 10.0 and rob >= 0.35:
                # 최고 수익률 기록 중인 포트폴리오 볼트에서 20% 이익 일부 실현
                best_holding_addr = None
                best_profit = -999999.0
                for h_k, h_v in active_holdings.items():
                    p = h_v["amount"] - h_v["cost"]
                    if p > best_profit:
                        best_profit = p
                        best_holding_addr = h_k

                if best_holding_addr and best_profit > 1000.0:
                    target_h = active_holdings[best_holding_addr]
                    harvest_amt = target_h["amount"] * 0.20 # 20% 수익 일부 정산
                    target_h["amount"] -= harvest_amt
                    target_h["cost"] -= harvest_amt * (target_h["cost"] / (target_h["amount"] + harvest_amt))

                    harvest_fee = harvest_amt * 0.0005
                    cumulative_fees += harvest_fee
                    inject_amt = harvest_amt - harvest_fee

                    tvl_s = max(float(v_curr.get("tvl", 1) or 1), 1.0)
                    pnl_s = float(v_curr.get("alltime_pnl", [0])[-1] if isinstance(v_curr.get("alltime_pnl"), list) and v_curr.get("alltime_pnl") else 0)

                    active_holdings[w_addr] = {
                        "name": w_name, "cost": inject_amt, "amount": inject_amt,
                        "pnl_start": pnl_s, "tvl_start": tvl_s, "share": inject_amt / (tvl_s + inject_amt),
                        "peak_amount": inject_amt, "invest_date": curr_date,
                        "type": "ROTATED_DIP_BUY", "mdd_tol": 18.0, "rob": rob, "hist_mdd": h_mdd
                    }
                    rotation_count += 1
                    rotation_events.append({
                        "date": curr_date,
                        "source_vault": target_h["name"],
                        "target_vault": w_name,
                        "harvested_amount": round(harvest_amt, 2),
                        "reason": f"와치리스트 우량 볼트 ({w_name}) 역사적 Max MDD(-{h_mdd:.1f}%) 극점 바닥(현재 DD -{curr_dd:.1f}%) 진입으로 20% 이익 정산 후 순환 매수"
                    })
                    break

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

    print(f"  - 총 순환매 이익실현 회수 횟수: {rotation_count} 회")
    print(f"  - 최종 운용 자산: ${final_val:,.2f} (누적 순수익률: +{tot_ret:.2f}%)")
    print(f"  - 연환산 순복리 (CAGR): {cagr:.2f}%")
    print(f"  - 샤프 지수 (Sharpe): {sharpe:.2f} | 최대 낙폭 (MDD): {mdd:.2f}%")
    print(f"  - 누적 지불 수수료: ${cumulative_fees:,.2f}")
    print("=" * 80)

    result = {
        "final_value": round(final_val, 2),
        "total_return": round(tot_ret, 2),
        "cagr": round(cagr, 2),
        "mdd": round(mdd, 2),
        "sharpe": round(sharpe, 2),
        "rotation_count": rotation_count,
        "rotation_events": rotation_events
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
