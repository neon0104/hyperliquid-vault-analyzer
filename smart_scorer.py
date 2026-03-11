#!/usr/bin/env python3
"""
smart_scorer.py — 평균회귀 기반 스마트 볼트 스코어러
=====================================================
핵심 인사이트 (Research 결과):
  - 현재 높은 APR은 지속성(persistence)이 매우 낮음 → 미래 수익 예측력 약함
  - 전체 수익곡선 기반 Sharpe ratio는 전략의 "실력"을 반영
  - 고(高)Sharpe + 최근 30일 APR 상대적 하락 = 일시적 슬럼프 → 평균 회귀 기회
  - Robustness score (R², 단조성, MDD회복력)가 장기 성과의 가장 강한 예측변수

스코어 공식:
  mean_reversion_score = (
      robustness × 0.35          # 장기 수익곡선 품질
    + normalized_sharpe × 0.30   # 리스크 대비 수익 (역대 전체 기준)
    + undervalue × 0.20          # 최근 APR이 역대 대비 얼마나 낮은지 (기회 신호)
    + leader_equity × 0.10       # 운용자 본인 투자 비율 (alignment)
    + age_score × 0.05           # 검증 기간
  )

사용법:
  from smart_scorer import compute_smart_scores, get_smart_recommendations
"""

import sys, os
import numpy as np
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 평균회귀 기회 점수 계산 ───────────────────────────────────────────────────
def calc_undervalue_score(vault: dict) -> float:
    """
    현재 30일 APR이 전체 기록 대비 얼마나 낮은지 계산.
    높을수록 "현재 저평가 상태" → 평균 회귀 기회.
    반환: 0~1 (1 = 매우 저평가, 기회)
    """
    alltime_pnl = vault.get("alltime_pnl", [])
    tvl         = float(vault.get("tvl", 1) or 1)
    apr_30d     = float(vault.get("apr_30d", 0))

    if len(alltime_pnl) < 30:
        return 0.5  # 데이터 부족 → 중립

    arr = np.array(alltime_pnl, dtype=float)

    # 30일 구간별 수익률 계산 (슬라이딩 윈도우)
    window = 30
    step   = max(1, (len(arr) - window) // 20)  # 최대 20개 구간
    period_aprs = []
    for i in range(0, len(arr) - window, step):
        seg = arr[i:i + window]
        seg_diff = np.diff(seg)
        denom = tvl + np.abs(seg[:-1]) + 1e-9
        seg_ret = np.sum(seg_diff / denom) * 12 * 100   # 연환산
        period_aprs.append(seg_ret)

    if not period_aprs:
        return 0.5

    hist_median = float(np.median(period_aprs))
    hist_std    = float(np.std(period_aprs)) + 1e-9

    # 현재 APR이 역대 중앙값보다 얼마나 낮은가 (z-score 기반)
    z = (hist_median - apr_30d) / hist_std
    # z > 0 이면 현재가 역대보다 낮음 (기회), z < 0 이면 현재가 역대보다 높음 (고점 위험)
    score = 1 / (1 + np.exp(-z * 0.8))  # sigmoid 변환 → 0~1

    return float(np.clip(score, 0, 1))


def calc_age_score(age_days: int) -> float:
    """운영 기간 점수. 180일 이상이면 최고점."""
    if age_days >= 365:  return 1.0
    if age_days >= 180:  return 0.8
    if age_days >= 90:   return 0.5
    if age_days >= 30:   return 0.3
    return 0.1


def calc_longterm_sharpe(alltime_pnl: list, tvl: float) -> float:
    """전체 alltime_pnl로 계산하는 장기 Sharpe (단기 APR에 영향 없음)."""
    if not alltime_pnl or len(alltime_pnl) < 10:
        return 0.0
    arr   = np.array(alltime_pnl, dtype=float)
    diffs  = np.diff(arr)
    denom  = tvl + np.abs(arr[:-1]) + 1e-9
    daily_r = np.clip(diffs / denom, -0.5, 0.5)
    mu      = daily_r.mean()
    sigma   = daily_r.std() + 1e-9
    return float(mu / sigma * np.sqrt(252))  # 연환산


def compute_smart_scores(vaults: list) -> list:
    """
    모든 볼트에 평균회귀 스마트 점수 부여.
    반환: 새 'smart_score', 'undervalue_score', 'longterm_sharpe' 필드 포함된 리스트
    """
    # 장기 Sharpe 계산
    for v in vaults:
        v["longterm_sharpe"] = calc_longterm_sharpe(
            v.get("alltime_pnl", []), float(v.get("tvl", 1) or 1)
        )
        v["undervalue_score"] = calc_undervalue_score(v)
        v["age_score"]        = calc_age_score(v.get("age_days", 0))

    # 정규화 (0~1)
    def normalize(vals):
        mn, mx = min(vals), max(vals)
        rng = mx - mn + 1e-9
        return [(v - mn) / rng for v in vals]

    n = len(vaults)
    if n == 0:
        return vaults

    sharpe_norm = normalize([v["longterm_sharpe"] for v in vaults])
    rob_vals    = [float(v.get("robustness_score", 0)) for v in vaults]
    leader_vals = [float(v.get("leader_equity_ratio", 0)) for v in vaults]

    for i, v in enumerate(vaults):
        smart = (
            rob_vals[i]             * 0.35 +   # 수익곡선 품질
            sharpe_norm[i]          * 0.30 +   # 장기 Sharpe
            v["undervalue_score"]   * 0.20 +   # 평균회귀 기회
            leader_vals[i]          * 0.10 +   # 운용자 본인 투자
            v["age_score"]          * 0.05     # 검증 기간
        )
        v["smart_score"] = round(float(smart), 4)

    # smart_score 내림차순 정렬
    vaults.sort(key=lambda v: v["smart_score"], reverse=True)
    return vaults


def get_smart_recommendations(
    vaults: list,
    top_k: int = 10,
    min_allow_deposits: bool = True,
    min_leader_equity: float = 0.30,
    min_robustness: float = 0.20,
    min_apr: float = -999,       # APR 최소값 (음수도 허용, 회복 기대)
) -> list:
    """
    평균회귀 전략 기반 추천 볼트 선정.
    기존 get_recommendations()와 달리:
      - 현재 APR이 낮아도 장기 Sharpe + Robustness가 높으면 추천
      - undervalue_score 가 높을수록 우선 (= 현재 저평가된 우량 볼트)
    """
    if not vaults:
        return []

    # 1단계 필터
    filtered = [
        v for v in vaults
        if (not min_allow_deposits or v.get("allow_deposits", True))
        and v.get("leader_equity_ratio", 0) >= min_leader_equity
        and v.get("robustness_score", 0) >= min_robustness
        and v.get("apr_30d", 0) >= min_apr
        and v.get("data_points", 0) >= 5
    ]

    # 필터가 너무 엄격하면 완화
    if len(filtered) < 3:
        filtered = [
            v for v in vaults
            if v.get("allow_deposits", True)
            and v.get("robustness_score", 0) >= min_robustness * 0.5
            and v.get("data_points", 0) >= 5
        ]
        print(f"  [Smart] 필터 완화 적용: {len(filtered)}개")

    # smart_score 기준 정렬 (이미 compute_smart_scores에서 정렬됨)
    filtered.sort(key=lambda v: v["smart_score"], reverse=True)
    selected = filtered[:top_k]

    # 배분 비중: smart_score 비례 배분
    total_score = sum(v["smart_score"] for v in selected) or 1.0
    for v in selected:
        raw_alloc = v["smart_score"] / total_score * 100
        # 최소 5%, 최대 35% 제한
        v["smart_allocation"] = round(max(5.0, min(35.0, raw_alloc)), 1)

    # 합계 100%로 재정규화
    total_alloc = sum(v["smart_allocation"] for v in selected)
    if total_alloc > 0:
        for v in selected:
            v["smart_allocation"] = round(v["smart_allocation"] / total_alloc * 100, 1)

    return selected


def compare_strategies(vaults: list, top_k: int = 10) -> dict:
    """
    기존 APR 기반 전략 vs 스마트 평균회귀 전략 비교.
    반환: 양쪽 추천 목록 + 겹치는 볼트 + 차이점
    """
    # APR 기반 (기존)
    apr_based = sorted(
        [v for v in vaults if v.get("allow_deposits") and v.get("robustness_score", 0) >= 0.35],
        key=lambda v: (v.get("robustness_score", 0) * 0.5 + min(v.get("apr_30d", 0) / 100, 1) * 0.5),
        reverse=True
    )[:top_k]

    # 스마트 평균회귀 기반
    smart_based = get_smart_recommendations(vaults, top_k=top_k)

    apr_addrs   = {v["address"] for v in apr_based}
    smart_addrs = {v["address"] for v in smart_based}
    overlap     = apr_addrs & smart_addrs
    smart_only  = smart_addrs - apr_addrs

    print(f"\n=== 전략 비교 ===")
    print(f"APR 기반 추천:  {len(apr_based)}개")
    print(f"스마트 추천:    {len(smart_based)}개")
    print(f"겹치는 볼트:    {len(overlap)}개 ({len(overlap)/max(top_k,1)*100:.0f}%)")
    print(f"스마트만 추가:  {len(smart_only)}개 (평균회귀 기회)")

    print("\n[스마트 전략 추가 볼트 (APR은 낮지만 장기 실력 우수):]")
    for v in smart_based:
        if v["address"] in smart_only:
            print(f"  {v['name'][:28]:<28} "
                  f"APR={v.get('apr_30d',0):+6.1f}%  "
                  f"LTSharpe={v.get('longterm_sharpe',0):5.2f}  "
                  f"Undervalue={v.get('undervalue_score',0):.2f}  "
                  f"Smart={v['smart_score']:.3f}")

    return {
        "apr_strategy":   apr_based,
        "smart_strategy": smart_based,
        "overlap_count":  len(overlap),
        "smart_only":     [v for v in smart_based if v["address"] in smart_only],
    }


if __name__ == "__main__":
    # 테스트용: 최신 스냅샷 로드 후 비교
    import json, glob
    from pathlib import Path

    snap_files = sorted(Path("vault_data/snapshots").glob("*.json"), reverse=True)
    if not snap_files:
        print("스냅샷 없음. 먼저 analyze_top_vaults.py 를 실행하세요.")
        sys.exit(1)

    with open(snap_files[0], encoding="utf-8") as f:
        vaults = json.load(f)

    print(f"스냅샷 로드: {snap_files[0].stem} ({len(vaults)}개 볼트)")
    vaults_scored = compute_smart_scores(vaults)
    result = compare_strategies(vaults_scored, top_k=10)

    print("\n=== 스마트 추천 TOP 10 ===")
    for i, v in enumerate(result["smart_strategy"], 1):
        print(f"{i:2}. {v['name'][:28]:<28} "
              f"APR={v.get('apr_30d',0):+6.1f}%  "
              f"LTSharpe={v.get('longterm_sharpe',0):5.2f}  "
              f"Rob={v.get('robustness_score',0):.3f}  "
              f"Undervalue={v.get('undervalue_score',0):.2f}  "
              f"Smart={v['smart_score']:.3f}  "
              f"Alloc={v.get('smart_allocation',0):.1f}%")
