#!/usr/bin/env python3
"""
autonomous_loop_engine.py — 🔄 자율 진화 루프 엔지니어링 퀀트 엔진 (Phase-Averaged & 10% HWM 검증)
====================================================================================================
핵심 기능:
  1. [자가 채점 루프] 어제 챔피언 추천 포트폴리오의 실제 24h 수익률 실측
  2. [공정 토너먼트 루프] SGRA+ 챔피언 포함 5대 퀀트 전략을 동일 무결 패널(2026-04-27~) 위에서
     볼트별 10% High-Water-Mark 성과보수 + 5bps 슬리피지 + 볼트 TVL 30% 상한 +
     14개 전 시작일 위상 평균(Phase-Averaged across all 14 offsets)으로 공정 검증
  3. [챔피언 자동 채택] 타이밍 운(Timing Luck)이 제거된 실증 Sharpe·Calmar 1위 모델 자동 승격
"""

import bisect
import json
import math
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hl_auto_vault_bot import EXCLUDED_ADDRESSES
from io_utils import atomic_write_json

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
EVAL_HIST_FILE = DATA_DIR / "loop_evaluation_history.json"
ACTIVE_STRAT_FILE = DATA_DIR / "active_quant_strategy.json"
LOOP_SUMMARY_FILE = DATA_DIR / "loop_engine_summary.json"


def load_json(filepath: Path, default=None):
    if not filepath.exists():
        return default if default is not None else {}
    try:
        return json.loads(filepath.read_text(encoding="utf-8"))
    except Exception:
        return default if default is not None else {}


def save_json(filepath: Path, data):
    atomic_write_json(str(filepath), data, indent=2)


def load_pit_db_series():
    db_path = DATA_DIR / "pnl_history.db"
    series = {}
    if not db_path.exists():
        return series
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT vault_address, collected_at, alltime_pnl FROM daily_pnl ORDER BY collected_at ASC")
        for addr, dt, pnl in cur.fetchall():
            a = str(addr or "").lower()
            if a not in series:
                series[a] = ([], [])
            series[a][0].append(dt)
            series[a][1].append(float(pnl or 0.0))
        conn.close()
    except Exception:
        pass
    return series


def load_all_snapshots():
    pit_series = load_pit_db_series()
    files = sorted([f for f in SNAPSHOTS_DIR.glob("*.json") if not f.name.endswith(".bak") and f.stem >= "2026-04-27"])
    cache = {}
    for f in files:
        try:
            date_str = f.stem
            snap_list = json.loads(f.read_text(encoding="utf-8"))
            if not isinstance(snap_list, list) or len(snap_list) < 20:
                continue
            for v in snap_list:
                addr = str(v.get("address", "")).lower()
                v["address"] = addr
                if addr in pit_series:
                    d_list, p_list = pit_series[addr]
                    idx = bisect.bisect_right(d_list, date_str)
                    if idx >= 8:
                        v["_pit_pnl"] = p_list[:idx]
            cache[date_str] = snap_list
        except Exception:
            pass
    return cache


def get_vault_metrics(v: dict):
    pnl_arr = v.get("alltime_pnl", [])
    pnl_val = float(pnl_arr[-1]) if (isinstance(pnl_arr, list) and len(pnl_arr) > 0) else float(v.get("pnl_alltime", 0.0) or 0.0)
    tvl_val = max(float(v.get("tvl", 1.0) or 1.0), 1.0)
    apr_30d = float(v.get("apr_30d", 0.0) or v.get("apr_pct", 0.0) or 0.0)
    sharpe = float(v.get("sharpe_ratio", 0.0) or 0.0)
    robustness = float(v.get("robustness_score", 0.0) or 0.0)
    l_usd = float(v.get("leader_equity_usd", 0.0) or v.get("leader_equity", 0.0) or 0.0)
    mdd = float(v.get("max_drawdown", 15.0) or 15.0)
    age = int(v.get("age_days", 30) or 30)
    return pnl_val, tvl_val, apr_30d, sharpe, robustness, l_usd, mdd, age


def _est_ret14(v: dict) -> float:
    pnl_arr = v.get("_pit_pnl") if len(v.get("_pit_pnl", [])) >= 15 else v.get("alltime_pnl", [])
    tvl = max(float(v.get("tvl", 1.0) or 1.0), 1.0)
    if isinstance(pnl_arr, list) and len(pnl_arr) >= 15:
        return float(np.clip((float(pnl_arr[-1]) - float(pnl_arr[-15])) / tvl, -0.5, 0.5))
    if isinstance(pnl_arr, list) and len(pnl_arr) >= 2:
        return float(np.clip((float(pnl_arr[-1]) - float(pnl_arr[0])) / tvl, -0.5, 0.5))
    return 0.0


class StrategySGRAPlusChampion:
    name = "SGRA+ Quality & Support Weighted (HWM Delta)"
    desc = "TVL>=$20k · MaxMDD<=40% · 리더지분>=5% + 신저점붕괴 차단 + 역사적 지지선·우량 가중배분"
    uses_hwm_delta = True

    @staticmethod
    def allocate(vaults: list, total_capital=100000.0, held_addrs=None) -> dict:
        held_norm = {a.lower() for a in (held_addrs or set())}
        cap_ref = max(float(total_capital), 50000.0)
        scored = []
        for v in vaults:
            addr = str(v.get("address", "")).lower()
            if not addr or addr in EXCLUDED_ADDRESSES or not bool(v.get("allow_deposits", True)):
                continue
            tvl = float(v.get("tvl", 0.0) or 0.0)
            skin = float(v.get("leader_equity_ratio", 0.0) or 0.0)
            rob = float(v.get("robustness_score", 0.0) or 0.0)
            dd_now = float(v.get("drawdown_now", 0.0) or 0.0)
            mdd = float(v.get("max_drawdown", 15.0) or 15.0)
            apr30 = float(v.get("apr_30d", 0.0) or 0.0)
            ret14 = _est_ret14(v)
            if tvl < 20000.0 or mdd > 40.0 or dd_now > 38.0 or skin < 0.05 or rob < 0.22 or ret14 < -0.05:
                continue
            if mdd < 2.2 and apr30 < 20.0 and ret14 < 0.015:
                continue
            if apr30 < -130.0:
                continue
            shp = float(np.clip(float(v.get("sharpe_ratio", 0.0) or 0.0), -20.0, 50.0))
            underval = float(np.clip(dd_now / max(mdd, 5.0), 0.0, 1.0))
            sc = rob * 0.30 + (shp / 50.0) * 0.20 + underval * 0.20 + min(skin / 0.40, 1.0) * 0.30
            vc = dict(v)
            vc["_sgra"] = sc
            vc["_eff_dd"] = max(0.5 * mdd + 0.5 * dd_now, 7.0)
            scored.append((sc, vc))

        scored.sort(key=lambda x: x[0], reverse=True)
        keep_set = {v["address"] for _, v in scored[:8]}
        sel = [v for _, v in scored if v["address"] in held_norm and v["address"] in keep_set][:6]
        sel_set = {v["address"] for v in sel}
        for _, v in scored:
            if len(sel) >= 6:
                break
            if v["address"] not in sel_set:
                sel.append(v)
                sel_set.add(v["address"])
        if not sel:
            return {}

        caps = np.array([min(0.25, (0.30 * float(v.get("tvl", 0.0) or 0.0)) / cap_ref) for v in sel], dtype=float)
        raw_w = np.array([max(v["_sgra"], 0.05) / math.sqrt(v["_eff_dd"]) for v in sel], dtype=float)
        w = raw_w / np.sum(raw_w) * min(1.0, float(np.sum(caps)))
        for _ in range(8):
            over = w > caps + 1e-9
            if not np.any(over):
                break
            ex = float(np.sum(w[over] - caps[over]))
            w[over] = caps[over]
            under = ~over
            if np.any(under) and np.sum(w[under]) > 0:
                w[under] += ex * (w[under] / np.sum(w[under]))
        return {v["address"]: float(wi) * total_capital for v, wi in zip(sel, w) if wi > 1e-4}


class StrategyBarbellSkinHeavy:
    name = "Barbell Skin-In-Game Heavy (60:40)"
    desc = "리더 달러 예치금(log USD) + 초저낙폭 Core 60% + 고수익 Satellite 40%"
    uses_hwm_delta = False

    @staticmethod
    def allocate(vaults: list, total_capital=100000.0, held_addrs=None) -> dict:
        scored = []
        for v in vaults:
            if not bool(v.get("allow_deposits", True)):
                continue
            _, tvl, apr_30d, sharpe, robustness, l_usd, mdd, _ = get_vault_metrics(v)
            if tvl < 10000.0 or apr_30d <= 0 or mdd > 35.0 or l_usd < 10000.0:
                continue
            sc = (np.log1p(l_usd) * 15.0) + (min(sharpe, 50.0) * 20.0) + (robustness * 40.0)
            scored.append((v, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        if not scored:
            return {}
        core_cands = [s for s in scored if float(s[0].get("max_drawdown", 15.0) or 15.0) <= 10.0]
        core = core_cands[:3] if len(core_cands) >= 3 else scored[:3]
        core_addrs = {v["address"] for v, _ in core}
        rem = [s for s in scored if s[0]["address"] not in core_addrs]
        sat = rem[:3] if rem else core
        alloc = {}
        for v, _ in core:
            cap_u = 0.30 * float(v.get("tvl", 0.0) or 0.0)
            alloc[v["address"]] = min(cap_u, alloc.get(v["address"], 0.0) + (total_capital * 0.60 / len(core)))
        for v, _ in sat:
            cap_u = 0.30 * float(v.get("tvl", 0.0) or 0.0)
            alloc[v["address"]] = min(cap_u, alloc.get(v["address"], 0.0) + (total_capital * 0.40 / len(sat)))
        return alloc


class StrategyFractionalKelly:
    name = "Fractional Kelly 0.3x Optimizer"
    desc = "승률과 손익비를 최적화한 0.3x 부분 켈리 비중 배분"
    uses_hwm_delta = False

    @staticmethod
    def allocate(vaults: list, total_capital=100000.0, held_addrs=None) -> dict:
        scored = []
        for v in vaults:
            if not bool(v.get("allow_deposits", True)):
                continue
            pnl_arr = v.get("_pit_pnl") if len(v.get("_pit_pnl", [])) >= 10 else v.get("alltime_pnl", [])
            _, tvl, apr_30d, _, rob, l_usd, mdd, _ = get_vault_metrics(v)
            if tvl < 10000.0 or len(pnl_arr) < 10 or apr_30d <= 0 or mdd > 30.0:
                continue
            diffs = np.diff(np.array(pnl_arr, dtype=float))
            win_w = diffs[-30:] if len(diffs) >= 30 else diffs
            if float(np.sum(win_w)) <= 0:
                continue
            wins = win_w[win_w > 0]
            losses = np.abs(win_w[win_w < 0])
            p = len(wins) / (len(win_w) + 1e-9)
            avg_w = float(np.mean(wins)) if len(wins) else 1.0
            avg_l = float(np.mean(losses)) if len(losses) else max(avg_w * 0.5, 1e-6)
            b = float(np.clip(avg_w / (avg_l + 1e-9), 0.1, 10.0))
            f_k = float(np.clip(((p * b - (1.0 - p)) / b) * 0.3, 0.0, 0.30))
            sc = f_k * (1.0 + np.log1p(l_usd) * 0.1) * (rob + 0.5)
            if sc > 0:
                scored.append((v, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:5]
        if not top:
            return {}
        tot_s = sum(s for _, s in top) + 1e-9
        return {v["address"]: min(0.30 * float(v.get("tvl", 0.0) or 0.0), (s / tot_s) * total_capital) for v, s in top}


class StrategyDynamicRegimeMomentum:
    name = "Dynamic Dual Momentum + Volatility Filter"
    desc = "단기 7일 가속도와 중기 30일 APR 모멘텀 추격 + 변동성 역가중"
    uses_hwm_delta = False

    @staticmethod
    def allocate(vaults: list, total_capital=100000.0, held_addrs=None) -> dict:
        scored = []
        for v in vaults:
            if not bool(v.get("allow_deposits", True)):
                continue
            _, tvl, apr_30d, sharpe, _, _, mdd, _ = get_vault_metrics(v)
            pnl_arr = v.get("_pit_pnl") if len(v.get("_pit_pnl", [])) >= 8 else v.get("alltime_pnl", [])
            if tvl < 10000.0 or len(pnl_arr) < 8 or apr_30d <= 0 or mdd > 25.0:
                continue
            mom_7d = ((pnl_arr[-1] - pnl_arr[-8]) / tvl) * 52.0 * 100.0
            sc = (apr_30d * 0.4) + (mom_7d * 0.4) + (min(sharpe, 50.0) * 10.0) - (mdd * 2.0)
            if sc > 0:
                scored.append((v, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:4]
        if not top:
            return {}
        inv = [1.0 / max(float(v.get("max_drawdown", 10.0) or 10.0), 1.0) for v, _ in top]
        tot_i = sum(inv) + 1e-9
        return {v["address"]: min(0.30 * float(v.get("tvl", 0.0) or 0.0), (w / tot_i) * total_capital) for (v, _), w in zip(top, inv)}


class StrategyMeanReversionDipBuyer:
    name = "Mean-Reversion Dip-Buyer Alpha"
    desc = "우량 볼트의 일시적 -1%~-22% 낙폭 구간 역발상 매수"
    uses_hwm_delta = False

    @staticmethod
    def allocate(vaults: list, total_capital=100000.0, held_addrs=None) -> dict:
        scored = []
        for v in vaults:
            if not bool(v.get("allow_deposits", True)):
                continue
            pnl_val, tvl, _, sharpe, rob, l_usd, mdd, _ = get_vault_metrics(v)
            dd_now = float(v.get("drawdown_now", 0.0) or 0.0)
            if tvl < 10000.0 or rob < 0.25 or mdd > 30.0 or pnl_val <= 0 or not (1.0 <= dd_now <= 22.0):
                continue
            sc = (rob * 35.0) + (min(sharpe, 50.0) * 15.0) + (min(dd_now / 20.0, 1.0) * 55.0) + (np.log1p(l_usd) * 10.0)
            scored.append((v, sc))
        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:4]
        if not top:
            return {}
        return {v["address"]: min(0.30 * float(v.get("tvl", 0.0) or 0.0), total_capital / len(top)) for v, _ in top}


ALL_STRATEGIES = [
    StrategySGRAPlusChampion,
    StrategyBarbellSkinHeavy,
    StrategyFractionalKelly,
    StrategyDynamicRegimeMomentum,
    StrategyMeanReversionDipBuyer,
]


def _simulate_single_offset(strat_cls, dates, snapshots_cache, start_idx, offset, initial_cap, rebalance_interval):
    cash = initial_cap
    holdings = {}  # addr -> {net, hwm}
    daily_returns = []
    values = [initial_cap]
    band = 0.10 if getattr(strat_cls, "uses_hwm_delta", False) else 0.0

    prev_pnl = {}
    for step, idx in enumerate(range(start_idx, len(dates))):
        snap = snapshots_cache[dates[idx]]
        cur_pnl = {}
        for v in snap:
            p = v.get("alltime_pnl", [])
            pv = float(p[-1]) if (isinstance(p, list) and p) else float(v.get("pnl_alltime", 0.0) or 0.0)
            cur_pnl[v["address"]] = (pv, max(float(v.get("tvl", 1.0) or 1.0), 1.0))

        if step > 0:
            prev_tot = cash + sum(h["net"] for h in holdings.values())
            for addr, h in list(holdings.items()):
                if addr in cur_pnl and addr in prev_pnl and prev_pnl[addr][1] >= 5000.0:
                    r = float(np.clip((cur_pnl[addr][0] - prev_pnl[addr][0]) / prev_pnl[addr][1], -0.35, 0.35))
                else:
                    r = 0.0
                gross = h["net"] * (1.0 + r)
                fee = 0.10 * (gross - h["hwm"]) if gross > h["hwm"] else 0.0
                h["net"] = gross - fee
                h["hwm"] = max(h["hwm"], gross) - fee
            cur_tot = cash + sum(h["net"] for h in holdings.values())
            daily_returns.append((cur_tot - prev_tot) / max(prev_tot, 1e-9))
            values.append(cur_tot)

        if step == 0 or (step % rebalance_interval == offset % rebalance_interval):
            port_tot = cash + sum(h["net"] for h in holdings.values())
            target_alloc = strat_cls.allocate(snap, total_capital=port_tot, held_addrs=set(holdings.keys()))

            for addr in list(holdings.keys()):
                tgt_u = target_alloc.get(addr, 0.0)
                cur_u = holdings[addr]["net"]
                if tgt_u <= 1.0:
                    pos = holdings.pop(addr)
                    cash += pos["net"] * (1.0 - 0.0005)
                elif cur_u > tgt_u * (1.0 + band) and (cur_u - tgt_u) >= 50.0:
                    trim = cur_u - tgt_u
                    frac = trim / cur_u
                    holdings[addr]["net"] -= trim
                    holdings[addr]["hwm"] *= (1.0 - frac)
                    cash += trim * (1.0 - 0.0005)

            buys = []
            for addr, tgt_u in target_alloc.items():
                cur_u = holdings[addr]["net"] if addr in holdings else 0.0
                if tgt_u > cur_u * (1.0 + band) and (tgt_u - cur_u) >= 50.0:
                    buys.append((addr, tgt_u - cur_u))
            tot_b = sum(x[1] for x in buys)
            sc = min(1.0, cash / (tot_b * 1.0005)) if tot_b > 0 else 0.0
            for addr, diff in buys:
                amt = diff * sc
                if amt < 50.0:
                    continue
                cash -= amt * 1.0005
                if addr in holdings:
                    holdings[addr]["net"] += amt
                    holdings[addr]["hwm"] += amt
                else:
                    holdings[addr] = {"net": amt, "hwm": amt}

        prev_pnl = cur_pnl

    final_cap = cash + sum(h["net"] for h in holdings.values())
    tot_ret = ((final_cap - initial_cap) / initial_cap) * 100.0
    days = max(len(values) - 1, 1)
    cagr = ((final_cap / initial_cap) ** (365.0 / days) - 1.0) * 100.0 if final_cap > 0 else -100.0
    arr = np.array(daily_returns, dtype=float)
    if len(arr) >= 2 and arr.std() > 1e-12:
        mu, sd = float(arr.mean()), float(arr.std())
        sharpe = float((mu / sd) * np.sqrt(365))
        tdd = float(np.sqrt(np.mean(np.minimum(0.0, arr) ** 2)))
        sortino = float(np.clip((mu / max(tdd, sd * 0.25, 1e-4)) * np.sqrt(365), -20.0, 50.0))
    else:
        sharpe, sortino = 0.0, 0.0
    pv = np.array(values, dtype=float)
    pk = np.maximum.accumulate(pv)
    mdd = float(np.max((pk - pv) / pk)) * 100.0 if len(pv) else 0.0
    return tot_ret, cagr, sharpe, sortino, mdd, final_cap


def run_strategy_backtest(strat_cls, snapshots_cache: dict, initial_cap=100000.0, rebalance_interval=14):
    dates = sorted(snapshots_cache.keys())
    if len(dates) < 35:
        return {"strategy_name": strat_cls.name, "description": strat_cls.desc, "total_return_pct": 0.0, "cagr_pct": 0.0, "sharpe_ratio": 0.0, "sortino_ratio": 0.0, "max_drawdown_pct": 0.0, "calmar_ratio": 0.0, "final_capital": initial_cap}

    start_idx = 30
    res_list = [
        _simulate_single_offset(strat_cls, dates, snapshots_cache, start_idx, off, initial_cap, rebalance_interval)
        for off in range(rebalance_interval)
    ]
    rets = [r[0] for r in res_list]
    mean_ret = float(np.mean(rets))
    mean_cagr = float(np.mean([r[1] for r in res_list]))
    mean_sharpe = float(np.mean([r[2] for r in res_list]))
    mean_sortino = float(np.mean([r[3] for r in res_list]))
    mean_mdd = float(np.mean([r[4] for r in res_list]))
    mean_cap = float(np.mean([r[5] for r in res_list]))
    calmar = float(mean_cagr / max(mean_mdd, 1.0))

    return {
        "strategy_name": strat_cls.name,
        "description": strat_cls.desc,
        "total_return_pct": round(mean_ret, 2),
        "phase_min_return_pct": round(float(np.min(rets)), 2),
        "phase_max_return_pct": round(float(np.max(rets)), 2),
        "positive_offsets": f"{sum(1 for x in rets if x > 0)}/{rebalance_interval}",
        "cagr_pct": round(mean_cagr, 2),
        "sharpe_ratio": round(mean_sharpe, 2),
        "sortino_ratio": round(mean_sortino, 2),
        "max_drawdown_pct": round(mean_mdd, 2),
        "calmar_ratio": round(calmar, 2),
        "final_capital": round(mean_cap, 2),
    }


def run_self_evaluation(snapshots_cache: dict):
    dates = sorted(snapshots_cache.keys())
    if len(dates) < 2:
        return {"status": "insufficient_data"}
    today_str, yesterday_str = dates[-1], dates[-2]
    today_map = {v["address"]: v for v in snapshots_cache[today_str]}
    yest_map = {v["address"]: v for v in snapshots_cache[yesterday_str]}

    sample = StrategySGRAPlusChampion.allocate(snapshots_cache[yesterday_str], total_capital=100000.0)
    total_gain = 0.0
    items = []
    for addr, alloc_usd in sample.items():
        vt, vy = today_map.get(addr), yest_map.get(addr)
        if vt and vy:
            pt = float(vt.get("alltime_pnl", [0])[-1] if vt.get("alltime_pnl") else 0.0)
            py = float(vy.get("alltime_pnl", [0])[-1] if vy.get("alltime_pnl") else 0.0)
            tvl = max(float(vy.get("tvl", 1.0) or 1.0), 1.0)
            ret = float(np.clip((pt - py) / tvl, -0.35, 0.35))
            prof = alloc_usd * ret
            total_gain += prof
            items.append({
                "vault_name": vt.get("name", addr[:10]),
                "address": addr,
                "allocated_usd": round(alloc_usd, 2),
                "actual_24h_gain_usd": round(prof, 2),
                "actual_24h_return_pct": round(ret * 100.0, 4),
            })

    eval_record = {
        "evaluated_date": today_str,
        "referenced_date": yesterday_str,
        "portfolio_24h_profit_usd": round(total_gain, 2),
        "portfolio_24h_return_pct": round((total_gain / 100000.0) * 100.0, 4),
        "evaluated_holdings": items,
    }
    hist = [h for h in load_json(EVAL_HIST_FILE, default=[]) if h.get("evaluated_date") != today_str]
    hist.append(eval_record)
    save_json(EVAL_HIST_FILE, hist[-60:])
    return eval_record


def run_autonomous_loop():
    print("=" * 72)
    print("🔄 [Hyperliquid Autonomous Loop] 10% HWM & 14-Offset 전위상 공정 토너먼트")
    print("=" * 72)
    snapshots_cache = load_all_snapshots()
    dates = sorted(snapshots_cache.keys())
    print(f"  📂 무결 연속 스냅샷: 총 {len(dates)}일치 ({dates[0]} ~ {dates[-1]})")

    eval_result = run_self_evaluation(snapshots_cache)
    if "portfolio_24h_return_pct" in eval_result:
        print(f"  ✅ 어제 SGRA+ 포트폴리오 24h 실현 수익률: {eval_result['portfolio_24h_return_pct']:+.2f}% (${eval_result['portfolio_24h_profit_usd']:+,.2f})")

    print("\n🏆 [Step 2/4] 5대 퀀트 전략 공정 백테스팅 (10% HWM + 5bps + 30% TVL캡 + 14개 전오프셋 평균)...")
    tournament_results = []
    for strat in ALL_STRATEGIES:
        res = run_strategy_backtest(strat, snapshots_cache)
        tournament_results.append((strat, res))
        print(
            f"  • {res['strategy_name']:<44} | 평균순수익: {res['total_return_pct']:>+6.2f}% "
            f"({res['positive_offsets']} 흑자) | Sharpe: {res['sharpe_ratio']:>5.2f} | MDD: {res['max_drawdown_pct']:>5.2f}%"
        )

    tournament_results.sort(
        key=lambda x: (x[1]["sharpe_ratio"] * 0.65 + min(x[1]["calmar_ratio"], 10.0) * 0.35),
        reverse=True,
    )
    champion_strat, champion_metrics = tournament_results[0]
    print(f"\n🥇 토너먼트 최종 챔피언: {champion_metrics['strategy_name']} (순수익 {champion_metrics['total_return_pct']:+.2f}%, Sharpe {champion_metrics['sharpe_ratio']})")

    today_snap = snapshots_cache[dates[-1]]
    champion_alloc = champion_strat.allocate(today_snap, total_capital=100000.0)
    today_vault_dict = {v["address"]: v for v in today_snap}
    recommended_portfolio = []
    for addr, usd in sorted(champion_alloc.items(), key=lambda x: x[1], reverse=True):
        v = today_vault_dict.get(addr, {})
        recommended_portfolio.append({
            "name": v.get("name", addr[:10]),
            "address": addr,
            "allocation_pct": round((usd / 100000.0) * 100.0, 2),
            "allocation_usd": round(usd, 2),
            "apr_30d": round(float(v.get("apr_30d", 0.0) or 0.0), 2),
            "mdd": round(float(v.get("max_drawdown", 0.0) or 0.0), 2),
            "sharpe_ratio": round(float(v.get("sharpe_ratio", 0.0) or 0.0), 2),
            "leader_equity_usd": round(float(v.get("leader_equity_usd", 0.0) or 0.0), 2),
        })

    save_json(ACTIVE_STRAT_FILE, {
        "updated_at": datetime.now().isoformat(),
        "champion_strategy": champion_metrics,
        "tournament_rankings": [t[1] for t in tournament_results],
    })
    save_json(LOOP_SUMMARY_FILE, {
        "timestamp": datetime.now().isoformat(),
        "latest_data_date": dates[-1],
        "self_evaluation_24h": eval_result,
        "champion_model": champion_metrics,
        "recommended_portfolio": recommended_portfolio,
        "all_tournament_results": [t[1] for t in tournament_results],
    })
    print(f"💾 결과 저장 완료: {LOOP_SUMMARY_FILE}")


if __name__ == "__main__":
    run_autonomous_loop()
