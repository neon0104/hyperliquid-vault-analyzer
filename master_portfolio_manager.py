#!/usr/bin/env python3
"""
master_portfolio_manager.py — 👑 SGRA+ 리스크-확신도 가중 마스터 포트폴리오 엔진
===================================================================================
실증 검증 완료 아키텍처 (SGRA+ Risk-Conviction Weighted):
  - 하드 안전 필터: AllowDeposits & TVL >= $10k & 리더 지분율(Skin) >= 30% &
                    Robustness >= 0.20 & 14일 수익률 >= -5% (칼날방지) & 현재낙폭 <= 40%
  - 카디널 스코어링: 0.35 Robustness + 0.30 (CushionedSharpe/50) + 0.20 HealthyUnderval + 0.15 SkinRatio
  - 가중 배분: SGRA_Score / sqrt(0.5*MaxDD + 0.5*DD_now) 비례 가중평균 (단일 슬롯 <= 25%, 볼트 TVL <= 30% 상한)
  - 국면 연동: 확증 강세장(BULL) 시 유휴현금 14일 모멘텀 슬리브 가동 / 약세·횡보장 시 방어용 현금 예비금 유지
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hl_auto_vault_bot import DEFAULT_BOT_CONFIG, compute_sgra_signal, load_autobot_config
from io_utils import atomic_write_json

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "vault_data"
OUTPUT_JSON = DATA_DIR / "master_portfolio_recommendation.json"


def load_vault_pnl_timeseries():
    db_path = DATA_DIR / "pnl_history.db"
    vault_series = {}
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT vault_address, collected_at, alltime_pnl, tvl
                FROM daily_pnl
                ORDER BY collected_at ASC
                """
            )
            for addr, dt, pnl, tvl in cur.fetchall():
                a = str(addr or "").lower()
                if a not in vault_series:
                    vault_series[a] = []
                vault_series[a].append((dt, float(pnl or 0.0), float(tvl or 1.0)))
            conn.close()
        except Exception:
            pass
    return vault_series


def compute_hurst(ts):
    if len(ts) < 15:
        return 0.5
    ts = np.array(ts, dtype=float)
    diffs = np.diff(ts)
    if len(diffs) < 10:
        return 0.5
    lags = [l for l in (4, 8, 12, 16, 24) if l <= len(diffs)]
    if len(lags) < 2:
        return 0.5
    rs_vals = []
    for lag in lags:
        sub_diffs = diffs[-lag:]
        dev = sub_diffs - np.mean(sub_diffs)
        cum_dev = np.cumsum(dev)
        r = np.max(cum_dev) - np.min(cum_dev)
        s = np.std(sub_diffs) + 1e-9
        rs_vals.append(max(r / s, 1e-9))
    poly = np.polyfit(np.log(lags), np.log(rs_vals), 1)
    return float(np.clip(poly[0], 0.1, 0.9))


def compute_sortino(ts, tvl):
    diffs = np.diff(np.array(ts, dtype=float))
    if len(diffs) < 5 or tvl <= 0:
        return 0.0
    rets = np.clip(diffs / (tvl + 1e-9), -0.5, 0.5)
    mu = float(rets.mean())
    tdd = float(np.sqrt(np.mean(np.minimum(0.0, rets) ** 2)))
    vol_floor = max(float(rets.std()) * 0.25, 5e-4)
    down_dev = max(tdd, vol_floor)
    return float(np.clip((mu / down_dev) * np.sqrt(365), -20.0, 50.0))


def run_comprehensive_portfolio_management(total_capital=100000.0):
    cfg = dict(DEFAULT_BOT_CONFIG)
    cfg.update(load_autobot_config())
    signal = compute_sgra_signal(float(total_capital), set(), cfg)
    if "error" in signal:
        print(f"❌ SGRA+ 시그널 산출 오류: {signal['error']}")
        return {}

    date_str = signal.get("snapshot_date", datetime.now().strftime("%Y-%m-%d"))
    regime = signal.get("regime", "NEUTRAL")
    vault_series = load_vault_pnl_timeseries()

    print("=" * 80)
    print(f"👑 [AI Master Portfolio Manager — SGRA+ Weighted] 온체인 분석 가동 ({date_str} | 국면: {regime})")
    print("=" * 80)

    portfolio_plan = []
    for a in signal.get("allocations", []):
        addr = a["address"].lower()
        ser = vault_series.get(addr, [])
        pnl_arr = [x[1] for x in ser]
        tvl_val = float(a.get("tvl_usd", 1.0) or 1.0)
        hurst_val = compute_hurst(pnl_arr) if len(pnl_arr) >= 15 else 0.5
        sortino_val = compute_sortino(pnl_arr, tvl_val) if len(pnl_arr) >= 10 else float(a.get("cushioned_sharpe", 0.0))
        dd_now = float(a.get("drawdown_now_pct", 0.0))
        max_mdd = float(a.get("max_mdd_pct", 15.0))
        is_dip = (max_mdd >= 5.0 and dd_now >= 0.50 * max_mdd and float(a.get("ret_14d_pct", 0.0)) >= -5.0)
        is_core = "CORE" in str(a.get("sleeve", "CORE"))

        portfolio_plan.append({
            "role": "🛡️ CORE (우량·지지선 가중)" if is_core else "⚡ BULL ACCEL (14d 모멘텀)",
            "name": a["name"],
            "address": addr,
            "allocation_pct": round(float(a["target_weight_pct"]), 2),
            "allocated_usd": round(float(a["target_usd"]), 2),
            "apr_30d": round(float(a["apr_30d_pct"]), 2),
            "ret_14d_pct": round(float(a["ret_14d_pct"]), 2),
            "mdd": round(max_mdd, 2),
            "curr_dd": round(dd_now, 2),
            "sharpe": round(float(a["cushioned_sharpe"]), 2),
            "sortino": round(sortino_val, 2),
            "hurst": round(hurst_val, 3),
            "robustness": round(float(a["robustness"]), 3),
            "leader_ratio_pct": round(float(a["leader_ratio_pct"]), 1),
            "leader_usd": round(tvl_val * float(a["leader_ratio_pct"]) / 100.0, 2),
            "sgra_score": a["sgra_score"],
            "action_guide": (
                f"🎯 검증된 지지선 근접 가중 매수 (현재DD {dd_now:.1f}% / MaxMDD {max_mdd:.1f}%)"
                if is_dip
                else "✅ ±10% HWM 보존 밴드 복리 유지 (4h 비상손절 가드 감시)"
            ),
            "is_dip": is_dip,
        })

    cash_pct = float(signal.get("cash_reserve_pct", 0.0))
    cash_usd = float(signal.get("cash_reserve_usd", 0.0))
    weighted_apr = sum(p["apr_30d"] * (p["allocated_usd"] / total_capital) for p in portfolio_plan)
    weighted_mdd = sum(p["mdd"] * (p["allocated_usd"] / total_capital) for p in portfolio_plan)
    est_monthly_profit = total_capital * (weighted_apr / 100.0 / 12.0)
    est_annual_profit = total_capital * (weighted_apr / 100.0)

    result = {
        "analysis_date": date_str,
        "updated_at": datetime.now().isoformat(),
        "total_capital": total_capital,
        "regime": regime,
        "cash_reserve_pct": round(cash_pct, 2),
        "cash_reserve_usd": round(cash_usd, 2),
        "portfolio_summary": {
            "expected_apr": round(weighted_apr, 2),
            "portfolio_mdd_estimate": round(max(weighted_mdd * 0.55, 5.0), 2),
            "estimated_monthly_profit_usd": round(est_monthly_profit, 2),
            "estimated_annual_profit_usd": round(est_annual_profit, 2),
            "strategy_framework": (
                "SGRA+ Quality & Proven-Support Weighted (TVL>=$20k, MaxMDD<=40%, Skin>=5%, "
                "Collapse-Block, 30% TVL Cap, ±10% HWM Delta Band)"
            ),
        },
        "master_portfolio": portfolio_plan,
        "dip_buying_alerts": [p for p in portfolio_plan if p["is_dip"]],
    }

    atomic_write_json(str(OUTPUT_JSON), result, indent=2)

    print("\n🎯 [SGRA+ 종합 판단] 리스크-확신도 가중 최적 포트폴리오 산출 결과:")
    print("-" * 86)
    print(f"{'역할':<24} {'볼트명':<22} {'비중':<7} {'금액($)':<10} {'Skin%':<7} {'MDD':<6} {'Sharpe':<6}")
    print("-" * 86)
    for p in portfolio_plan:
        print(
            f"{p['role']:<22} {p['name'][:21]:<22} {p['allocation_pct']:>5.1f}%  "
            f"${p['allocated_usd']:>8,.0f}  {p['leader_ratio_pct']:>5.1f}%  {p['mdd']:>4.1f}% {p['sharpe']:>5.2f}"
        )
    if cash_pct > 0.5:
        print(f"{'💵 방어용 USD 예비금':<22} {'USDC Cash Reserve':<22} {cash_pct:>5.1f}%  ${cash_usd:>8,.0f}      -      0.0%  0.00")
    print("-" * 86)
    print(f"💾 최상 포트폴리오 저장 완료: {OUTPUT_JSON}")
    print("=" * 80)
    return result


if __name__ == "__main__":
    run_comprehensive_portfolio_management()
