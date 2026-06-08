#!/usr/bin/env python3
"""
portfolio_tracker.py  —  실제 투자 수익률 추적 (요청 5, 6번)
"""
import json, os, glob
from datetime import datetime
import numpy as np

DATA_DIR      = "vault_data"
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
MY_PORT_FILE  = "my_portfolio.json"


def load_snapshots_all():
    result = {}
    for fp in sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json"))):
        date = os.path.basename(fp).replace(".json", "")
        try:
            with open(fp, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list) and len(raw) > 0:
                result[date] = {v["address"]: v for v in raw if "address" in v}
        except Exception:
            pass
    return result


VIRTUAL_PORTFOLIOS_FILE = os.path.join(DATA_DIR, "virtual_portfolios.json")


def load_my_portfolio():
    if not os.path.exists(MY_PORT_FILE):
        return {"positions": {}, "invest_date": None, "total_capital": 100000}
    with open(MY_PORT_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    if "positions" in raw:
        return raw
    return {"positions": raw, "invest_date": None, "total_capital": sum(float(v) for v in raw.values())}


def load_virtual_portfolios():
    # If my_portfolio.json exists but virtual_portfolios.json does not, migrate it
    if not os.path.exists(VIRTUAL_PORTFOLIOS_FILE) and os.path.exists(MY_PORT_FILE):
        try:
            my_port = load_my_portfolio()
            default_port = {
                "id": "default",
                "name": "기본 포트폴리오",
                "ptype": "custom",
                "total_capital": my_port.get("total_capital", 100000.0),
                "invest_date": my_port.get("invest_date") or datetime.now().strftime("%Y-%m-%d"),
                "positions": my_port.get("positions", {})
            }
            save_virtual_portfolios([default_port])
        except Exception as e:
            print(f"[PORTFOLIO MIGRATION ERROR] {e}")

    if not os.path.exists(VIRTUAL_PORTFOLIOS_FILE):
        return []
    try:
        with open(VIRTUAL_PORTFOLIOS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_virtual_portfolios(portfolios):
    os.makedirs(os.path.dirname(VIRTUAL_PORTFOLIOS_FILE), exist_ok=True)
    with open(VIRTUAL_PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolios, f, ensure_ascii=False, indent=2)


def calc_portfolio_performance(positions, invest_date, total_capital, snapshots):
    """Calculates performance metrics, holdings, and equity curve values for a portfolio configuration."""
    if not positions or not snapshots:
        return {
            "total_invested": 0.0,
            "total_value": 0.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "monthly_est": 0.0,
            "annual_est": 0.0,
            "holdings": [],
            "n_vaults": 0,
            "invest_date": invest_date,
            "analysis_date": None,
            "days_held": 0,
            "history_dates": [],
            "history_values": [],
            "mdd": 0.0
        }

    # Normalize positions: if positions sum to <= 1.05, treat as decimal weights;
    # if positions sum to <= 100.5, treat as percentage weights;
    # otherwise, treat as absolute USD amounts.
    raw_sum = sum(float(v) for v in positions.values())
    scaled_positions = {}
    if raw_sum <= 1.05 and total_capital > 100:
        for addr, w in positions.items():
            scaled_positions[addr] = float(w) * total_capital
    elif raw_sum <= 100.5 and total_capital > 1000:
        for addr, w in positions.items():
            scaled_positions[addr] = (float(w) / 100.0) * total_capital
    else:
        scaled_positions = {addr: float(val) for addr, val in positions.items()}

    dates      = sorted(snapshots.keys())
    latest_dt  = dates[-1] if dates else None
    latest_map = snapshots[latest_dt] if latest_dt else {}

    total_inv = sum(float(v) for v in scaled_positions.values())
    holdings  = []

    for addr, amount in scaled_positions.items():
        amount = float(amount)
        # Get the latest vault info
        v = latest_map.get(addr, {})
        if not v:
            for d in reversed(dates):
                v = snapshots[d].get(addr, {})
                if v: break

        name       = v.get("name", addr[:16] + "...")
        apr_30d    = float(v.get("apr_30d", 0))
        mdd        = float(v.get("max_drawdown", 0))
        tvl        = float(v.get("tvl", 1))
        robust     = float(v.get("robustness_score", 0))
        grade      = v.get("equity_curve_grade", "-")
        allow_dep  = v.get("allow_deposits", True)
        leader_eq  = float(v.get("leader_equity_ratio", 0))

        # Calculate holding days
        try:
            start_dt   = datetime.strptime(invest_date, "%Y-%m-%d") if invest_date else datetime.now()
            days_held  = max(1, (datetime.now() - start_dt).days)
        except Exception:
            days_held = 1

        # Locate first snapshot on/after invest_date
        first_snap_pnl = None
        for d in dates:
            if invest_date and d >= invest_date:
                snap_v = snapshots[d].get(addr, {})
                if snap_v:
                    pnl_arr = snap_v.get("alltime_pnl", [])
                    if pnl_arr:
                        first_snap_pnl = (d, pnl_arr[-1], float(snap_v.get("tvl", tvl)))
                        break

        latest_pnl_arr = v.get("alltime_pnl", [])

        if first_snap_pnl and latest_pnl_arr:
            _, start_pnl_val, start_tvl = first_snap_pnl
            pnl_vault_diff = latest_pnl_arr[-1] - start_pnl_val
            my_share       = amount / max(start_tvl, 1)
            my_pnl_real    = pnl_vault_diff * my_share
        else:
            # Fallback to APR calculation
            daily_r        = apr_30d / 100 / 365
            my_pnl_real    = amount * ((1 + daily_r) ** days_held - 1)

        est_value  = amount + my_pnl_real
        pnl_pct    = my_pnl_real / amount * 100 if amount > 0 else 0
        monthly_est= amount * apr_30d / 100 / 12

        holdings.append({
            "address":      addr,
            "name":         name,
            "invested_usd": round(amount, 2),
            "weight_pct":   round(amount / total_inv * 100, 1) if total_inv > 0 else 0,
            "apr_30d":      round(apr_30d, 2),
            "mdd":          round(mdd, 2),
            "tvl":          round(tvl, 0),
            "robustness":   round(robust, 3),
            "grade":        grade,
            "leader_eq":    round(leader_eq * 100, 1),
            "allow_deposits": allow_dep,
            "days_held":    days_held,
            "est_value":    round(est_value, 2),
            "pnl":          round(my_pnl_real, 2),
            "pnl_pct":      round(pnl_pct, 2),
            "monthly_est":  round(monthly_est, 2),
            "is_danger":    (mdd > 30 or apr_30d < -5),
            "_first_pnl":   first_snap_pnl
        })

    holdings.sort(key=lambda x: x["pnl"], reverse=True)
    total_val  = sum(h["est_value"] for h in holdings)
    total_pnl  = total_val - total_inv
    total_pct  = total_pnl / total_inv * 100 if total_inv > 0 else 0

    # Build history series
    hist_dates = [d for d in dates if not invest_date or d >= invest_date]
    hist_values = []
    
    for d in hist_dates:
        daily_total = 0
        for h in holdings:
            addr = h["address"]
            amt = h["invested_usd"]
            if not h["_first_pnl"]:
                try:
                    start_dt = datetime.strptime(invest_date, "%Y-%m-%d") if invest_date else datetime.now()
                    d_dt = datetime.strptime(d, "%Y-%m-%d")
                    days_gap = max(0, (d_dt - start_dt).days)
                except: days_gap = 0
                daily_r = h["apr_30d"] / 100 / 365
                daily_total += amt * ((1 + daily_r) ** days_gap)
                continue
                
            _, start_pnl_val, start_tvl = h["_first_pnl"]
            v_snap_d = snapshots[d].get(addr, {})
            if v_snap_d and v_snap_d.get("alltime_pnl"):
                d_pnl_val = v_snap_d["alltime_pnl"][-1]
                pnl_diff = d_pnl_val - start_pnl_val
                my_share = amt / max(start_tvl, 1)
                daily_total += amt + (pnl_diff * my_share)
            else:
                daily_total += h["est_value"]
        hist_values.append(round(daily_total, 2))

    # Calculate portfolio MDD
    mdd_val = 0.0
    if hist_values:
        eq_arr = np.array(hist_values, dtype=float)
        if len(eq_arr) > 0:
            rm = np.maximum.accumulate(eq_arr)
            denom = np.where(rm > 0, rm, 1.0)
            dd = (rm - eq_arr) / denom * 100
            mdd_val = round(float(dd.max()), 2)

    return {
        "total_invested": round(total_inv, 2),
        "total_value":    round(total_val, 2),
        "total_pnl":      round(total_pnl, 2),
        "total_pnl_pct":  round(total_pct, 2),
        "monthly_est":    round(sum(h["monthly_est"] for h in holdings), 2),
        "annual_est":     round(sum(h["monthly_est"] for h in holdings) * 12, 2),
        "holdings":       holdings,
        "n_vaults":       len(holdings),
        "invest_date":    invest_date,
        "analysis_date":  latest_dt,
        "days_held":      holdings[0]["days_held"] if holdings else 0,
        "history_dates":  hist_dates,
        "history_values": hist_values,
        "mdd":            mdd_val
    }


def calc_my_portfolio(positions, invest_date, snapshots):
    """Fallback calc_my_portfolio delegating to calc_portfolio_performance."""
    total_capital = sum(float(v) for v in positions.values()) if positions else 100000.0
    return calc_portfolio_performance(positions, invest_date, total_capital, snapshots)


def get_portfolio_insights(positions, performance, latest_snapshot):
    """Diagnoses the portfolio and returns a list of text insights."""
    insights = []
    if not positions or not performance or not latest_snapshot:
        return ["포트폴리오 구성 요소가 부족하여 진단할 수 없습니다."]

    holdings = performance.get("holdings", [])
    if not holdings:
        return ["포트폴리오에 보유한 볼트가 없습니다."]

    # 1. Diversification check
    max_weight_holding = max(holdings, key=lambda x: x["weight_pct"])
    if max_weight_holding["weight_pct"] > 50.0:
        insights.append(
            f"⚠️ 분산 투자 경고: 단일 볼트 '{max_weight_holding['name']}'의 비중이 "
            f"{max_weight_holding['weight_pct']}%로 50%를 초과합니다. 리스크 분산을 위해 비중 조절을 권장합니다."
        )

    # 2. Robustness check
    total_invested = performance.get("total_invested", 0.0)
    if total_invested > 0:
        weighted_robustness = sum(
            h["invested_usd"] * h["robustness"] for h in holdings
        ) / total_invested
    else:
        weighted_robustness = 0.0

    if weighted_robustness < 0.4:
        insights.append(
            f"⚠️ 로버스트니스 경고: 포트폴리오의 가중 평균 로버스트니스 점수가 "
            f"{weighted_robustness:.2f}로 기준치(0.4) 미만입니다. 장기적 안정성이 낮을 수 있습니다."
        )

    # 3. Risk warning
    portfolio_mdd = performance.get("mdd", 0.0)
    high_vault_mdd = [h for h in holdings if h["mdd"] > 30.0]

    if portfolio_mdd > 20.0 or high_vault_mdd:
        mdd_msgs = []
        if portfolio_mdd > 20.0:
            mdd_msgs.append(f"포트폴리오의 최대 낙폭(MDD)이 {portfolio_mdd:.2f}%로 20%를 초과합니다.")
        if high_vault_mdd:
            names = ", ".join([f"'{h['name']}'({h['mdd']}%)" for h in high_vault_mdd])
            mdd_msgs.append(f"개별 볼트 중 MDD가 30%를 초과하는 위험 자산이 포함되어 있습니다: {names}")
        insights.append(f"⚠️ 위험 관리 경고: {' '.join(mdd_msgs)}")

    # 4. Barbell strategy check
    snapshot_map = {v["address"]: v for v in latest_snapshot if "address" in v}
    
    core_usd = 0.0
    satellite_usd = 0.0
    unknown_usd = 0.0
    
    for h in holdings:
        addr = h["address"]
        v = snapshot_map.get(addr, {})
        group = v.get("barbell_group")
        
        # Fallback classification if barbell_group is not specified
        if not group:
            mdd_val = float(v.get("max_drawdown", h["mdd"]))
            rob_val = float(v.get("robustness_score", h["robustness"]))
            if mdd_val <= 15.0 and rob_val >= 0.5:
                group = "CORE"
            else:
                group = "SATELLITE"
                
        if group == "CORE":
            core_usd += h["invested_usd"]
        elif group == "SATELLITE":
            satellite_usd += h["invested_usd"]
        else:
            unknown_usd += h["invested_usd"]

    total_usd = core_usd + satellite_usd + unknown_usd
    if total_usd > 0:
        core_pct = (core_usd / total_usd) * 100.0
        satellite_pct = (satellite_usd / total_usd) * 100.0
        
        if not (50.0 <= core_pct <= 80.0) or not (20.0 <= satellite_pct <= 50.0):
            insights.append(
                f"⚖️ 바벨 전략 제안: 현재 포트폴리오 비중(CORE: {core_pct:.1f}%, SATELLITE: {satellite_pct:.1f}%)이 "
                f"이상적인 균형(CORE 50%~80%, SATELLITE 20%~50%)을 벗어났습니다. 비중 리밸런싱을 고려해보세요."
            )
    
    if not insights:
        insights.append("✨ 포트폴리오가 정상 범위 내에서 안정적으로 운영되고 있습니다. (진단 결과 특이사항 없음)")

    return insights


def run_scenario_analysis(portfolios, snapshots):
    """Returns a simulated report for each portfolio under 4 scenarios."""
    if not snapshots:
        return {}

    dates = sorted(snapshots.keys())
    latest_dt = dates[-1] if dates else None
    latest_map = snapshots[latest_dt] if latest_dt else {}

    reports = {}

    for port in portfolios:
        port_id = port.get("id")
        positions = port.get("positions", {})
        total_capital = float(port.get("total_capital", 100000.0))
        
        # Calculate weights
        raw_sum = sum(float(v) for v in positions.values())
        scaled_positions = {}
        if raw_sum <= 1.05 and total_capital > 100:
            for addr, w in positions.items():
                scaled_positions[addr] = float(w) * total_capital
        elif raw_sum <= 100.5 and total_capital > 1000:
            for addr, w in positions.items():
                scaled_positions[addr] = (float(w) / 100.0) * total_capital
        else:
            scaled_positions = {addr: float(val) for addr, val in positions.items()}

        total_inv = sum(float(v) for v in scaled_positions.values())
        if total_inv <= 0:
            continue

        # Get vault details
        vault_details = []
        for addr, amount in scaled_positions.items():
            w = amount / total_inv
            v = latest_map.get(addr, {})
            if not v:
                for d in reversed(dates):
                    v = snapshots[d].get(addr, {})
                    if v: break
            
            apr = float(v.get("apr_30d", 0))
            mdd = float(v.get("max_drawdown", 0))
            vault_details.append({
                "weight": w,
                "apr": apr,
                "mdd": mdd
            })

        # 1. 상승장 (Bull Market)
        bull_ret = sum(vd["weight"] * vd["apr"] * 1.5 for vd in vault_details)
        bull_mdd = sum(vd["weight"] * vd["mdd"] * 0.5 for vd in vault_details)
        bull_val = total_capital * (1.0 + bull_ret / 100.0)

        # 2. 하락장 (Bear Market)
        bear_mdd = sum(vd["weight"] * vd["mdd"] for vd in vault_details)
        bear_ret = -bear_mdd
        bear_val = total_capital * (1.0 + bear_ret / 100.0)

        # 3. 고변동성 (High Volatility)
        vol_ret = sum(vd["weight"] * vd["apr"] * 0.8 for vd in vault_details)
        vol_mdd = sum(vd["weight"] * vd["mdd"] * 1.3 for vd in vault_details)
        vol_val = total_capital * (1.0 + vol_ret / 100.0)

        # 4. 안정수익 (Stable Yield)
        stable_rets = []
        for vd in vault_details:
            if vd["mdd"] <= 10.0:
                sim_apr = vd["apr"]
            else:
                sim_apr = vd["apr"] * (10.0 / max(vd["mdd"], 1.0))
            stable_rets.append(vd["weight"] * sim_apr)
        stable_ret = sum(stable_rets)
        stable_mdd = sum(vd["weight"] * min(vd["mdd"], 10.0) for vd in vault_details)
        stable_val = total_capital * (1.0 + stable_ret / 100.0)

        reports[port_id] = {
            "name": port.get("name"),
            "total_capital": total_capital,
            "scenarios": {
                "bull": {
                    "scenario_name": "상승장 (Bull Market)",
                    "expected_return_pct": round(bull_ret, 2),
                    "simulated_mdd": round(bull_mdd, 2),
                    "expected_ending_value": round(bull_val, 2),
                    "desc": "가상 상승장 시뮬레이션: 미래 수익률을 현재 30일 APR의 1.5배로 가정하여 낙관적인 자산 성장률을 프로젝션합니다."
                },
                "bear": {
                    "scenario_name": "하락장 (Bear Market)",
                    "expected_return_pct": round(bear_ret, 2),
                    "simulated_mdd": round(bear_mdd, 2),
                    "expected_ending_value": round(bear_val, 2),
                    "desc": "시장 크래시 시뮬레이션: 포트폴리오 내 모든 볼트가 과거 최대 낙폭(MDD)을 동시에 겪는 최악의 상황을 시뮬레이션합니다."
                },
                "volatility": {
                    "scenario_name": "고변동성 (High Volatility)",
                    "expected_return_pct": round(vol_ret, 2),
                    "simulated_mdd": round(vol_mdd, 2),
                    "expected_ending_value": round(vol_val, 2),
                    "desc": "변동성 급증 시뮬레이션: 시장의 불확실성이 커져 수익률은 20% 감소하고 개별 볼트의 MDD는 1.3배 증가하는 시나리오입니다."
                },
                "stable": {
                    "scenario_name": "안정수익 (Stable Yield)",
                    "expected_return_pct": round(stable_ret, 2),
                    "simulated_mdd": round(stable_mdd, 2),
                    "expected_ending_value": round(stable_val, 2),
                    "desc": "보수적 안정수익 시뮬레이션: MDD 10% 이하의 저위험 볼트는 수익률을 유지하고, 고위험 볼트의 수익률은 MDD 비율로 페널티를 주어 시뮬레이션합니다."
                }
            }
        }
    return reports


def simulate_rec_backtest(recs, snapshots, start_date=None, sim_amount=100000.0):
    """요청 5: 추천 볼트를 start_date에 담았다면 지금 성적"""
    if not snapshots:
        return None

    dates = sorted(snapshots.keys())
    if not start_date:
        start_date = dates[0]
    end_date   = dates[-1]
    start_snap = snapshots.get(start_date, {})
    end_snap   = snapshots.get(end_date, {})

    results = []
    for v in recs:
        addr   = v.get("address", "")
        alloc  = v.get("suggested_allocation", 0) / 100
        amount = sim_amount * alloc
        name   = v.get("name", addr[:16])

        v_s = start_snap.get(addr, {})
        v_e = end_snap.get(addr, {})
        tvl = float((v_e or v_s or {}).get("tvl", 0))

        p_s = v_s.get("alltime_pnl", []) if v_s else []
        p_e = v_e.get("alltime_pnl", []) if v_e else []

        if p_s and p_e and tvl > 0:
            pnl_diff = p_e[-1] - p_s[-1]
            my_pnl   = pnl_diff * (amount / tvl)
        else:
            # APR 추정
            try:
                d_start = datetime.strptime(start_date, "%Y-%m-%d")
                d_end   = datetime.strptime(end_date, "%Y-%m-%d")
                days    = max(1, (d_end - d_start).days)
            except Exception:
                days = 1
            apr      = float(v.get("apr_30d", v_e.get("apr_30d", v_s.get("apr_30d", 0))))
            my_pnl   = amount * apr / 100 / 365 * days

        results.append({
            "name":       name,
            "address":    addr,
            "alloc_pct":  round(alloc * 100, 1),
            "invested":   round(amount, 2),
            "pnl":        round(my_pnl, 2),
            "pnl_pct":    round(my_pnl / amount * 100, 2) if amount > 0 else 0,
            "final_val":  round(amount + my_pnl, 2),
        })

    results.sort(key=lambda x: x["pnl"], reverse=True)
    total_pnl = sum(r["pnl"] for r in results)

    # ── 시계열 백테스트 (history) ──
    # If start_date isn't in dates, still create points from start_date to earliest snap date?
    # To keep it simple, we just use available snap dates plus start_date if it's missing.
    hist_dates = [d for d in dates if d >= start_date and d <= end_date]
    if start_date not in hist_dates:
        hist_dates.insert(0, start_date)
        
    hist_values = []
    
    for d in hist_dates:
        d_val = 0
        snap_d = snapshots.get(d, {})
        for v in recs:
            addr   = v.get("address", "")
            alloc  = v.get("suggested_allocation", 0) / 100
            amt    = sim_amount * alloc
            
            v_start = start_snap.get(addr, {})
            p_s = v_start.get("alltime_pnl", []) if v_start else []
            tvl_s = float(v_start.get("tvl", 0)) if v_start else 0

            v_d = snap_d.get(addr, {})
            p_d = v_d.get("alltime_pnl", []) if v_d else []
            
            v_e = end_snap.get(addr, {})
            
            if p_s and p_d and tvl_s > 0:
                pnl_diff = p_d[-1] - p_s[-1]
                my_pnl_d = pnl_diff * (amt / tvl_s)
            else:
                try:
                    ds = datetime.strptime(start_date, "%Y-%m-%d")
                    dd = datetime.strptime(d, "%Y-%m-%d")
                    days_gap = max(0, (dd - ds).days)
                except: days_gap = 0
                apr = float(v.get("apr_30d", v_d.get("apr_30d", v_e.get("apr_30d", 0))))
                my_pnl_d = amt * apr / 100 / 365 * days_gap

            d_val += amt + my_pnl_d

        hist_values.append(round(d_val, 2))

    return {
        "start_date":    start_date,
        "end_date":      end_date,
        "sim_amount":    sim_amount,
        "total_pnl":     round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl / sim_amount * 100, 2),
        "total_value":   round(sim_amount + total_pnl, 2),
        "holdings":      results,
        "history_dates": hist_dates,
        "history_values": hist_values
    }
