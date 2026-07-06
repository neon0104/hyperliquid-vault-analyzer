#!/usr/bin/env python3
"""
rebalance_engine.py — 30일 리밸런싱 엔진
==========================================
현재 포트폴리오와 최적 포트폴리오를 비교하여
구체적인 USD 금액 기반 리밸런싱 계획을 생성합니다.

실행:
  python rebalance_engine.py           # 리밸런싱 분석 + 플랜 생성
  python rebalance_engine.py --dry-run # 분석만 (파일 저장 없음)
  python rebalance_engine.py --force   # 30일 주기 무시, 강제 재실행

사용 방법:
  from rebalance_engine import run_rebalance_analysis, load_rebalance_plan
"""

import os
import sys
import json
import glob
import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "vault_data"
SNAPSHOTS_DIR   = DATA_DIR / "snapshots"
PORTFOLIO_FILE = BASE_DIR / "my_portfolio.json"
STATUS_FILE     = DATA_DIR / "status.json"
REBALANCE_FILE  = DATA_DIR / "rebalance_plan.json"   # ★ 메인 출력

REBALANCE_DAYS  = 30   # 기본 리밸런싱 주기 (일)
MAX_REBALANCE_DAYS = 60 # 시간 가드레일 (일)
MIN_DRIFT_PCT   = 5.0  # 개별 자산 비중 드리프트 임계값 (%)
DANGER_MDD      = 15.0 # 위험 MDD 기준 (%)
DANGER_APR      = 0.0  # 위험 APR 기준 (%)


# ── 유틸 ─────────────────────────────────────────────────────────────────────
def _sf(x, d=0.0):
    try:
        return float(x) if x is not None else d
    except (TypeError, ValueError):
        return d


def load_latest_snapshot():
    """최신 볼트 스냅샷 로드"""
    paths = sorted(SNAPSHOTS_DIR.glob("*.json"), reverse=True)
    if not paths:
        return None, None
    try:
        with open(paths[0], encoding="utf-8") as f:
            return json.load(f), paths[0].stem
    except Exception as e:
        print(f"  [RE] 스냅샷 로드 오류: {e}")
        return None, None


def load_my_portfolio():
    """내 현재 포트폴리오 로드: {vault_address: invested_usd}"""
    if not PORTFOLIO_FILE.exists():
        return {}
    try:
        with open(PORTFOLIO_FILE, encoding="utf-8") as f:
            d = json.load(f)
            if "positions" in d:
                return d["positions"]
            return d
    except Exception as e:
        print(f"  [RE] 포트폴리오 로드 오류: {e}")
        return {}


def load_rebalance_plan():
    """마지막 리밸런싱 플랜 로드"""
    if not REBALANCE_FILE.exists():
        return {}
    try:
        with open(REBALANCE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_rebalance_plan(plan: dict):
    """리밸런싱 플랜 저장"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REBALANCE_FILE, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2, default=float)
    print(f"  [RE] ✅ 플랜 저장: {REBALANCE_FILE}")


def load_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def update_status(patch: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    status = load_status()
    status.update(patch)
    status["last_updated"] = datetime.now().isoformat()
    STATUS_FILE.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8",
    )


# ── 리밸런싱 주기 판단 ────────────────────────────────────────────────────────
def should_rebalance(vault_map: dict = None, my_portfolio: dict = None, force: bool = False) -> tuple[bool, str, int]:
    """
    포트폴리오 변동성에 따라 가변적인 리밸런싱 주기(14일 ~ 45일)를 산출하고 여부를 판단.
    Returns:
        (should_run: bool, reason: str, days_left: int)
    """
    if force:
        return True, "강제 실행 (--force)", 0

    # 1. 포트폴리오 가중 변동성 계산
    vols = []
    weights = []
    if my_portfolio and vault_map:
        total = sum(my_portfolio.values())
        if total > 0:
            for addr, usd in my_portfolio.items():
                v = vault_map.get(addr, {})
                vols.append(float(v.get("vol_score", 30.0)))
                weights.append(usd / total)
    if not vols:
        vols = [30.0]
        weights = [1.0]
    
    weighted_vol = sum(v * w for v, w in zip(vols, weights))
    # 변동성이 높을수록 주기를 단축 (14일 ~ 45일)
    adaptive_days = int(np.clip(30.0 * (30.0 / max(weighted_vol, 5.0)), 14, 45))

    plan = load_rebalance_plan()
    last_date_str = plan.get("generated_at", "")

    if not last_date_str:
        return True, f"첫 리밸런싱 실행 (가변 주기: {adaptive_days}일, 가중 변동성: {weighted_vol:.1f}%)", 0

    try:
        last_date = datetime.fromisoformat(last_date_str[:10])
        days_since = (datetime.now() - last_date).days
        
        # 60일 가드레일 체크
        if days_since >= MAX_REBALANCE_DAYS:
            return True, f"시간 가드레일 초과 도달 ({days_since}일 경과 >= {MAX_REBALANCE_DAYS}일)", 0
            
        days_left  = max(0, adaptive_days - days_since)

        if days_left <= 0:
            return True, f"가변 리밸런싱 주기 도달 (변동성 {weighted_vol:.1f}% -> 주기 {adaptive_days}일, {days_since}일 경과)", 0
        else:
            return False, f"가변 리밸런싱(주기 {adaptive_days}일, 변동성 {weighted_vol:.1f}%)까지 {days_left}일 남음", days_left
    except Exception:
        return True, "날짜 파싱 오류 → 재실행", 0


# ── 최적 포트폴리오 계산 ──────────────────────────────────────────────────────
def get_optimal_portfolio(vaults: list, top_k: int = 10) -> list:
    """
    portfolio_engine.get_recommendations 방식으로 최적 포트폴리오 계산.
    analyze_top_vaults.get_recommendations 를 재사용합니다.
    """
    try:
        from analyze_top_vaults import get_recommendations
        recs = get_recommendations(vaults, top_k=top_k)
        return recs
    except Exception as e:
        print(f"  [RE] get_recommendations 오류: {e}")
        # 폴백: 점수&필터 기반 단순 Equal Weight
        candidates = [
            v for v in vaults
            if v.get("allow_deposits")
            and v.get("apr_30d", 0) > DANGER_APR
            and v.get("max_drawdown", 999) <= DANGER_MDD
            and v.get("leader_equity_ratio", -1) >= 0.40
        ]
        candidates.sort(key=lambda v: v.get("score", 0), reverse=True)
        sel = candidates[:top_k]
        equal_alloc = round(100.0 / len(sel), 2) if sel else 0
        for v in sel:
            v["suggested_allocation"] = equal_alloc
        return sel


# ── 현재 포트폴리오 평가 ──────────────────────────────────────────────────────
def evaluate_current_portfolio(
    my_portfolio: dict,    # {address: usd_invested}
    vault_map: dict,       # {address: vault_dict}
    optimal: list,         # get_recommendations() 결과
    min_drift_pct: float = 5.0,
) -> dict:
    """
    현재 포트폴리오 vs 최적 포트폴리오 상태 분석.
    Returns 상세 평가 결과 dict.
    """
    total_invested = sum(my_portfolio.values())
    if total_invested <= 0:
        return {"error": "포트폴리오 총투자금이 0입니다."}

    import portfolio_tracker
    from resilience_analyzer import analyze_vault_resilience, get_tvl_change_7d
    snapshots = portfolio_tracker.load_snapshots_all()

    opt_map = {v["address"]: v for v in optimal}
    holdings = []
    danger_vaults   = []
    missing_vaults  = []  # 최적에 있지만 내가 없는 볼트
    excess_vaults   = []  # 내가 보유하지만 최적에 없는 볼트

    # 현재 보유 분석
    for addr, usd in my_portfolio.items():
        v      = vault_map.get(addr, {})
        apr    = _sf(v.get("apr_30d"))
        mdd    = _sf(v.get("max_drawdown"))
        name   = v.get("name", addr[:16] + "…")
        current_pct = round(usd / total_invested * 100, 2)
        target_v    = opt_map.get(addr)
        target_pct  = _sf(target_v.get("suggested_allocation")) if target_v else 0.0
        drift_pct   = current_pct - target_pct

        # 회복탄력성 기반 위험 예외 검증
        res = analyze_vault_resilience(addr, snapshots)
        is_buy_the_dip = False
        is_broken = False
        is_resilient = False
        if res:
            hist_mdd = res["historical_max_mdd"]
            curr_dd = res["current_drawdown"]
            rec_count = res["recovered_count"]
            avg_rec_days = res["avg_recovery_days"]
            
            # 과거 원복 성공 이력이 있고, 역사적 MDD 지지선 범위 내인 경우
            is_buy_the_dip = (
                curr_dd >= hist_mdd * 0.70
                and curr_dd <= hist_mdd * 1.15
                and rec_count >= 1
                and avg_rec_days <= 45.0
            )
            # 역사적 MDD를 한참 뚫고 내려가 복구가 보이지 않는 지지선 붕괴 상태
            is_broken = (
                curr_dd > hist_mdd * 1.15
                and (rec_count == 0 or avg_rec_days > 45.0)
            )
            # 회복탄력성이 검증된 자산인지 여부
            is_resilient = rec_count >= 1 and avg_rec_days <= 45.0

        basic_danger = (
            mdd > DANGER_MDD
            or apr < DANGER_APR
            or not v.get("allow_deposits", True)
        )

        # 7일 TVL 변동률 감시 (자금 급유출 감지 시 위험 처리)
        tvl_change = get_tvl_change_7d(addr, snapshots)
        is_tvl_bankrun = tvl_change <= -25.0

        is_danger = False
        danger_reason = ""
        if is_broken:
            is_danger = True
            danger_reason = f"추세 붕괴 (MDD {mdd:.1f}%)"
        elif is_tvl_bankrun:
            is_danger = True
            danger_reason = f"급격한 자금 유출 (7일 TVL {tvl_change:.1f}%)"
        elif basic_danger:
            # 기본 위험군이라도 회복탄력성이 입증되었고 추세가 붕괴되지 않았다면 위험에서 제외
            if is_resilient and not is_broken:
                is_danger = False
            else:
                is_danger = True
                if not v.get("allow_deposits", True):
                    danger_reason = "입금 불가 상태"
                elif apr < DANGER_APR:
                    danger_reason = f"수익률 음수 (APR {apr:.1f}%)"
                elif mdd > DANGER_MDD:
                    danger_reason = f"MDD 허용치 초과 ({mdd:.1f}% > {DANGER_MDD}%)"

        if is_danger:
            danger_vaults.append(addr)

        h = {
            "address":      addr,
            "name":         name,
            "invested_usd": round(usd, 2),
            "current_pct":  current_pct,
            "target_pct":   round(target_pct, 2),
            "drift_pct":    round(drift_pct, 2),
            "apr_30d":      round(apr, 2),
            "max_drawdown": round(mdd, 2),
            "robustness":   _sf(v.get("robustness_score")),
            "allow_deposits": v.get("allow_deposits", True),
            "is_danger":    is_danger,
            "danger_reason": danger_reason,
            "in_optimal":   addr in opt_map,
        }
        holdings.append(h)

        if addr not in opt_map:
            excess_vaults.append(h)

    # 최적 포트폴리오에만 있는 볼트 (내가 아직 없는)
    for v in optimal:
        if v["address"] not in my_portfolio:
            missing_vaults.append({
                "address":   v["address"],
                "name":      v.get("name", ""),
                "target_pct": _sf(v.get("suggested_allocation")),
                "apr_30d":   _sf(v.get("apr_30d")),
                "max_drawdown": _sf(v.get("max_drawdown")),
                "robustness":  _sf(v.get("robustness_score")),
            })

    # 리밸런싱 필요 여부
    needs_rebalance = False
    reasons = []

    if danger_vaults:
        needs_rebalance = True
        reasons.append(f"🔴 위험 볼트 {len(danger_vaults)}개 (MDD>{DANGER_MDD}% 또는 APR<0)")

    # 전체 비중 괴리 합산 계산 (Total absolute drift)
    total_absolute_drift = sum(abs(h["drift_pct"]) for h in holdings)
    total_absolute_drift += sum(abs(v["target_pct"]) for v in missing_vaults)
    
    if total_absolute_drift >= 15.0:
        needs_rebalance = True
        reasons.append(f"⚖️ 전체 포트폴리오 비중 괴리 누적치 임계값 도달 ({total_absolute_drift:.1f}% >= 15%)")

    drifted = [h for h in holdings if abs(h["drift_pct"]) >= min_drift_pct]
    if drifted:
        needs_rebalance = True
        top_drift = sorted(drifted, key=lambda x: abs(x["drift_pct"]), reverse=True)[0]
        reasons.append(
            f"📊 개별 비중 드리프트 {len(drifted)}개 볼트 (임계값 {min_drift_pct:.1f}%, 최대 {top_drift['name']}: {top_drift['drift_pct']:+.1f}%)"
        )

    if missing_vaults:
        needs_rebalance = True
        reasons.append(f"⭐ 신규 추천 볼트 {len(missing_vaults)}개 미보유")

    # 월간 수익 추정
    estimated_monthly = sum(
        h["invested_usd"] * h["apr_30d"] / 100 / 12
        for h in holdings
    )

    return {
        "total_invested":     round(total_invested, 2),
        "n_holdings":         len(holdings),
        "estimated_monthly":  round(estimated_monthly, 2),
        "estimated_annual":   round(estimated_monthly * 12, 2),
        "holdings":           holdings,
        "danger_vaults":      danger_vaults,
        "missing_vaults":     missing_vaults,
        "excess_vaults":      excess_vaults,
        "needs_rebalance":    needs_rebalance,
        "rebalance_reasons":  reasons,
    }


# ── 리밸런싱 실행 계획 생성 ───────────────────────────────────────────────────
def generate_rebalance_plan(
    evaluation: dict,
    optimal: list,
    my_portfolio: dict,
    min_drift_pct: float = 5.0,
) -> dict:
    """
    평가 결과 → 구체적 실행 계획 (출금 / 입금 USD 금액).

    Hyperliquid 볼트 출금은 1일 지연이 있으므로:
      - 오늘: 출금 신청 (WITHDRAW 액션)
      - 내일: 출금 완료 후 → 새 볼트에 입금 (DEPOSIT 액션)
    """
    total = evaluation.get("total_invested", 0)
    if total <= 0:
        return {}

    opt_map = {v["address"]: v for v in optimal}
    holdings_map = {h["address"]: h for h in evaluation.get("holdings", [])}

    actions = []

    # ── 1. 출금 계획 (현재 비중 > 목표 비중 + 드리프트 초과)
    for h in evaluation.get("holdings", []):
        addr         = h["address"]
        current_pct  = h["current_pct"]
        target_pct   = h["target_pct"]
        drift        = h["drift_pct"]

        # 위험 볼트는 목표 0% → 전액 출금
        if h["is_danger"] and addr not in opt_map:
            danger_r = h.get("danger_reason")
            if not danger_r:
                mdd_val = h.get("max_drawdown", 0.0)
                apr_val = h.get("apr_30d", 0.0)
                danger_r = f"MDD {mdd_val:.1f}% / APR {apr_val:.1f}%"
            reason_str = f"🔴 위험 볼트 ({danger_r})"
            actions.append({
                "step":       "D-1 오늘 출금 신청",
                "action":     "WITHDRAW",
                "address":    addr,
                "name":       h["name"],
                "amount_usd": round(h["invested_usd"], 2),
                "current_pct": current_pct,
                "target_pct": 0.0,
                "reason":     reason_str,
                "deadline":   "⚠️ 오늘 출금 신청 필요 (1일 지연 — 내일 완료)",
                "priority":   1,
            })
        # 비중 과잉 볼트 (드리프트 > 임계값)
        elif drift > min_drift_pct and addr in opt_map:
            reduce_usd = drift / 100 * total
            actions.append({
                "step":       "D-1 오늘 출금 신청",
                "action":     "WITHDRAW",
                "address":    addr,
                "name":       h["name"],
                "amount_usd": round(reduce_usd, 2),
                "current_pct": current_pct,
                "target_pct": target_pct,
                "reason":     f"비중 조정 ({current_pct:.1f}% → {target_pct:.1f}%)",
                "deadline":   "⚠️ 오늘 출금 신청 필요 (1일 지연)",
                "priority":   2,
            })

    # ── 총 출금 자금
    total_withdraw_usd = sum(a["amount_usd"] for a in actions if a["action"] == "WITHDRAW")

    # ── 2. 입금 계획 (목표 비중 > 현재 비중)
    deposit_actions = []
    for v in optimal:
        addr       = v["address"]
        target_pct = _sf(v.get("suggested_allocation"))
        current_h  = holdings_map.get(addr)
        current_pct = current_h["current_pct"] if current_h else 0.0
        drift_pct   = current_pct - target_pct

        if drift_pct < -min_drift_pct:   # 목표보다 부족
            add_usd = abs(drift_pct) / 100 * total
            deposit_actions.append({
                "step":       "D0 내일 입금",
                "action":     "DEPOSIT",
                "address":    addr,
                "name":       v.get("name", ""),
                "amount_usd": round(add_usd, 2),
                "current_pct": round(current_pct, 2),
                "target_pct":  round(target_pct, 2),
                "apr_30d":     _sf(v.get("apr_30d")),
                "reason":      f"비중 추가 ({current_pct:.1f}% → {target_pct:.1f}%)",
                "priority":    3,
            })

    actions.extend(deposit_actions)

    # ── 3. 신규 볼트 입금 (missing_vaults — 아예 없는 볼트)
    for mv in evaluation.get("missing_vaults", []):
        addr       = mv["address"]
        target_pct = _sf(mv.get("target_pct"))
        add_usd    = target_pct / 100 * total

        actions.append({
            "step":       "D0 내일 입금",
            "action":     "NEW_DEPOSIT",
            "address":    addr,
            "name":       mv.get("name", ""),
            "amount_usd": round(add_usd, 2),
            "current_pct": 0.0,
            "target_pct":  round(target_pct, 2),
            "apr_30d":     _sf(mv.get("apr_30d")),
            "reason":      "⭐ 신규 추천 볼트 진입",
            "priority":    4,
        })

    # ── 거래 비용 및 슬리피지 모델링 필터 (Friction Cost vs Expected Gain)
    opt_weighted_apr = sum(v.get("apr_30d", 0.0) * (v.get("suggested_allocation", 0.0) / 100.0) for v in optimal)
    filtered_actions = []
    for a in actions:
        if a["action"] == "WITHDRAW":
            # 위험군 탈출이거나 강제 실행이면 무조건 실행 (비용 무시)
            is_danger = any(h["address"] == a["address"] and h["is_danger"] for h in evaluation.get("holdings", []))
            if is_danger:
                filtered_actions.append(a)
                continue
            
            # 일반 비중 축소의 경우 비용-편익 분석 진행
            # 1일 출금 지연 기회비용 = W_usd * (old_apr / 100) / 365
            old_apr = sum(h["apr_30d"] for h in evaluation.get("holdings", []) if h["address"] == a["address"])
            opp_cost = a["amount_usd"] * (old_apr / 100.0) / 365.0
            # 슬리피지 및 수수료 마찰비용 = 0.2%
            friction_cost = a["amount_usd"] * 0.002
            total_cost = friction_cost + opp_cost
            
            # 30일간의 기대 수익 상승분 = W_usd * (new_apr - old_apr) / 100 * (30 / 365)
            new_apr = opt_weighted_apr
            expected_gain = a["amount_usd"] * (new_apr - old_apr) / 100.0 * (30.0 / 365.0)
            
            if expected_gain <= total_cost:
                a["action"] = "SKIPPED_WITHDRAW"
                a["skipped"] = True
                a["skip_reason"] = f"비용-편익 미달 (예상수익 ${expected_gain:.2f} <= 마찰비용 ${total_cost:.2f})"
                a["reason"] += f" [⚠️ 비용미달로 실행생략]"
                filtered_actions.append(a)
            else:
                filtered_actions.append(a)
        else:
            filtered_actions.append(a)
            
    actions = filtered_actions

    # ── 우선순위 정렬
    actions.sort(key=lambda a: a["priority"])

    # ── 요약 통계
    total_deposit_usd  = sum(a["amount_usd"] for a in actions if a["action"] in ("DEPOSIT", "NEW_DEPOSIT"))
    net_movement_usd   = total_withdraw_usd - total_deposit_usd

    # 리밸런싱 후 예상 월간 수익
    expected_monthly = sum(
        v.get("suggested_allocation", 0) / 100 * total * v.get("apr_30d", 0) / 100 / 12
        for v in optimal
    )

    return {
        "total_actions":      len(actions),
        "total_withdraw_usd": round(total_withdraw_usd, 2),
        "total_deposit_usd":  round(total_deposit_usd, 2),
        "net_movement_usd":   round(net_movement_usd, 2),
        "expected_monthly_usd": round(expected_monthly, 2),
        "actions":            actions,
        "action_summary": {
            "withdrawals":    sum(1 for a in actions if a["action"] == "WITHDRAW"),
            "deposits":       sum(1 for a in actions if a["action"] == "DEPOSIT"),
            "new_deposits":   sum(1 for a in actions if a["action"] == "NEW_DEPOSIT"),
        },
        "timeline": {
            "today":    "출금 신청 (WITHDRAW 항목)",
            "tomorrow": "① 출금 완료 확인 → ② 입금 실행 (DEPOSIT / NEW_DEPOSIT 항목)",
        }
    }


# ── 포트폴리오 건강 점수 ──────────────────────────────────────────────────────
def calc_portfolio_health(evaluation: dict, optimal: list) -> dict:
    """
    현재 포트폴리오 건강 점수 (0~100, 높을수록 좋음).
    """
    if not evaluation.get("holdings"):
        return {"score": 0, "grade": "N/A", "details": {}}

    holdings = evaluation["holdings"]
    total    = evaluation.get("total_invested", 1)
    opt_map  = {v["address"]: v for v in optimal}

    # 1. 위험 볼트 비중 (낮을수록 좋음)
    danger_usd = sum(h["invested_usd"] for h in holdings if h["is_danger"])
    danger_pct = danger_usd / total * 100

    # 2. 드리프트 합계 절댓값 (낮을수록 좋음)
    drift_sum = sum(abs(h["drift_pct"]) for h in holdings)

    # 3. 평균 APR (높을수록 좋음)
    w_apr = sum(h["invested_usd"] / total * h["apr_30d"] for h in holdings)

    # 4. 평균 Robustness (높을수록 좋음)
    w_rob = sum(h["invested_usd"] / total * h["robustness"] for h in holdings)

    # 5. 최적 커버리지 (내가 보유한 최적 볼트 비율)
    in_opt = sum(1 for h in holdings if h["address"] in opt_map)
    coverage = in_opt / len(optimal) * 100 if optimal else 0

    # 점수 계산 (100점 만점)
    score_danger   = max(0, 30 - danger_pct * 1.5)        # 위험 볼트 0% → 30점
    score_drift    = max(0, 25 - drift_sum * 0.5)          # 드리프트 0% → 25점
    score_apr      = min(25, max(0, w_apr * 0.8))          # APR 30% → 24점
    score_robust   = min(15, max(0, w_rob * 15))           # Robustness 1.0 → 15점
    score_coverage = coverage / 100 * 5                    # 커버리지 → 5점

    total_score = score_danger + score_drift + score_apr + score_robust + score_coverage
    total_score = max(0, min(100, round(total_score, 1)))

    if total_score >= 85:   grade = "A+"
    elif total_score >= 70: grade = "A"
    elif total_score >= 55: grade = "B"
    elif total_score >= 40: grade = "C"
    else:                   grade = "D"

    return {
        "score":   total_score,
        "grade":   grade,
        "details": {
            "danger_score":   round(score_danger, 1),
            "drift_score":    round(score_drift, 1),
            "apr_score":      round(score_apr, 1),
            "robust_score":   round(score_robust, 1),
            "coverage_score": round(score_coverage, 1),
            "danger_pct":     round(danger_pct, 2),
            "drift_sum_pct":  round(drift_sum, 2),
            "weighted_apr":   round(w_apr, 2),
            "weighted_rob":   round(w_rob, 4),
            "opt_coverage_pct": round(coverage, 1),
        },
    }


# ── 메인 분석 실행 ────────────────────────────────────────────────────────────
def run_rebalance_analysis(
    dry_run: bool = False,
    force:   bool = False,
    top_k:   int  = 10,
    capital: float = 100_000,
) -> dict:
    """
    ★ 30일 리밸런싱 분석 메인 함수.

    Args:
        dry_run: True이면 파일 저장 없음 (테스트 모드)
        force:   30일 주기 무시하고 강제 실행
        top_k:   추천 볼트 수
        capital: 포트폴리오 없을 경우 시뮬레이션 투자금

    Returns:
        완전한 리밸런싱 플랜 dict
    """
    today = datetime.now().strftime("%Y-%m-%d")
    print("=" * 60)
    print("  🔄 30일 리밸런싱 엔진 시작")
    print("=" * 60)

    # ── 스냅샷 로드
    vaults, snap_date = load_latest_snapshot()
    if not vaults:
        err = {"error": "스냅샷 없음. 먼저 analyze_top_vaults.py를 실행하세요."}
        print("  [RE] ⚠️ " + err["error"])
        return err

    print(f"  [RE] 스냅샷: {len(vaults)}개 볼트 ({snap_date})")
    vault_map = {v["address"]: v for v in vaults}

    # ── 최적 포트폴리오 계산
    optimal = get_optimal_portfolio(vaults, top_k=top_k)
    if not optimal:
        err = {"error": "최적 포트폴리오 계산 실패 (볼트 데이터 부족)"}
        print("  [RE] ⚠️ " + err["error"])
        return err
    print(f"  [RE] 최적 포트폴리오: {len(optimal)}개 볼트")

    # ── 내 포트폴리오 로드 (없으면 시뮬레이션 모드)
    my_portfolio = load_my_portfolio()
    simulation_mode = not bool(my_portfolio)
    if simulation_mode:
        print(f"  [RE] ⚠️ my_portfolio.json 없음 → ${{capital:,.0f}} 시뮬레이션 모드")
        # 최적 포트폴리오 기준 Equal 시뮬레이션
        my_portfolio = {
            v["address"]: v.get("suggested_allocation", 0) / 100 * capital
            for v in optimal
        }

    total_invested = sum(my_portfolio.values())
    print(f"  [RE] 총 투자금: ${total_invested:,.0f} ({'시뮬레이션' if simulation_mode else '실제'})")

    # ── 리밸런싱 주기 판단
    should_run, timing_reason, days_left = should_rebalance(vault_map, my_portfolio, force=force)
    print(f"  [RE] 리밸런싱 여부: {should_run} ({timing_reason})")

    # ── 가변 비중 임계값 계산 (3.0% ~ 8.0%)
    vols = []
    weights = []
    if my_portfolio and vault_map:
        for addr, usd in my_portfolio.items():
            v = vault_map.get(addr, {})
            vols.append(float(v.get("vol_score", 30.0)))
            weights.append(usd / total_invested)
    if not vols:
        vols = [30.0]
        weights = [1.0]
    weighted_vol = sum(v * w for v, w in zip(vols, weights))
    adaptive_drift = float(np.clip(5.0 * (weighted_vol / 30.0), 3.0, 8.0))
    print(f"  [RE] 가변 비중 임계값: {adaptive_drift:.2f}% (가중 변동성: {weighted_vol:.1f}%)")

    # ── 현재 포트폴리오 평가
    evaluation = evaluate_current_portfolio(my_portfolio, vault_map, optimal, min_drift_pct=adaptive_drift)
    if "error" in evaluation:
        return evaluation

    # ── 건강 점수
    health = calc_portfolio_health(evaluation, optimal)
    print(f"  [RE] 포트폴리오 건강 점수: {health['score']} ({health['grade']})")

    # ── 리밸런싱 계획 생성 (리밸런싱 필요 시)
    rebalance_plan = {}
    if evaluation.get("needs_rebalance") or should_run:
        rebalance_plan = generate_rebalance_plan(evaluation, optimal, my_portfolio, min_drift_pct=adaptive_drift)
        n_actions = rebalance_plan.get("total_actions", 0)
        print(f"  [RE] 리밸런싱 액션: {n_actions}개")
        if n_actions > 0:
            print(f"       출금: ${rebalance_plan.get('total_withdraw_usd', 0):,.0f}")
            print(f"       입금: ${rebalance_plan.get('total_deposit_usd', 0):,.0f}")
    else:
        print(f"  [RE] ✅ 리밸런싱 불필요 ({timing_reason})")

    # ── 최종 플랜 결합
    plan = {
        "generated_at":       today,
        "generated_at_full":  datetime.now().isoformat(),
        "snapshot_date":      snap_date,
        "simulation_mode":    simulation_mode,

        # 타이밍
        "rebalance_cycle_days":  REBALANCE_DAYS,
        "should_rebalance":      should_run or evaluation.get("needs_rebalance", False),
        "timing_reason":         timing_reason,
        "days_to_next_rebalance": days_left,

        # 현재 포트폴리오 상태
        "current_portfolio": {
            "total_invested":    evaluation.get("total_invested", 0),
            "n_vaults":          evaluation.get("n_holdings", 0),
            "estimated_monthly": evaluation.get("estimated_monthly", 0),
            "estimated_annual":  evaluation.get("estimated_annual", 0),
            "holdings":          evaluation.get("holdings", []),
        },

        # 최적 포트폴리오
        "optimal_portfolio": [
            {
                "address":    v.get("address"),
                "name":       v.get("name"),
                "target_pct": _sf(v.get("suggested_allocation")),
                "target_usd": round(_sf(v.get("suggested_allocation")) / 100 * total_invested, 2),
                "apr_30d":    _sf(v.get("apr_30d")),
                "max_drawdown": _sf(v.get("max_drawdown")),
                "robustness": _sf(v.get("robustness_score")),
                "sharpe":     _sf(v.get("sharpe_ratio")),
            }
            for v in optimal
        ],

        # 리밸런싱 평가
        "evaluation": {
            "needs_rebalance":  evaluation.get("needs_rebalance"),
            "reasons":          evaluation.get("rebalance_reasons", []),
            "danger_vaults":    evaluation.get("danger_vaults", []),
            "missing_vaults":   evaluation.get("missing_vaults", []),
            "excess_vaults":    [{"address": ev["address"], "name": ev["name"]}
                                  for ev in evaluation.get("excess_vaults", [])],
        },

        # 건강 점수
        "health": health,

        # 실행 계획
        "rebalance_plan": rebalance_plan,

        # scheduler.py send_alert 연동용 요약
        "alert_summary": _build_alert_summary(evaluation, rebalance_plan, health),
    }

    # ── 파일 저장
    if not dry_run:
        save_rebalance_plan(plan)
        # status.json 업데이트
        update_status({
            "rebalance_analysis_date": today,
            "rebalance_needed":        plan["should_rebalance"],
            "rebalance_health_score":  health["score"],
            "rebalance_health_grade":  health["grade"],
            "days_to_rebalance":       days_left,
        })
    else:
        print("  [RE] 🔍 Dry-run 모드: 파일 저장 생략")

    print("=" * 60)
    return plan


def _build_alert_summary(evaluation: dict, plan: dict, health: dict) -> dict:
    """
    scheduler.py send_alert() 연동을 위한 알림 요약 생성.
    """
    reasons = evaluation.get("rebalance_reasons", [])
    actions = plan.get("actions", [])
    withdrawals = [a for a in actions if a["action"] == "WITHDRAW"]

    summary = {
        "level":    "WARNING" if evaluation.get("needs_rebalance") else "INFO",
        "title":    "리밸런싱 분석 완료" if not evaluation.get("needs_rebalance") else "⚠️ 리밸런싱 권고",
        "message":  "\n".join(reasons) if reasons else "포트폴리오 정상 — 리밸런싱 불필요",
        "health_score": health.get("score", 0),
        "health_grade": health.get("grade", "N/A"),
        "action_required": bool(withdrawals),
        "withdrawal_items": [
            {
                "name":       w["name"],
                "amount_usd": w["amount_usd"],
                "reason":     w["reason"],
                "deadline":   w.get("deadline", ""),
            }
            for w in withdrawals
        ],
    }
    return summary


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperliquid 30일 리밸런싱 엔진")
    parser.add_argument("--dry-run", action="store_true", help="파일 저장 없이 분석만")
    parser.add_argument("--force",   action="store_true", help="30일 주기 무시하고 강제 실행")
    parser.add_argument("--top-k",   type=int, default=10, help="추천 볼트 수 (기본: 10)")
    parser.add_argument("--capital", type=float, default=100_000, help="시뮬레이션 투자금 (기본: $100,000)")
    args = parser.parse_args()

    result = run_rebalance_analysis(
        dry_run=args.dry_run,
        force=args.force,
        top_k=args.top_k,
        capital=args.capital,
    )

    if "error" in result:
        print(f"\n❌ 오류: {result['error']}")
        sys.exit(1)

    # 결과 요약 출력
    print("\n📊 리밸런싱 분석 결과")
    print("-" * 40)
    pf = result["current_portfolio"]
    print(f"  총 투자금:  ${pf['total_invested']:>12,.0f}")
    print(f"  예상 월수익: ${pf['estimated_monthly']:>11,.0f}")
    print(f"  예상 연수익: ${pf['estimated_annual']:>11,.0f}")
    print(f"  건강 점수:  {result['health']['score']} ({result['health']['grade']})")
    print(f"  리밸런싱 필요: {'✅ 예' if result['should_rebalance'] else '✅ 아니오 — 이미 최적화됨'}")

    plan = result.get("rebalance_plan", {})
    if plan.get("actions"):
        print(f"\n  리밸런싱 액션: {plan['total_actions']}개")
        print(f"  오늘 출금:     ${plan['total_withdraw_usd']:,.0f}")
        print(f"  내일 입금:     ${plan['total_deposit_usd']:,.0f}")
        print("\n  ── 실행 계획 ──")
        for a in plan["actions"]:
            emoji = "↗️" if a["action"] in ("DEPOSIT", "NEW_DEPOSIT") else "↙️"
            print(f"  {emoji} [{a['step']}] {a['name'][:25]:<25} ${a['amount_usd']:>10,.0f}  ({a['reason']})")

    if args.dry_run:
        print("\n  [dry-run] 파일 저장 생략 — 실제 적용 시 --force 또는 --dry-run 제거")
    else:
        print(f"\n  💾 저장 위치: {REBALANCE_FILE}")
