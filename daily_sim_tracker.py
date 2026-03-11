#!/usr/bin/env python3
"""
daily_sim_tracker.py — 일별 추천 포트폴리오 시뮬레이션 추적기
=============================================================
목적:
  "내가 X일에 추천 포트폴리오를 담았다면 지금 수익이 어떻게 됐을까?"
  매일 추천 목록을 기록하고, 실제 alltime_pnl 변화로 수익을 시뮬레이션.

작동 방식:
  1. 매일 analyze_top_vaults.py 실행 → 스냅샷 저장
  2. 이 스크립트가 해당 날짜의 추천 포트폴리오를 기록
  3. 이후 날마다 실제 pnl 데이터로 각 포트폴리오의 가치 변화 계산
  4. 결과를 vault_data/daily_sim.json 에 저장
  5. 대시보드에서 시각화

사용법:
  python daily_sim_tracker.py --update   # 오늘 포트폴리오 기록 + 모든 시뮬 업데이트
  python daily_sim_tracker.py --report   # 현재 시뮬레이션 결과 출력
  python daily_sim_tracker.py --both     # 둘 다
"""

import sys, os, json, argparse
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR      = "vault_data"
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
SIM_FILE      = os.path.join(DATA_DIR, "daily_sim.json")
CAPITAL       = 100_000.0   # 시뮬레이션 기준 투자금

# ── 데이터 로드/저장 ──────────────────────────────────────────────────────────
def load_sim() -> dict:
    """vault_data/daily_sim.json 로드"""
    if not os.path.exists(SIM_FILE):
        return {"portfolios": {}, "updated_at": ""}
    try:
        with open(SIM_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"portfolios": {}, "updated_at": ""}


def save_sim(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    data["updated_at"] = datetime.now().isoformat()
    with open(SIM_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=float)
    print(f"  >> 시뮬레이션 저장: {os.path.abspath(SIM_FILE)}")


def load_snapshot(date_str: str) -> list:
    p = os.path.join(SNAPSHOTS_DIR, f"{date_str}.json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sorted_snapshot_dates() -> list:
    """날짜 오름차순으로 스냅샷 날짜 목록 반환"""
    return sorted(p.stem for p in Path(SNAPSHOTS_DIR).glob("*.json"))


# ── 볼트의 특정 기간 수익률 계산 ─────────────────────────────────────────────
def get_vault_return(addr: str, from_date: str, to_date: str, snapshots_cache: dict) -> float:
    """
    주소(addr) 볼트의 from_date ~ to_date 기간 수익률(소수) 반환.
    alltime_pnl 데이터를 이용해 두 스냅샷 간 PnL 변화 비율로 계산.
    """
    snap_to = snapshots_cache.get(to_date)
    if not snap_to:
        return 0.0

    # to_date 스냅샷에서 해당 볼트 찾기
    vault_to = next((v for v in snap_to if v.get("address") == addr), None)
    if not vault_to:
        return 0.0

    pnl_to = vault_to.get("alltime_pnl", [])
    tvl    = float(vault_to.get("tvl", 1) or 1)

    # from_date 스냅샷에서 해당 볼트 찾기
    snap_from = snapshots_cache.get(from_date)
    vault_from = None
    if snap_from:
        vault_from = next((v for v in snap_from if v.get("address") == addr), None)

    if not pnl_to or len(pnl_to) < 2:
        return 0.0

    # from_date 없거나 pnl 비교 불가능한 경우 → 최근 2 포인트 비율 사용
    if not vault_from:
        # 마지막 pnl 변화로 추정
        delta = pnl_to[-1] - pnl_to[-2] if len(pnl_to) >= 2 else 0
        return float(np.clip(delta / (tvl + abs(pnl_to[-2]) + 1e-9), -0.3, 0.3))

    pnl_from = vault_from.get("alltime_pnl", [])

    # 두 스냅샷의 마지막 pnl 값 비교
    if not pnl_from:
        return 0.0

    val_to   = float(pnl_to[-1])
    val_from = float(pnl_from[-1])
    delta    = val_to - val_from
    denom    = tvl + abs(val_from) + 1e-9
    return float(np.clip(delta / denom, -0.3, 0.3))


# ── 오늘의 추천 포트폴리오 기록 ──────────────────────────────────────────────
def record_today_portfolio(date_str: str, sim_data: dict) -> bool:
    """
    오늘 스냅샷에서 추천 포트폴리오를 계산해 sim_data에 기록.
    이미 오늘 기록이 있으면 스킵.
    """
    if date_str in sim_data["portfolios"]:
        print(f"  [Tracker] {date_str} 이미 기록됨 (스킵)")
        return False

    snap = load_snapshot(date_str)
    if not snap:
        print(f"  [Tracker] {date_str} 스냅샷 없음 (스킵)")
        return False

    # 기존 추천 로직
    try:
        from analyze_top_vaults import get_recommendations
        recs = get_recommendations(snap, top_k=10)
    except Exception as e:
        print(f"  [Tracker] 추천 로직 오류: {e}")
        return False

    # 스마트 전략 추천도 병행
    try:
        from smart_scorer import compute_smart_scores, get_smart_recommendations
        snap_scored = compute_smart_scores([dict(v) for v in snap])
        smart_recs  = get_smart_recommendations(snap_scored, top_k=10)
    except Exception as e:
        print(f"  [Tracker] 스마트 스코어 오류: {e}")
        smart_recs = []

    def vault_to_record(v, alloc_key="suggested_allocation"):
        return {
            "address":      v.get("address", ""),
            "name":         v.get("name", "")[:30],
            "allocation":   v.get(alloc_key, 10.0),
            "apr_30d":      v.get("apr_30d", 0),
            "sharpe":       v.get("sharpe_ratio", 0),
            "robustness":   v.get("robustness_score", 0),
            "longterm_sharpe": v.get("longterm_sharpe", 0),
            "undervalue":   v.get("undervalue_score", 0),
            "smart_score":  v.get("smart_score", 0),
        }

    sim_data["portfolios"][date_str] = {
        "date":    date_str,
        "capital": CAPITAL,
        # 기존 APR 기반 추천
        "apr_strategy": {
            "vaults":   [vault_to_record(v) for v in recs],
            "history":  {date_str: CAPITAL},   # 날짜별 포트폴리오 가치
        },
        # 스마트 평균회귀 기반 추천
        "smart_strategy": {
            "vaults":   [vault_to_record(v, "smart_allocation") for v in smart_recs],
            "history":  {date_str: CAPITAL},
        },
    }
    print(f"  [Tracker] {date_str} 포트폴리오 기록: APR전략 {len(recs)}개, 스마트전략 {len(smart_recs)}개")
    return True


# ── 모든 시뮬레이션 업데이트 ─────────────────────────────────────────────────
def update_all_simulations(sim_data: dict):
    """
    기록된 모든 날짜의 포트폴리오에 대해 이후 날짜까지 가치 변화 시뮬레이션.
    """
    dates = sorted_snapshot_dates()
    if not dates:
        print("  [Tracker] 스냅샷 없음")
        return

    # 스냅샷 캐시 (메모리 절약: 필요할 때만 로드)
    snap_cache = {}
    for d in dates:
        snap_cache[d] = load_snapshot(d)

    for entry_date, pf_data in sim_data["portfolios"].items():
        # entry_date 이후의 날짜들에 대해 계산
        later_dates = [d for d in dates if d > entry_date]

        for strategy_key in ["apr_strategy", "smart_strategy"]:
            strategy = pf_data.get(strategy_key, {})
            vaults   = strategy.get("vaults", [])
            history  = strategy.get("history", {entry_date: CAPITAL})

            if not vaults:
                continue

            # 직전 날짜의 포트폴리오 가치에서 시작
            sorted_hist = sorted(history.keys())
            prev_date   = sorted_hist[-1]
            prev_value  = history[prev_date]

            for curr_date in later_dates:
                if curr_date in history:
                    # 이미 계산된 날짜 → prev 업데이트 후 스킵
                    prev_date  = curr_date
                    prev_value = history[curr_date]
                    continue

                # 각 볼트의 수익률 계산
                portfolio_return = 0.0
                total_alloc = sum(v.get("allocation", 0) for v in vaults) or 100.0

                for v in vaults:
                    addr  = v.get("address", "")
                    alloc = v.get("allocation", 0) / total_alloc  # 0~1
                    r     = get_vault_return(addr, prev_date, curr_date, snap_cache)
                    portfolio_return += alloc * r

                new_value = prev_value * (1 + portfolio_return)
                history[curr_date] = round(float(new_value), 2)
                prev_date  = curr_date
                prev_value = new_value

            strategy["history"] = history
            # 최종 성과 계산
            if len(history) >= 2:
                dates_sorted = sorted(history.keys())
                first_val = history[dates_sorted[0]]
                last_val  = history[dates_sorted[-1]]
                n_days    = len(dates_sorted) - 1
                strategy["total_return_pct"] = round((last_val / first_val - 1) * 100, 2)
                strategy["current_value"]    = round(last_val, 2)
                strategy["profit"]           = round(last_val - first_val, 2)
                strategy["days_held"]        = n_days
                # Max Drawdown
                vals = [history[d] for d in dates_sorted]
                peak = np.maximum.accumulate(vals)
                dd   = (np.array(peak) - np.array(vals)) / np.array(peak) * 100
                strategy["max_drawdown_pct"] = round(float(dd.max()), 2)

    print(f"  [Tracker] {len(sim_data['portfolios'])}개 포트폴리오 시뮬레이션 완료")


# ── 리포트 출력 ───────────────────────────────────────────────────────────────
def print_report(sim_data: dict):
    portfolios = sim_data.get("portfolios", {})
    if not portfolios:
        print("시뮬레이션 데이터 없음. --update 를 먼저 실행하세요.")
        return

    print("=" * 80)
    print(f"  일별 포트폴리오 시뮬레이션 리포트")
    print(f"  기준 투자금: ${CAPITAL:,.0f}")
    print("=" * 80)
    print(f"  {'날짜':<12} {'전략':<10} {'현재가치':>12} {'수익금':>12} {'수익률':>8} {'최대손실':>9} {'기간':>6}")
    print("  " + "-" * 74)

    for entry_date in sorted(portfolios.keys()):
        pf = portfolios[entry_date]
        for s_key, s_label in [("apr_strategy", "APR기반"), ("smart_strategy", "스마트")]:
            st = pf.get(s_key, {})
            if not st.get("current_value"):
                continue
            cv   = st["current_value"]
            prof = st.get("profit", 0)
            ret  = st.get("total_return_pct", 0)
            mdd  = st.get("max_drawdown_pct", 0)
            days = st.get("days_held", 0)
            color = "+" if prof >= 0 else ""
            print(f"  {entry_date:<12} {s_label:<10} ${cv:>10,.0f} {color}${prof:>10,.0f} {color}{ret:>6.1f}% {mdd:>7.1f}%  {days:>4}일")

    print()
    print("  [스마트 전략이 APR 기반보다 우수한 날짜:]")
    for entry_date in sorted(portfolios.keys()):
        pf = portfolios[entry_date]
        apr_ret   = pf.get("apr_strategy",   {}).get("total_return_pct", 0)
        smart_ret = pf.get("smart_strategy",  {}).get("total_return_pct", 0)
        if smart_ret > apr_ret + 0.1:
            diff = smart_ret - apr_ret
            print(f"    {entry_date}: 스마트 {smart_ret:+.1f}% vs APR {apr_ret:+.1f}%  (차이 {diff:+.1f}%p)")


def get_sim_summary_for_dashboard(sim_data: dict) -> list:
    """
    대시보드용 요약 데이터 반환.
    반환: [{date, apr_current, smart_current, apr_profit, smart_profit, ...}, ...]
    """
    result = []
    for entry_date, pf in sim_data.get("portfolios", {}).items():
        apr_st   = pf.get("apr_strategy",   {})
        smart_st = pf.get("smart_strategy", {})

        # 공통 날짜의 equity curve
        apr_hist   = apr_st.get("history",   {})
        smart_hist = smart_st.get("history", {})
        all_dates  = sorted(set(apr_hist) | set(smart_hist))

        row = {
            "entry_date":         entry_date,
            "capital":            pf.get("capital", CAPITAL),
            "apr_vaults":         len(apr_st.get("vaults", [])),
            "smart_vaults":       len(smart_st.get("vaults", [])),
            "apr_current":        apr_st.get("current_value", CAPITAL),
            "smart_current":      smart_st.get("current_value", CAPITAL),
            "apr_profit":         apr_st.get("profit", 0),
            "smart_profit":       smart_st.get("profit", 0),
            "apr_return_pct":     apr_st.get("total_return_pct", 0),
            "smart_return_pct":   smart_st.get("total_return_pct", 0),
            "apr_mdd":            apr_st.get("max_drawdown_pct", 0),
            "smart_mdd":          smart_st.get("max_drawdown_pct", 0),
            "days_held":          apr_st.get("days_held", 0),
            # equity curve (날짜별)
            "dates":              all_dates,
            "apr_equity":         [apr_hist.get(d, CAPITAL)   for d in all_dates],
            "smart_equity":       [smart_hist.get(d, CAPITAL) for d in all_dates],
        }
        result.append(row)
    return sorted(result, key=lambda x: x["entry_date"])


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="일별 포트폴리오 시뮬레이션 추적기")
    parser.add_argument("--update", action="store_true", help="오늘 포트폴리오 기록 + 시뮬 업데이트")
    parser.add_argument("--report", action="store_true", help="시뮬레이션 결과 출력")
    parser.add_argument("--both",   action="store_true", help="update + report")
    parser.add_argument("--date",   default=None, help="기록할 날짜 (기본: 오늘)")
    args = parser.parse_args()

    if not (args.update or args.report or args.both):
        parser.print_help()
        return

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    sim_data = load_sim()

    if args.update or args.both:
        print(f"\n[1/2] 오늘({date_str}) 포트폴리오 기록...")
        record_today_portfolio(date_str, sim_data)

        print("\n[2/2] 모든 시뮬레이션 업데이트...")
        update_all_simulations(sim_data)
        save_sim(sim_data)

    if args.report or args.both:
        print()
        print_report(sim_data)


if __name__ == "__main__":
    main()
