#!/usr/bin/env python3
"""
quant_master_grid_search.py — 퀀트 마스터 그리드 탐색 & 최적 포트폴리오 도출 엔진
=============================================================================
이 스크립트는 Hyperliquid 120일 스냅샷 데이터 전체에 대해 다음 변수들의 전수 조합(Grid Search)을 실행합니다:
1. 볼트 스코어링 함수 (Smart vs RAAM vs Skin-in-Game vs Sharpe-Momentum vs Ensemble)
2. 포트폴리오 구조 (집중 80:20 vs 바벨 70:30 vs 바벨 50:50 vs 동일비중 Top 5~10)
3. 현금 처리 (즉시 알파 재투자 vs 10% 안전 버퍼 vs 현금 방치)
4. 손절 및 이탈 조건 (고정 15% vs 계층별 가변 12~30% vs 트레일링 스탑 10~25%)
5. 리밸런싱 주기 (7일 vs 14일 vs 30일 vs 수치 이탈 동적 트리거)
"""

import os, sys, json, glob
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR      = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"

# 1. 스냅샷 데이터 캐싱
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

# 2. 다양한 스코어링 모듈 정의
def score_vault(v: dict, model_type: str):
    apr = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    l_usd = float(v.get("leader_equity_usd", 0.0) or v.get("leader_equity", 0.0) or 0.0)
    l_rat = float(v.get("leader_equity_ratio", 0.0) or 0.0)
    robust = float(v.get("robustness_score", 0.0) or 0.0)
    sharpe = float(v.get("sharpe_ratio", 0.0) or 0.0)
    mdd = float(v.get("max_drawdown", 0.0) or 0.0)

    if model_type == "RAAM": # Risk-Adjusted Alpha Momentum
        if apr <= 0: return -100.0
        return (apr ** 0.85) * np.log1p(max(l_usd, 1000.0)) * (max(robust, 0.1) ** 0.5)

    elif model_type == "SKIN_HEAVY": # 리더 자본 중상 가중형
        if apr <= 0: return -100.0
        return (l_usd ** 0.6) * (apr ** 0.5) * (1.0 - mdd / 100.0)

    elif model_type == "SHARPE_MOMENTUM": # 샤프-모멘텀 가중형
        if apr <= 0: return -100.0
        return (sharpe * 20.0) + (apr * 0.5) + (robust * 30.0)

    elif model_type == "SMART_ENSEMBLE": # 앙상블 종합형
        if apr <= 0: return -100.0
        s1 = (apr ** 0.8) * np.log1p(max(l_usd, 1000.0)) * (max(robust, 0.1) ** 0.5)
        s2 = (l_usd ** 0.5) * (apr ** 0.5)
        return s1 * 0.7 + s2 * 0.3

    else: # Default Smart
        return (robust * 50.0) + (apr * 0.2) + (np.log1p(l_usd) * 5.0)

def run_grid_backtest(
    model_type="RAAM",
    core_ratio=0.70,
    sat_ratio=0.30,
    k_core=3,
    k_sat=3,
    reinvest_mode="INSTANT_ALPHA", # INSTANT_ALPHA, CASH_BUFFER_10, IDLE_CASH
    stop_mode="TIERED_ADAPTIVE",  # TIERED_ADAPTIVE, FIXED_15, TRAILING_10
    rebalance_days=30
):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}

    last_rebalance_date = sim_dates[0]
    daily_values = []
    ejection_count = 0
    rebalance_count = 0

    def select_vaults(snap):
        filtered = []
        for v in snap:
            if not bool(v.get("allow_deposits", True)): continue
            rob = float(v.get("robustness_score", 0) or 0)
            mdd = float(v.get("max_drawdown", 0) or 0)
            apr = float(v.get("apr_30d", 0) or v.get("apr_pct", 0) or 0)

            if rob >= 0.15 and mdd <= 35.0 and apr > 0:
                vc = dict(v)
                vc["calc_score"] = score_vault(v, model_type)
                filtered.append(vc)

        if not filtered:
            filtered = [dict(v) for v in snap[:k_core + k_sat]]
            for v in filtered: v["calc_score"] = score_vault(v, model_type)

        filtered.sort(key=lambda x: x["calc_score"], reverse=True)
        core_v = filtered[:k_core]
        sat_v = filtered[k_core:k_core + k_sat]
        return core_v, sat_v

    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_vaults(first_snap)

    if sat_v:
        c_alloc = (total_capital * core_ratio) / (len(core_v) or 1)
        s_alloc = (total_capital * sat_ratio) / (len(sat_v) or 1)
    else:
        c_alloc = total_capital / (len(core_v) or 1)
        s_alloc = 0.0

    def get_stop_loss_limit(v: dict, is_core: bool):
        if stop_mode == "FIXED_15":
            return 15.0
        elif stop_mode == "TRAILING_10":
            return 10.0
        else: # TIERED_ADAPTIVE
            l_usd = float(v.get("leader_equity_usd", 0) or v.get("leader_equity", 0) or 0)
            if is_core and l_usd >= 40000.0: return 28.0
            elif is_core: return 20.0
            elif l_usd >= 20000.0: return 18.0
            else: return 12.0

    for v in core_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": c_alloc, "amount": c_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": c_alloc / (tvl_s + c_alloc),
            "peak_amount": c_alloc, "invest_date": sim_dates[0], "type": "CORE",
            "mdd_tol": get_stop_loss_limit(v, True)
        }

    for v in sat_v:
        addr = v["address"]
        pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
        active_holdings[addr] = {
            "name": v["name"], "cost": s_alloc, "amount": s_alloc,
            "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
            "share": s_alloc / (tvl_s + s_alloc),
            "peak_amount": s_alloc, "invest_date": sim_dates[0], "type": "SATELLITE",
            "mdd_tol": get_stop_loss_limit(v, False)
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
                pnl_c, _, _ = get_vault_snapshot_pnl_tvl(v_curr)
                pnl_diff = pnl_c - h["pnl_start"]
                my_pnl = pnl_diff * h["share"]
            else:
                daily_r = h["apr_start"] / 100.0 / 365.0
                days_held = max(1, (np.datetime64(curr_date) - np.datetime64(h["invest_date"])).astype(int))
                my_pnl = h["cost"] * ((1.0 + daily_r) ** days_held - 1.0)

            h["amount"] = max(h["cost"] + my_pnl, 0.0)

            if h["amount"] > h["peak_amount"]:
                h["peak_amount"] = h["amount"]

            drawdown_pct = ((h["peak_amount"] - h["amount"]) / h["peak_amount"]) * 100.0 if h["peak_amount"] > 0 else 0.0
            loss_pct = ((h["cost"] - h["amount"]) / h["cost"]) * 100.0 if h["cost"] > 0 else 0.0

            if drawdown_pct >= h["mdd_tol"] or loss_pct >= h["mdd_tol"]:
                cash += h["amount"]
                ejected_today.append(addr)
                ejection_count += 1
            else:
                current_holdings_total += h["amount"]

        for addr in ejected_today:
            del active_holdings[addr]

        # 현금 처리 매커니즘
        if cash > 100.0 and len(active_holdings) > 0:
            if reinvest_mode == "INSTANT_ALPHA":
                add_per = cash / len(active_holdings)
                for addr, h in active_holdings.items():
                    h["amount"] += add_per
                    h["cost"] += add_per
                    v_c = snap_map.get(addr, {})
                    tvl_c = float(v_c.get("tvl", 1.0) or 1.0)
                    h["share"] = h["amount"] / (tvl_c + h["amount"])
                current_holdings_total += cash
                cash = 0.0
            elif reinvest_mode == "CASH_BUFFER_10":
                keep_cash = total_capital * 0.10
                reinvest_amt = max(0.0, cash - keep_cash)
                if reinvest_amt > 100.0:
                    add_per = reinvest_amt / len(active_holdings)
                    for addr, h in active_holdings.items():
                        h["amount"] += add_per
                        h["cost"] += add_per
                        v_c = snap_map.get(addr, {})
                        tvl_c = float(v_c.get("tvl", 1.0) or 1.0)
                        h["share"] = h["amount"] / (tvl_c + h["amount"])
                    current_holdings_total += reinvest_amt
                    cash -= reinvest_amt

        # 정기 리밸런싱
        days_since = (np.datetime64(curr_date) - np.datetime64(last_rebalance_date)).astype(int)
        if days_since >= rebalance_days:
            portfolio_total = current_holdings_total + cash
            core_v, sat_v = select_vaults(snap)

            active_holdings.clear()
            cash = 0.0
            last_rebalance_date = curr_date
            rebalance_count += 1

            if sat_v:
                c_alloc = (portfolio_total * core_ratio) / (len(core_v) or 1)
                s_alloc = (portfolio_total * sat_ratio) / (len(sat_v) or 1)
            else:
                c_alloc = portfolio_total / (len(core_v) or 1)
                s_alloc = 0.0

            for v in core_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
                share = c_alloc / (tvl_s + c_alloc)
                active_holdings[addr] = {
                    "name": v["name"], "cost": c_alloc, "amount": c_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": share, "peak_amount": c_alloc, "invest_date": curr_date,
                    "type": "CORE", "mdd_tol": get_stop_loss_limit(v, True)
                }

            for v in sat_v:
                addr = v["address"]
                pnl_s, tvl_s, apr_s = get_vault_snapshot_pnl_tvl(v)
                share = s_alloc / (tvl_s + s_alloc)
                active_holdings[addr] = {
                    "name": v["name"], "cost": s_alloc, "amount": s_alloc,
                    "pnl_start": pnl_s, "tvl_start": tvl_s, "apr_start": apr_s,
                    "share": share, "peak_amount": s_alloc, "invest_date": curr_date,
                    "type": "SATELLITE", "mdd_tol": get_stop_loss_limit(v, False)
                }

            current_holdings_total = portfolio_total

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
    sortino_downside = rets[rets < 0]
    sortino = float(np.mean(rets) / (np.std(sortino_downside) + 1e-9) * np.sqrt(365)) if len(sortino_downside) > 0 else sharpe

    # Calmar Ratio = CAGR / abs(MDD)
    calmar = cagr / abs(mdd) if abs(mdd) > 0 else 0.0

    return {
        "final_val": round(final_val, 2),
        "tot_ret": round(tot_ret, 2),
        "cagr": round(cagr, 2),
        "mdd": round(mdd, 2),
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
        "ejections": ejection_count,
        "rebalances": rebalance_count
    }

if __name__ == "__main__":
    print("=" * 75)
    print("🧪 [Quantum Grid Search System] 백테스트 시뮬레이션 가동 중...")
    print("=" * 75)

    models = ["RAAM", "SKIN_HEAVY", "SHARPE_MOMENTUM", "SMART_ENSEMBLE"]
    allocations = [(0.80, 0.20, 2, 2), (0.70, 0.30, 3, 3), (0.50, 0.50, 3, 4), (0.40, 0.60, 2, 5)]
    reinvests = ["INSTANT_ALPHA", "CASH_BUFFER_10", "IDLE_CASH"]
    stops = ["TIERED_ADAPTIVE", "FIXED_15", "TRAILING_10"]
    reb_intervals = [14, 30]

    all_results = []

    for m in models:
        for c_r, s_r, kc, ks in allocations:
            for r_mode in reinvests:
                for s_mode in stops:
                    for reb in reb_intervals:
                        res = run_grid_backtest(
                            model_type=m, core_ratio=c_r, sat_ratio=s_r,
                            k_core=kc, k_sat=ks, reinvest_mode=r_mode,
                            stop_mode=s_mode, rebalance_days=reb
                        )
                        label = f"{m} | Alloc {int(c_r*100)}:{int(s_r*100)} (Core {kc}/Sat {ks}) | {r_mode} | {s_mode} | Reb {reb}d"
                        res["config"] = label
                        all_results.append(res)

    # Sort by Calmar Ratio & CAGR & Sharpe
    all_results.sort(key=lambda x: (x["cagr"], x["sharpe"], x["calmar"]), reverse=True)

    print(f"\n총 {len(all_results)} 개 조합 시뮬레이션 완료!")
    print("\n🏆 Top 10 최적 포트폴리오 구동 성과 리스트:")
    print("-" * 110)
    print(f"{'Rank':<5} | {'Configuration':<55} | {'Return':<8} | {'CAGR':<8} | {'MDD':<7} | {'Sharpe':<6} | {'Calmar':<6}")
    print("-" * 110)
    for idx, r in enumerate(all_results[:10], 1):
        print(f"#{idx:<4} | {r['config']:<55} | +{r['tot_ret']:>6.2f}% | {r['cagr']:>6.1f}% | {r['mdd']:>6.2f}% | {r['sharpe']:>5.2f} | {r['calmar']:>5.2f}")

    # Best strategy JSON export
    with open(DATA_DIR / "grid_search_summary.json", "w", encoding="utf-8") as f:
        json.dump(all_results[:20], f, ensure_ascii=False, indent=2)

    print(f"\n상위 20개 최적 전략 내역이 {DATA_DIR / 'grid_search_summary.json'}에 저장되었습니다.")
