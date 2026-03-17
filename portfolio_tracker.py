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


def load_my_portfolio():
    if not os.path.exists(MY_PORT_FILE):
        return {"positions": {}, "invest_date": None, "total_capital": 100000}
    with open(MY_PORT_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    if "positions" in raw:
        return raw
    return {"positions": raw, "invest_date": None, "total_capital": sum(float(v) for v in raw.values())}


def calc_my_portfolio(positions, invest_date, snapshots):
    """내 실제 포트폴리오 수익률 계산"""
    if not positions or not snapshots:
        return None

    dates      = sorted(snapshots.keys())
    latest_dt  = dates[-1]
    latest_map = snapshots[latest_dt]

    total_inv = sum(float(v) for v in positions.values())
    holdings  = []

    for addr, amount in positions.items():
        amount = float(amount)
        # 가장 최신 볼트 정보
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

        # 투자 기간 계산
        try:
            start_dt   = datetime.strptime(invest_date, "%Y-%m-%d") if invest_date else datetime.now()
            days_held  = max(1, (datetime.now() - start_dt).days)
        except Exception:
            days_held = 1

        # 스냅샷 기반 실제 수익 추정
        # invest_date 이후 최초 스냅샷 찾기
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
            # 내 지분 비율로 환산
            my_share       = amount / max(start_tvl, 1)
            my_pnl_real    = pnl_vault_diff * my_share
        else:
            # APR 기반 추정
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
                # If no starting snapshot, guess value based on linear APR
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
                # Missing snapshot for this day, assume value hasn't changed from best known
                daily_total += h["est_value"]
        hist_values.append(round(daily_total, 2))

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
        "history_values": hist_values
    }


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
            apr      = float(v.get("apr_30d", 0))
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

    return {
        "start_date":    start_date,
        "end_date":      end_date,
        "sim_amount":    sim_amount,
        "total_pnl":     round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl / sim_amount * 100, 2),
        "total_value":   round(sim_amount + total_pnl, 2),
        "holdings":      results,
    }
