#!/usr/bin/env python3
"""
portfolio_tracker.py  —  실제 투자 수익률 추적 (요청 5, 6번)
"""
import json, os, glob
from datetime import datetime
import numpy as np
from io_utils import atomic_write_json

DATA_DIR      = "vault_data"
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
MY_PORT_FILE  = "my_portfolio.json"


_SNAPS_MEM_CACHE = {"sig": None, "data": None}


def load_snapshots_all():
    files = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json")))
    sig = (len(files), files[-1] if files else "", os.path.getmtime(files[-1]) if files else 0.0)
    if _SNAPS_MEM_CACHE["sig"] == sig and _SNAPS_MEM_CACHE["data"] is not None:
        return _SNAPS_MEM_CACHE["data"]
    result = {}
    for fp in files:
        date = os.path.basename(fp).replace(".json", "")
        try:
            with open(fp, encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, list) and len(raw) > 0:
                result[date] = {v["address"]: v for v in raw if "address" in v}
        except Exception:
            pass
    _SNAPS_MEM_CACHE["sig"] = sig
    _SNAPS_MEM_CACHE["data"] = result
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
                "name": "나의 실제 포트폴리오",
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
    atomic_write_json(VIRTUAL_PORTFOLIOS_FILE, portfolios, indent=2)


def calc_portfolio_performance(positions, invest_date, total_capital, snapshots):
    """Calculates performance metrics, holdings, and equity curve values for a portfolio configuration."""
    if not positions or not snapshots:
        return {
            "total_invested": 0.0,
            "total_value": 0.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "net_total_pnl": 0.0,
            "net_total_pnl_pct": 0.0,
            "net_total_value": 0.0,
            "avg_monthly_gross_pct": 0.0,
            "avg_monthly_net_pct": 0.0,
            "monthly_returns": [],
            "monthly_est": 0.0,
            "annual_est": 0.0,
            "holdings": [],
            "n_vaults": 0,
            "invest_date": invest_date,
            "analysis_date": None,
            "days_held": 0,
            "history_dates": [],
            "history_values": [],
            "net_history_values": [],
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
        apr_calc   = float(v.get("apr_30d", 0))
        apr_30d    = float(v["apr_pct"]) if v.get("apr_pct") is not None else apr_calc
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
            daily_r        = apr_calc / 100 / 365
            my_pnl_real    = amount * ((1 + daily_r) ** days_held - 1)

        est_value  = amount + my_pnl_real
        pnl_pct    = my_pnl_real / amount * 100 if amount > 0 else 0
        monthly_est= amount * apr_30d / 100 / 12

        # Net profit after 10% leader fee (profit share)
        net_pnl = my_pnl_real * 0.9 if my_pnl_real > 0 else my_pnl_real
        net_val = amount + net_pnl

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
            "net_pnl":      round(net_pnl, 2),
            "net_pnl_pct":  round(net_pnl / amount * 100, 2) if amount > 0 else 0,
            "net_value":    round(net_val, 2),
            "monthly_est":  round(monthly_est, 2),
            "is_danger":    (mdd > 30 or apr_30d < -5),
            "_first_pnl":   first_snap_pnl
        })

    holdings.sort(key=lambda x: x["pnl"], reverse=True)
    total_val  = sum(h["est_value"] for h in holdings)
    total_pnl  = total_val - total_inv
    total_pct  = total_pnl / total_inv * 100 if total_inv > 0 else 0

    net_total_pnl = sum(h["net_pnl"] for h in holdings)
    net_total_val = total_inv + net_total_pnl
    net_total_pct = net_total_pnl / total_inv * 100 if total_inv > 0 else 0

    # Build history series (chronological carry-forward per holding, avoiding future leakage on missing days)
    hist_dates = [d for d in dates if not invest_date or d >= invest_date]
    hist_values = []
    net_hist_values = []
    last_gross_by_addr = {h["address"]: float(h["invested_usd"]) for h in holdings}

    for d in hist_dates:
        daily_total = 0.0
        daily_net_total = 0.0
        for h in holdings:
            addr = h["address"]
            amt = float(h["invested_usd"])
            if not h["_first_pnl"]:
                try:
                    start_dt = datetime.strptime(invest_date, "%Y-%m-%d") if invest_date else datetime.now()
                    d_dt = datetime.strptime(d, "%Y-%m-%d")
                    days_gap = max(0, (d_dt - start_dt).days)
                except Exception:
                    days_gap = 0
                daily_r = h["apr_30d"] / 100 / 365
                vg = amt * ((1 + daily_r) ** days_gap)
                last_gross_by_addr[addr] = vg
            else:
                first_d, start_pnl_val, start_tvl = h["_first_pnl"]
                if d >= first_d:
                    v_snap_d = snapshots[d].get(addr, {})
                    if v_snap_d and v_snap_d.get("alltime_pnl"):
                        d_pnl_val = v_snap_d["alltime_pnl"][-1]
                        pnl_diff = d_pnl_val - start_pnl_val
                        my_share = amt / max(start_tvl, 1)
                        last_gross_by_addr[addr] = amt + (pnl_diff * my_share)
                vg = last_gross_by_addr[addr]
            gp = vg - amt
            vn = amt + (gp * 0.9 if gp > 0 else gp)
            daily_total += vg
            daily_net_total += vn
        hist_values.append(round(daily_total, 2))
        net_hist_values.append(round(daily_net_total, 2))

    # Calendar month-by-month return breakdown (Gross & Net after 10% profit share)
    monthly_returns = []
    if hist_dates and hist_values:
        ym_buckets = {}
        for d, vg, vn in zip(hist_dates, hist_values, net_hist_values):
            ym_buckets.setdefault(d[:7], []).append((d, vg, vn))
        prev_g = float(total_inv)
        prev_n = float(total_inv)
        for ym in sorted(ym_buckets.keys()):
            items = ym_buckets[ym]
            start_d = items[0][0]
            end_d, end_g, end_n = items[-1]
            r_g = ((end_g / prev_g) - 1.0) * 100.0 if prev_g > 0 else 0.0
            r_n = ((end_n / prev_n) - 1.0) * 100.0 if prev_n > 0 else 0.0
            monthly_returns.append({
                "month": ym,
                "short_label": f"{ym[2:4]}.{ym[5:7]}",
                "month_num": f"{int(ym[5:7])}월",
                "start_date": start_d,
                "end_date": end_d,
                "days": len(items),
                "start_net": round(prev_n, 2),
                "end_net": round(end_n, 2),
                "net_pnl": round(end_n - prev_n, 2),
                "net_pct": round(r_n, 2),
                "gross_pnl": round(end_g - prev_g, 2),
                "gross_pct": round(r_g, 2),
            })
            prev_g = end_g
            prev_n = end_n

    days_held_val = holdings[0]["days_held"] if holdings else 0
    avg_monthly_gross_pct = 0.0
    avg_monthly_net_pct = 0.0
    if days_held_val > 0:
        if days_held_val < 7:
            avg_monthly_gross_pct = (total_pct / days_held_val) * 30.4375
            avg_monthly_net_pct = (net_total_pct / days_held_val) * 30.4375
        else:
            avg_monthly_gross_pct = ((1.0 + max(total_pct, -99.9999) / 100.0) ** (30.4375 / days_held_val) - 1.0) * 100.0
            avg_monthly_net_pct = ((1.0 + max(net_total_pct, -99.9999) / 100.0) ** (30.4375 / days_held_val) - 1.0) * 100.0

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
        "net_total_pnl":  round(net_total_pnl, 2),
        "net_total_pnl_pct": round(net_total_pct, 2),
        "net_total_value": round(net_total_val, 2),
        "avg_monthly_gross_pct": round(avg_monthly_gross_pct, 2),
        "avg_monthly_net_pct":   round(avg_monthly_net_pct, 2),
        "monthly_returns":       monthly_returns,
        "monthly_est":    round(sum(h["monthly_est"] for h in holdings), 2),
        "annual_est":     round(sum(h["monthly_est"] for h in holdings) * 12, 2),
        "holdings":       holdings,
        "n_vaults":       len(holdings),
        "invest_date":    invest_date,
        "analysis_date":  latest_dt,
        "days_held":      days_held_val,
        "history_dates":  hist_dates,
        "history_values": hist_values,
        "net_history_values": net_hist_values,
        "mdd":            mdd_val
    }



import threading as _threading
import time as _time

_LIVE_CACHE_LOCK = _threading.Lock()
_LIVE_CACHE = {"ts": 0.0, "data": None}


def calc_live_onchain_portfolio_performance(p_cfg, snapshots, ttl_sec=4.0):
    """
    Computes 100% real-time on-chain performance for '나의 실제 포트폴리오' (id='default')
    directly from Hyperliquid Mainnet `userVaultEquities` + `vaultDetails(vaultAddress, user)`:
      - invested_usd = exact basis (`vaultEquity - pnl`)
      - est_value    = exact `Your Deposits` (`vaultEquity`)
      - pnl          = exact `All-time Earned` / active PnL (`pnl`)
      - net_value    = exact post-10% withdrawal payout (`vaultWithdraw` formula)
      - apr_30d      = exact Hyperliquid `Past Month Return` (`apr * 100`)
    """
    now_t = _time.time()
    with _LIVE_CACHE_LOCK:
        if _LIVE_CACHE["data"] is not None and (now_t - _LIVE_CACHE["ts"]) < ttl_sec:
            return _LIVE_CACHE["data"]

    try:
        import hl_auto_vault_bot as _bot
        account_addr, _, _ = _bot.get_wallet_credentials_meta()
        if not account_addr:
            my_pf = load_my_portfolio()
            account_addr = my_pf.get("account_address")
        onchain = _bot.fetch_onchain_account_state(account_addr)
    except Exception:
        onchain = {"connected": False}

    if not onchain.get("connected"):
        return calc_portfolio_performance(
            p_cfg.get("positions", {}),
            p_cfg.get("invest_date"),
            p_cfg.get("total_capital", 100000.0),
            snapshots,
        )

    v_pos_map = onchain.get("vault_positions") or {}
    cash_usd = round(
        float(onchain.get("perp_withdrawable_usd", 0.0) or 0.0)
        + float(onchain.get("spot_usdc_usd", 0.0) or 0.0),
        2,
    )

    if not v_pos_map and cash_usd < 1.0:
        return calc_portfolio_performance(
            p_cfg.get("positions", {}),
            p_cfg.get("invest_date"),
            p_cfg.get("total_capital", 100000.0),
            snapshots,
        )

    v_details = _bot.fetch_live_vault_follower_details(account_addr, list(v_pos_map.keys()))

    dates = sorted(snapshots.keys()) if snapshots else []
    latest_dt = dates[-1] if dates else datetime.now().strftime("%Y-%m-%d")
    latest_map = snapshots[latest_dt] if (snapshots and latest_dt in snapshots) else {}

    raw_holdings = []
    for addr, pos_info in v_pos_map.items():
        addr_low = addr.lower()
        det = v_details.get(addr_low) or {}
        v = latest_map.get(addr_low, {})
        if not v and snapshots:
            for d in reversed(dates):
                v = snapshots[d].get(addr_low, {})
                if v:
                    break

        eq_val = float(det.get("vault_equity_usd", pos_info.get("equity_usd", 0.0)) or 0.0)
        if "pnl_usd" in det:
            cur_pnl = float(det["pnl_usd"])
            all_pnl = float(det.get("all_time_pnl_usd", cur_pnl))
            principal = float(det["principal_usd"])
        else:
            saved_p = float((p_cfg.get("positions") or {}).get(addr_low, eq_val) or eq_val)
            principal = round(saved_p, 2)
            cur_pnl = eq_val - principal
            all_pnl = cur_pnl

        comm_rate = float(det.get("leader_commission", 0.10) or 0.10)
        net_pnl_val = cur_pnl * (1.0 - comm_rate) if cur_pnl > 0 else cur_pnl
        net_val = principal + net_pnl_val

        hl_apr = float(det["hl_apr_pct"]) if "hl_apr_pct" in det else float(v.get("apr_pct", v.get("apr_30d", 0.0)) or 0.0)
        mdd = float(v.get("max_drawdown", 0.0) or 0.0)
        tvl = float(det["tvl_usd"]) if det.get("tvl_usd") is not None else float(v.get("tvl", 1.0) or 1.0)
        robust = float(v.get("robustness_score", 0.0) or 0.0)
        grade = v.get("equity_curve_grade", "-")
        allow_dep = bool(det.get("allow_deposits", v.get("allow_deposits", True)))
        leader_eq = float(v.get("leader_equity_ratio", 0.0) or 0.0)
        name = str(det.get("name") or v.get("name") or (addr_low[:16] + "..."))

        pnl_pct = (cur_pnl / principal * 100.0) if principal > 0 else 0.0
        net_pnl_pct = (net_pnl_val / principal * 100.0) if principal > 0 else 0.0
        monthly_est = principal * hl_apr / 100.0 / 12.0

        raw_holdings.append({
            "address": addr_low,
            "name": name,
            "invested_usd": round(principal, 2),
            "weight_pct": 0.0,  # filled after sum
            "apr_30d": round(hl_apr, 2),
            "monthly_return_pct": round(float(v.get("monthly_return", 0.0) or 0.0), 2),
            "mdd": round(mdd, 2),
            "tvl": round(tvl, 0),
            "robustness": round(robust, 3),
            "grade": grade,
            "leader_eq": round(leader_eq * 100.0, 1),
            "allow_deposits": allow_dep,
            "days_held": 1,  # filled from active session start below
            "est_value": round(eq_val, 2),
            "pnl": round(cur_pnl, 2),
            "all_time_pnl": round(all_pnl, 2),
            "pnl_pct": round(pnl_pct, 2),
            "net_pnl": round(net_pnl_val, 2),
            "net_pnl_pct": round(net_pnl_pct, 2),
            "net_value": round(net_val, 2),
            "monthly_est": round(monthly_est, 2),
            "is_locked": bool(pos_info.get("is_locked", False)),
            "locked_until": pos_info.get("locked_until"),
            "is_danger": (mdd > 35.0 or float(v.get("apr_30d", 0.0) or 0.0) < -130.0),
        })

    active_val_sum = sum(h["est_value"] for h in raw_holdings)
    active_prin_sum = round(sum(h["invested_usd"] for h in raw_holdings), 2)
    active_unrealized_pnl = round(active_val_sum - active_prin_sum, 2)
    for h in raw_holdings:
        h["weight_pct"] = round(h["est_value"] / active_val_sum * 100.0, 1) if active_val_sum > 0 else 0.0

    raw_holdings.sort(key=lambda x: x["pnl"], reverse=True)

    # Reconstruct exact active deployment session & rebalance history from L1 ledger
    # (never using `followerState.vaultEntryTime`, which Hyperliquid retains across full exits!)
    ledger_summary = _bot.fetch_wallet_vault_ledger_summary(
        account_addr,
        vault_name_map={h["address"]: h["name"] for h in raw_holdings},
        live_holdings_map={h["address"]: h for h in raw_holdings},
        snapshots=snapshots,
        ttl_sec=(0.0 if ttl_sec <= 0 else 10.0),
    )

    if ledger_summary.get("ok") and ledger_summary.get("invest_date"):
        invest_date = str(ledger_summary["invest_date"])
        entry_dt = datetime.fromtimestamp(float(ledger_summary["session_start_ms"]) / 1000.0)
        days_held_exact = max(0.05, (datetime.now() - entry_dt).total_seconds() / 86400.0)
        days_held_int = max(1, int(round(days_held_exact)))
    else:
        invest_date = str(p_cfg.get("invest_date") or latest_dt)
        try:
            start_dt = datetime.strptime(invest_date, "%Y-%m-%d")
            days_held_int = max(1, (datetime.now() - start_dt).days)
            days_held_exact = float(days_held_int)
        except Exception:
            days_held_int = 1
            days_held_exact = 1.0

    for h in raw_holdings:
        h["days_held"] = days_held_int

    fallback_cap = float(p_cfg.get("total_capital", 0.0) or 0.0)
    if fallback_cap < 100.0:
        fallback_cap = round(active_prin_sum + cash_usd, 2)
    if ledger_summary.get("ok") and float(ledger_summary.get("net_capital_usd", 0.0) or 0.0) >= 100.0:
        base_cap = round(float(ledger_summary["net_capital_usd"]), 2)
    else:
        base_cap = _bot.compute_net_wallet_capital(account_addr, fallback_capital=fallback_cap)
    if base_cap < 100.0:
        base_cap = round(active_prin_sum + cash_usd, 2)

    total_val = round(active_val_sum + cash_usd, 2)
    total_pnl = round(total_val - base_cap, 2)
    total_pct = round((total_pnl / base_cap * 100.0), 2) if base_cap > 0 else 0.0

    active_net_val_sum = sum(h["net_value"] for h in raw_holdings)
    net_total_val = round(active_net_val_sum + cash_usd, 2)
    net_total_pnl = round(net_total_val - base_cap, 2)
    net_total_pct = round((net_total_pnl / base_cap * 100.0), 2) if base_cap > 0 else 0.0
    realized_pnl_usd = round(
        float(ledger_summary.get("realized_pnl_usd", (active_prin_sum + cash_usd) - base_cap)), 2
    ) if ledger_summary.get("ok") else round((active_prin_sum + cash_usd) - base_cap, 2)

    # Replay true day-by-day on-chain portfolio equity curve strictly from `invest_date` to `today_str`
    today_str = datetime.now().strftime("%Y-%m-%d")
    hist_dates = [d for d in dates if invest_date <= d <= today_str]
    if invest_date not in hist_dates:
        hist_dates.insert(0, invest_date)
    if today_str not in hist_dates:
        hist_dates.append(today_str)

    hist_values = []
    net_hist_values = []

    if ledger_summary.get("ok") and ledger_summary.get("session_vault_events") and snapshots:
        vault_evs = ledger_summary["session_vault_events"]
        fund_evs = ledger_summary.get("session_funding_events") or []
        init_cap = base_cap - sum(float(f.get("delta_usd", 0.0) or 0.0) for f in fund_evs)
        sim_cash = float(init_cap)
        sim_lots = []  # [{"vault", "amt", "entry_date", "ref_d", "last_gross"}]
        ev_idx = 0
        f_idx = 0

        for d in hist_dates:
            while f_idx < len(fund_evs) and fund_evs[f_idx]["date"] <= d:
                sim_cash += float(fund_evs[f_idx].get("delta_usd", 0.0) or 0.0)
                f_idx += 1
            while ev_idx < len(vault_evs) and vault_evs[ev_idx]["date"] <= d:
                ev = vault_evs[ev_idx]
                ev_idx += 1
                vaddr = ev["vault"]
                if ev["kind"] == "DEPOSIT":
                    amt_u = float(ev["usdc"])
                    sim_cash -= amt_u
                    ref_d = next(
                        (sd for sd in dates if sd >= ev["date"] and vaddr in snapshots[sd] and snapshots[sd][vaddr].get("alltime_pnl")),
                        None,
                    )
                    sim_lots.append({
                        "vault": vaddr,
                        "amt": amt_u,
                        "entry_date": ev["date"],
                        "ref_d": ref_d,
                        "last_gross": amt_u,
                    })
                elif ev["kind"] == "WITHDRAW":
                    sim_cash += float(ev["net_withdrawn_usd"])
                    rem_b = float(ev["basis_usd"])
                    for lt in sim_lots:
                        if lt["vault"] != vaddr or lt["amt"] <= 1e-6 or rem_b <= 1e-6:
                            continue
                        take = min(lt["amt"], rem_b)
                        ratio_left = max(0.0, (lt["amt"] - take) / lt["amt"]) if lt["amt"] > 0 else 0.0
                        lt["amt"] = max(0.0, lt["amt"] - take)
                        lt["last_gross"] = lt["last_gross"] * ratio_left
                        rem_b -= take
                    sim_lots = [lt for lt in sim_lots if lt["amt"] > 0.01]

            if d == invest_date and d != today_str:
                hist_values.append(round(base_cap, 2))
                net_hist_values.append(round(base_cap, 2))
            elif d == today_str:
                hist_values.append(total_val)
                net_hist_values.append(net_total_val)
            else:
                day_g = max(0.0, sim_cash)
                day_n = max(0.0, sim_cash)
                snap_d = snapshots.get(d, {})
                for lt in sim_lots:
                    ref_d = lt["ref_d"]
                    vaddr = lt["vault"]
                    amt_u = lt["amt"]
                    if ref_d and d >= ref_d and vaddr in snap_d and snap_d[vaddr].get("alltime_pnl"):
                        s0 = snapshots[ref_d][vaddr]
                        p_diff = float(snap_d[vaddr]["alltime_pnl"][-1]) - float(s0["alltime_pnl"][-1])
                        tvl0 = max(float(s0.get("tvl", 1.0) or 1.0), 1.0)
                        lt["last_gross"] = max(0.0, amt_u + p_diff * (amt_u / tvl0))
                    vg = lt["last_gross"]
                    gp = vg - amt_u
                    vn = amt_u + (gp * 0.90 if gp > 0 else gp)
                    day_g += vg
                    day_n += vn
                hist_values.append(round(day_g, 2))
                net_hist_values.append(round(day_n, 2))
    else:
        snap_hist = calc_portfolio_performance(
            {h["address"]: h["invested_usd"] for h in raw_holdings},
            invest_date,
            active_prin_sum,
            snapshots,
        )
        hist_dates = list(snap_hist.get("history_dates") or [])
        hist_values = [round(v + cash_usd + realized_pnl_usd, 2) for v in (snap_hist.get("history_values") or [])]
        net_hist_values = [round(v + cash_usd + realized_pnl_usd, 2) for v in (snap_hist.get("net_history_values") or [])]
        if not hist_dates:
            hist_dates = [invest_date, today_str] if invest_date != today_str else [today_str]
            hist_values = [base_cap, total_val] if len(hist_dates) == 2 else [total_val]
            net_hist_values = [base_cap, net_total_val] if len(hist_dates) == 2 else [net_total_val]
        else:
            if hist_dates[0] == invest_date:
                hist_values[0] = round(base_cap, 2)
                net_hist_values[0] = round(base_cap, 2)
            if hist_dates[-1] == today_str:
                hist_values[-1] = total_val
                net_hist_values[-1] = net_total_val
            else:
                hist_dates.append(today_str)
                hist_values.append(total_val)
                net_hist_values.append(net_total_val)

    monthly_returns = []
    if hist_dates and hist_values:
        ym_buckets = {}
        for d, vg, vn in zip(hist_dates, hist_values, net_hist_values):
            ym_buckets.setdefault(d[:7], []).append((d, vg, vn))
        prev_g = float(base_cap)
        prev_n = float(base_cap)
        for ym in sorted(ym_buckets.keys()):
            items = ym_buckets[ym]
            start_d = items[0][0]
            end_d, end_g, end_n = items[-1]
            r_g = ((end_g / prev_g) - 1.0) * 100.0 if prev_g > 0 else 0.0
            r_n = ((end_n / prev_n) - 1.0) * 100.0 if prev_n > 0 else 0.0
            monthly_returns.append({
                "month": ym,
                "short_label": f"{ym[2:4]}.{ym[5:7]}",
                "month_num": f"{int(ym[5:7])}월",
                "start_date": start_d,
                "end_date": end_d,
                "days": len(items),
                "start_net": round(prev_n, 2),
                "end_net": round(end_n, 2),
                "net_pnl": round(end_n - prev_n, 2),
                "net_pct": round(r_n, 2),
                "gross_pnl": round(end_g - prev_g, 2),
                "gross_pct": round(r_g, 2),
            })
            prev_g = end_g
            prev_n = end_n

    eff_days = max(1.0, days_held_exact)
    if eff_days < 7.0:
        avg_monthly_gross_pct = (total_pct / eff_days) * 30.4375
        avg_monthly_net_pct = (net_total_pct / eff_days) * 30.4375
    else:
        avg_monthly_gross_pct = ((1.0 + max(total_pct, -99.9999) / 100.0) ** (30.4375 / eff_days) - 1.0) * 100.0
        avg_monthly_net_pct = ((1.0 + max(net_total_pct, -99.9999) / 100.0) ** (30.4375 / eff_days) - 1.0) * 100.0

    mdd_val = 0.0
    if hist_values:
        eq_arr = np.array([base_cap] + hist_values, dtype=float)
        rm = np.maximum.accumulate(eq_arr)
        denom = np.where(rm > 0, rm, 1.0)
        dd = (rm - eq_arr) / denom * 100.0
        mdd_val = round(float(dd.max()), 2)

    rebalance_summary = None
    rebalance_history = []
    if ledger_summary.get("ok"):
        rebalance_history = ledger_summary.get("rebalance_history") or []
        rebalance_summary = {
            "rebalance_count": int(ledger_summary.get("rebalance_count", 0) or 0),
            "session_start_ts": ledger_summary.get("session_start_ts", invest_date),
            "last_rebalance_ts": ledger_summary.get("last_rebalance_ts"),
            "total_withdrawn_basis_usd": round(float(ledger_summary.get("total_withdrawn_basis_usd", 0.0) or 0.0), 2),
            "total_withdrawn_net_usd": round(float(ledger_summary.get("total_withdrawn_net_usd", 0.0) or 0.0), 2),
            "realized_pnl_usd": realized_pnl_usd,
            "realized_pnl_pct_on_exited": round(float(ledger_summary.get("realized_pnl_pct_on_exited", 0.0) or 0.0), 2),
            "realized_pnl_pct_on_capital": round((realized_pnl_usd / base_cap * 100.0) if base_cap > 0 else 0.0, 2),
            "active_unrealized_pnl_usd": active_unrealized_pnl,
            "active_unrealized_pnl_pct": round((active_unrealized_pnl / active_prin_sum * 100.0) if active_prin_sum > 0 else 0.0, 2),
            "total_commission_usd": round(float(ledger_summary.get("total_commission_usd", 0.0) or 0.0), 2),
        }

    out_res = {
        "is_live_onchain": True,
        "fetched_at": onchain.get("fetched_at"),
        "account_address": account_addr,
        "wallet_cash_usd": cash_usd,
        "active_principal_usd": active_prin_sum,
        "active_unrealized_pnl_usd": active_unrealized_pnl,
        "realized_pnl_usd": realized_pnl_usd,
        "rebalance_summary": rebalance_summary,
        "rebalance_history": rebalance_history,
        "total_invested": round(base_cap, 2),
        "total_value": total_val,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pct,
        "net_total_pnl": net_total_pnl,
        "net_total_pnl_pct": net_total_pct,
        "net_total_value": net_total_val,
        "avg_monthly_gross_pct": round(avg_monthly_gross_pct, 2),
        "avg_monthly_net_pct": round(avg_monthly_net_pct, 2),
        "monthly_returns": monthly_returns,
        "monthly_est": round(sum(h["monthly_est"] for h in raw_holdings), 2),
        "annual_est": round(sum(h["monthly_est"] for h in raw_holdings) * 12.0, 2),
        "holdings": raw_holdings,
        "n_vaults": len(raw_holdings),
        "invest_date": invest_date,
        "analysis_date": onchain.get("fetched_at", latest_dt),
        "days_held": days_held_int,
        "history_dates": hist_dates,
        "history_values": hist_values,
        "net_history_values": net_hist_values,
        "mdd": mdd_val,
    }
    with _LIVE_CACHE_LOCK:
        _LIVE_CACHE["ts"] = _time.time()
        _LIVE_CACHE["data"] = out_res
    return out_res


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
