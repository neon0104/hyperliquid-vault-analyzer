#!/usr/bin/env python3
"""
포트폴리오 엔진 v1.0
====================
① alltime_pnl → 일별 수익률 & 로버스트니스 분석
② 상관관계 행렬 계산 (저상관 볼트 추출)
③ 4가지 포트폴리오 최적화 (Max Sharpe / Min Var / Risk Parity / Min CVaR)
④ 백테스팅 (전체 기간 시뮬레이션)
⑤ 일별 히스토리 누적 관리
"""

import json, os, sys, glob
import numpy as np
from datetime import datetime
from pathlib import Path
from scipy.optimize import minimize

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA_DIR      = "vault_data"
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
HISTORY_DIR   = os.path.join(DATA_DIR, "history")
SIM_CAPITAL   = 100_000

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR,   exist_ok=True)

_sf = lambda x, d=0.0: float(x) if x is not None else d

# ── 스냅샷 로드 ───────────────────────────────────────────────────────────────
def load_latest_snapshot():
    paths = sorted(Path(SNAPSHOTS_DIR).glob("*.json"), reverse=True)
    if not paths:
        return None, None
    with open(str(paths[0]), encoding="utf-8") as f:
        return json.load(f), paths[0].stem

def load_snapshot_by_date(date_str):
    """특정 날짜의 스냅샷 로드"""
    p = Path(SNAPSHOTS_DIR) / f"{date_str}.json"
    if not p.exists():
        return None, None
    try:
        with open(str(p), encoding="utf-8") as f:
            data = json.load(f)
            if not data or not isinstance(data, list) or len(data) < 5:
                return None, None
            return data, date_str
    except Exception:
        return None, None

def load_all_history(max_days=90):
    """날짜별 볼트 메트릭 히스토리 (스냅샷 누적)"""
    paths = sorted(Path(SNAPSHOTS_DIR).glob("*.json"), reverse=True)[:max_days]
    history = {}
    dates   = []
    for p in reversed(paths):
        date = p.stem
        dates.append(date)
        try:
            with open(str(p), encoding="utf-8") as f:
                day = json.load(f)
        except Exception:
            continue
        for v in day:
            addr = v.get("address", "")
            if not addr:
                continue
            if addr not in history:
                history[addr] = {
                    "name": v.get("name", ""),
                    "dates": [], "tvl": [], "apr_30d": [],
                    "sharpe_ratio": [], "max_drawdown": [],
                    "robustness_score": [], "score": [], "rank": []
                }
            h = history[addr]
            if date not in h["dates"]:
                h["dates"].append(date)
                h["tvl"].append(_sf(v.get("tvl", 0)))
                h["apr_30d"].append(_sf(v.get("apr_30d", 0)))
                h["sharpe_ratio"].append(_sf(v.get("sharpe_ratio", 0)))
                h["max_drawdown"].append(_sf(v.get("max_drawdown", 0)))
                h["robustness_score"].append(_sf(v.get("robustness_score", 0)))
                h["score"].append(_sf(v.get("score", 0)))
                h["rank"].append(_sf(v.get("rank", 999)))
    return history, dates

# ── 수익률 행렬 ───────────────────────────────────────────────────────────────
def extract_returns(alltime_pnl, tvl, min_pts=8, max_pts=90):
    """alltime_pnl[] → 정규화 일별 수익률"""
    if not alltime_pnl or len(alltime_pnl) < min_pts or tvl <= 0:
        return None
    arr = np.array(alltime_pnl[-max_pts:], dtype=float)
    diffs = np.diff(arr)
    denom = tvl + np.abs(arr[:-1]) + 1e-9
    return np.clip(diffs / denom, -0.5, 0.5)

def build_returns_matrix(vaults, min_pts=8, max_pts=90):
    """볼트 리스트 → (선택 볼트, 수익률 행렬 (n, T))"""
    vr = {}
    for v in vaults:
        r = extract_returns(v.get("alltime_pnl", []), v.get("tvl", 0), min_pts, max_pts)
        if r is not None and len(r) >= min_pts:
            vr[v["address"]] = (v, r)
    if len(vr) < 2:
        return [], np.empty((0, 0))
    min_len = max(min_pts, min(min(len(r) for _, r in vr.values()), max_pts))
    sel, rows = [], []
    for addr, (vault, ret) in vr.items():
        sel.append(vault)
        rows.append(ret[-min_len:])
    return sel, np.array(rows)

# ── 상관관계 행렬 ─────────────────────────────────────────────────────────────
def calc_corr(returns_matrix):
    """피어슨 상관관계 행렬"""
    if returns_matrix.shape[0] < 2:
        return np.eye(1)
    stds = returns_matrix.std(axis=1, keepdims=True)
    stds[stds < 1e-10] = 1.0
    normed = (returns_matrix - returns_matrix.mean(axis=1, keepdims=True)) / stds
    T = returns_matrix.shape[1]
    corr = np.clip((normed @ normed.T) / (T - 1), -1, 1)
    np.fill_diagonal(corr, 1.0)
    return corr

# ── 저상관 고성과 볼트 선택 ───────────────────────────────────────────────────
def select_low_corr_vaults(vaults, returns_matrix, corr_matrix, top_k=10, max_corr=0.6):
    """
    탐욕적 선택: Sharpe 내림차순으로 정렬 후
    기선택 볼트와 상관 < max_corr 인 볼트만 추가
    """
    means  = returns_matrix.mean(axis=1)
    stds   = returns_matrix.std(axis=1)
    sharpes = np.where(stds > 1e-8, means / stds * np.sqrt(252), 0)
    priority = np.argsort(-sharpes)

    sel, sel_idx = [], []
    for idx in priority:
        if len(sel) >= top_k:
            break
        if sharpes[idx] <= 0:
            continue
        if sel_idx:
            max_c = max(abs(corr_matrix[idx, j]) for j in sel_idx)
            if max_c > max_corr:
                continue
        sel.append(vaults[idx])
        sel_idx.append(idx)

    if not sel_idx:
        return [], [], np.empty((0, 0))
    return sel, sel_idx, returns_matrix[sel_idx]

# ── 포트폴리오 최적화 ─────────────────────────────────────────────────────────
def _pf_stats(w, ann_means, ann_cov, names):
    ret = float(w @ ann_means) * 100
    cov_scal = ann_cov if ann_cov.ndim == 2 else np.array([[ann_cov]])
    var = max(float(w @ cov_scal @ w), 0)
    vol = float(np.sqrt(var)) * 100
    sharpe = ret / vol if vol > 0 else 0
    return {
        "annual_return_pct": round(ret, 2),
        "annual_vol_pct":    round(vol, 2),
        "sharpe":            round(sharpe, 3),
        "weights":           {names[i]: round(float(w[i]) * 100, 1) for i in range(len(names))}
    }

def _base_opt(obj_fn, n, max_w=0.35):
    w0     = np.ones(n) / n
    bounds = [(0.0, max_w)] * n
    cons   = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    try:
        res = minimize(obj_fn, w0, method="SLSQP", bounds=bounds, constraints=cons,
                       options={"ftol": 1e-9, "maxiter": 1000})
        w = res.x if res.success else w0
    except Exception:
        w = w0
    w = np.clip(w, 0, 1)
    return w / w.sum()

def optimize_max_sharpe(returns_matrix, names, max_w=0.35):
    n  = returns_matrix.shape[0]
    mu = returns_matrix.mean(axis=1) * 252
    cov= np.atleast_2d(np.cov(returns_matrix) * 252)
    if n == 1:
        return np.array([1.0]), _pf_stats(np.array([1.0]), mu, cov, names)
    def obj(w): 
        r = w @ mu; v = max(w @ cov @ w, 1e-12)
        return -r / np.sqrt(v)
    w = _base_opt(obj, n, max_w)
    return w, _pf_stats(w, mu, cov, names)

def optimize_min_variance(returns_matrix, names, max_w=0.35):
    n  = returns_matrix.shape[0]
    mu = returns_matrix.mean(axis=1) * 252
    cov= np.atleast_2d(np.cov(returns_matrix) * 252)
    if n == 1:
        return np.array([1.0]), _pf_stats(np.array([1.0]), mu, cov, names)
    w = _base_opt(lambda w: w @ cov @ w, n, max_w)
    return w, _pf_stats(w, mu, cov, names)

def optimize_risk_parity(returns_matrix, names, max_w=0.35):
    n  = returns_matrix.shape[0]
    mu = returns_matrix.mean(axis=1) * 252
    cov= np.atleast_2d(np.cov(returns_matrix) * 252)
    if n == 1:
        return np.array([1.0]), _pf_stats(np.array([1.0]), mu, cov, names)
    target = np.ones(n) / n
    def obj(w):
        w = np.abs(w)
        sigma = np.sqrt(max(w @ cov @ w, 1e-12))
        mc = (cov @ w) / sigma
        rc = w * mc
        s  = rc.sum()
        if s < 1e-12: return 0.0
        return np.sum((rc / s - target) ** 2)
    w0 = np.ones(n) / n
    bounds = [(0.01, max_w)] * n
    cons   = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    try:
        res = minimize(obj, w0, method="SLSQP", bounds=bounds, constraints=cons,
                       options={"ftol": 1e-9, "maxiter": 2000})
        w = np.abs(res.x if res.success else w0)
    except Exception:
        w = w0
    w = np.clip(w, 0, 1); w /= w.sum()
    return w, _pf_stats(w, mu, cov, names)

def optimize_min_cvar(returns_matrix, names, alpha=0.05, max_w=0.35):
    """최소 CVaR — 원금 보호 최우선"""
    n  = returns_matrix.shape[0]
    mu = returns_matrix.mean(axis=1) * 252
    cov= np.atleast_2d(np.cov(returns_matrix) * 252)
    if n == 1:
        return np.array([1.0]), _pf_stats(np.array([1.0]), mu, cov, names)
    def obj(w):
        pr = returns_matrix.T @ w
        var_val = np.percentile(pr, alpha * 100)
        tail = pr[pr <= var_val]
        return -tail.mean() if len(tail) > 0 else 0.0
    w = _base_opt(obj, n, max_w)
    return w, _pf_stats(w, mu, cov, names)

# ── 백테스팅 ──────────────────────────────────────────────────────────────────
def backtest(weights, returns_matrix, initial_capital=SIM_CAPITAL):
    """포트폴리오 백테스팅"""
    if len(weights) == 0 or returns_matrix.size == 0:
        return {}
    w  = np.array(weights)
    pr = returns_matrix.T @ w            # (T,) 일별 포트 수익률
    eq = initial_capital * np.cumprod(1 + pr)
    eq = np.insert(eq, 0, float(initial_capital))

    rm  = np.maximum.accumulate(eq)
    dd  = (rm - eq) / rm * 100
    T   = len(pr)
    ann_r = ((eq[-1] / eq[0]) ** (252 / T) - 1) * 100 if T > 0 else 0
    vol   = float(pr.std() * np.sqrt(252) * 100)
    sharpe= ann_r / vol if vol > 0 else 0

    # 간략 equity curve (최대 60 포인트)
    step = max(1, len(eq) // 60)
    curve = [round(float(e), 2) for e in eq[::step]]

    return {
        "initial_capital":    initial_capital,
        "final_value":        round(float(eq[-1]), 2),
        "total_profit":       round(float(eq[-1] - initial_capital), 2),
        "total_return_pct":   round(float((eq[-1] / eq[0] - 1) * 100), 2),
        "annual_return_pct":  round(ann_r, 2),
        "max_drawdown_pct":   round(float(dd.max()), 2),
        "sharpe_ratio":       round(sharpe, 3),
        "volatility_pct":     round(vol, 2),
        "n_periods":          T,
        "equity_curve":       curve,
    }


# ── ★ 포트폴리오 일별 추적 (요구사항 9번) ──────────────────────────────────────
PORTFOLIO_HISTORY_FILE = os.path.join(DATA_DIR, "portfolio_history.json")


def load_portfolio_history():
    """저장된 포트폴리오 이력 로드"""
    if not os.path.exists(PORTFOLIO_HISTORY_FILE):
        return {}
    try:
        with open(str(PORTFOLIO_HISTORY_FILE), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_portfolio_history(history):
    """포트폴리오 이력 저장"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(str(PORTFOLIO_HISTORY_FILE), "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2, default=float)


def calc_portfolio_risk_score(recommendations):
    """
    포트폴리오 리스크 점수 (0=안전, 1=위험)
    = 낙은 robustness + 높은 MDD + 높은 변동성의 가중 합산
    """
    if not recommendations:
        return 0.5
    total_w = sum(v.get("suggested_allocation", 0) for v in recommendations)
    if total_w <= 0:
        return 0.5

    weighted_rob = sum(
        v.get("suggested_allocation", 0) * v.get("robustness_score", 0.3)
        for v in recommendations
    ) / total_w
    weighted_mdd = sum(
        v.get("suggested_allocation", 0) * v.get("max_drawdown", 20)
        for v in recommendations
    ) / total_w
    weighted_vol = sum(
        v.get("suggested_allocation", 0) * v.get("vol_score", 30)
        for v in recommendations
    ) / total_w

    # 리스크 = (1 - robustness) 음, MDD, 변동성 가중합
    risk = (
        (1.0 - min(weighted_rob, 1.0))   * 0.50 +
        min(weighted_mdd / 50.0, 1.0)    * 0.30 +
        min(weighted_vol / 100.0, 1.0)   * 0.20
    )
    return round(float(np.clip(risk, 0, 1)), 4)


def update_portfolio_tracking(recommendations, date_str, initial_capital=SIM_CAPITAL):
    """
    ★ 매일 포트폴리오 성과 기록 (일 1회 자동 누적)
    - recommendations : get_recommendations() 결과 (suggested_allocation 포함)
    - date_str        : 'YYYY-MM-DD'
    - initial_capital : 최초 투자금 (기준값, 변하지 않음)
    반환: 전체 이력 dict
    """
    history = load_portfolio_history()
    if date_str in history:
        return history  # 오늘 기록 이미 존재

    sorted_dates = sorted(history.keys())
    if not sorted_dates:
        # 첫날 초기화
        prev_value      = float(initial_capital)
        cumulative_pnl  = 0.0
        max_equity_ever = float(initial_capital)
    else:
        last            = history[sorted_dates[-1]]
        prev_value      = last["portfolio_value"]
        cumulative_pnl  = last["cumulative_pnl"]
        max_equity_ever = last.get("max_equity_ever", prev_value)

    # 오늘 일별 수익 추정 (추천 볼트 apr_30d 기반, 일 단위)
    daily_return_frac = 0.0
    for v in recommendations:
        weight  = v.get("suggested_allocation", 0) / 100.0
        apr_30d = v.get("apr_30d", 0) / 100.0   #  % → decimal
        daily   = apr_30d / 365.0               # 연 → 일
        daily_return_frac += weight * daily

    new_value       = prev_value * (1.0 + daily_return_frac)
    daily_pnl       = new_value - prev_value
    cumulative_pnl  = new_value - initial_capital
    max_equity_ever = max(max_equity_ever, new_value)
    mdd_pct         = (max_equity_ever - new_value) / max_equity_ever * 100 if max_equity_ever > 0 else 0.0
    risk_score      = calc_portfolio_risk_score(recommendations)

    history[date_str] = {
        "portfolio_value":   round(new_value, 2),
        "daily_pnl":         round(daily_pnl, 2),
        "daily_return_pct":  round(daily_return_frac * 100, 4),
        "cumulative_pnl":    round(cumulative_pnl, 2),
        "cumulative_pct":    round((new_value / initial_capital - 1) * 100, 4),
        "max_equity_ever":   round(max_equity_ever, 2),
        "mdd_pct":           round(mdd_pct, 4),
        "risk_score":        risk_score,
        "n_vaults":          len(recommendations),
        "vaults": [
            {
                "name":       v.get("name", "")[:30],
                "address":    v.get("address", ""),
                "alloc_pct":  v.get("suggested_allocation", 0),
                "apr_30d":    v.get("apr_30d", 0),
                "robustness": v.get("robustness_score", 0),
                "undervalue": v.get("undervalue_score", 1.0),
                "leader_eq":  v.get("leader_equity_ratio", 0),
            }
            for v in recommendations
        ]
    }
    save_portfolio_history(history)
    print(f"  [추적] {date_str} | 가치 ${new_value:,.0f} | "
          f"누적PnL ${cumulative_pnl:+,.0f} ({cumulative_pnl / initial_capital * 100:+.2f}%) | "
          f"MDD {mdd_pct:.2f}% | 리스크 {risk_score:.2f}")
    return history


def get_portfolio_summary(history=None):
    """
    ★ 포트폴리오 이력 요약 통계
    반환: 일별 시계열 + 요약 지표
    """
    if history is None:
        history = load_portfolio_history()
    if not history:
        return {"error": "포트폴리오 이력 없음. 먼저 분석을 실행하세요."}

    sorted_dates = sorted(history.keys())
    first = history[sorted_dates[0]]
    last  = history[sorted_dates[-1]]

    values     = [history[d]["portfolio_value"] for d in sorted_dates]
    mdd_values = [history[d]["mdd_pct"]         for d in sorted_dates]
    risk_vals  = [history[d]["risk_score"]       for d in sorted_dates]
    pnl_vals   = [history[d]["daily_pnl"]        for d in sorted_dates]

    # Sharpe (일별 수익기준)
    daily_rets = np.array([history[d]["daily_return_pct"] / 100 for d in sorted_dates])
    sharpe = float((daily_rets.mean() / daily_rets.std() * np.sqrt(252))
                   if daily_rets.std() > 1e-8 else 0)

    return {
        "first_date":       sorted_dates[0],
        "last_date":        sorted_dates[-1],
        "tracking_days":    len(sorted_dates),
        "initial_capital":  first["portfolio_value"],
        "current_value":    last["portfolio_value"],
        "cumulative_pnl":   last["cumulative_pnl"],
        "cumulative_pct":   last["cumulative_pct"],
        "peak_value":       round(max(values), 2),
        "current_mdd_pct":  last["mdd_pct"],
        "max_mdd_pct":      round(max(mdd_values), 4),
        "avg_risk_score":   round(float(np.mean(risk_vals)), 4),
        "current_risk":     last["risk_score"],
        "sharpe_ratio":     round(sharpe, 3),
        # 시계열 (대시보드/웹 시각화용)
        "value_series":     [(d, history[d]["portfolio_value"]) for d in sorted_dates],
        "mdd_series":       [(d, history[d]["mdd_pct"])         for d in sorted_dates],
        "risk_series":      [(d, history[d]["risk_score"])      for d in sorted_dates],
        "daily_pnl_series": [(d, history[d]["daily_pnl"])       for d in sorted_dates],
    }

# ── 메인 분석 ─────────────────────────────────────────────────────────────────
def run_portfolio_analysis(top_k=25, max_corr=0.55, min_pts=8, max_pts=90, addresses=None, snapshot_date=None):
    """전체 포트폴리오 분석 실행. addresses가 주어지면 해당 주소 볼트만 분석. snapshot_date가 주어지면 해당 날짜 스냅샷 사용."""
    if snapshot_date:
        vaults, date = load_snapshot_by_date(snapshot_date)
    else:
        vaults, date = load_latest_snapshot()
    if not vaults:
        return {"error": f"스냅샷 없음 ({snapshot_date or 'latest'}). 먼저 분석을 실행하세요."}

    print(f"  [PE] 스냅샷: {len(vaults)}개 볼트 ({date})")

    # ★ 사용자 선택 주소가 있으면 해당 볼트만 필터
    if addresses:
        addr_set = set(addresses)
        vaults = [v for v in vaults if v.get("address", "") in addr_set]
        print(f"  [PE] 사용자 선택 볼트: {len(vaults)}개 (요청: {len(addr_set)}개)")

    # alltime_pnl 있는 볼트만
    valid = [v for v in vaults
             if v.get("alltime_pnl") and len(v.get("alltime_pnl", [])) >= min_pts]
    print(f"  [PE] PnL 데이터 유효 볼트: {len(valid)}개")

    # ★ 기본 필터 (요구사항 기준):
    #   - 입금 가능 (allowDeposits)
    #   - 리더 에쿼티 >= 40% (skin-in-the-game)
    #   - MDD 제한 없음 (요구사항 4번)
    MIN_LEADER_EQ = 0.40
    filter_details = []
    for v in valid:
        ok_deposit  = v.get("allow_deposits", True)
        ok_leader   = v.get("leader_equity_ratio", 0) >= MIN_LEADER_EQ
        # 리더 에쿼티 데이터가 없는 경우(0.0) → 데이터 부족으로 일단 통과
        leader_ratio = v.get("leader_equity_ratio", -1)
        ok_leader_pass = (leader_ratio < 0 or leader_ratio >= MIN_LEADER_EQ)
        # 사용자가 직접 선택한 볼트는 필터 무조건 통과
        user_selected = bool(addresses)
        filter_details.append({
            **v,
            "_ok_deposit":     ok_deposit,
            "_ok_leader":      ok_leader,
            "_leader_ratio":   leader_ratio,
            "_filter_pass":    user_selected or (ok_deposit and ok_leader_pass),
        })

    filtered = [v for v in filter_details if v["_filter_pass"]]
    if not addresses and len(filtered) < 5:
        filtered = [v for v in filter_details if v.get("allow_deposits", True)]
        print(f"  [PE] 리더에쿼티 데이터 부족 → 입금가능 폴백: {len(filtered)}개")
    print(f"  [PE] 기본 필터 통과: {len(filtered)}개 {'(사용자 선택 모드)' if addresses else f'(입금가능+리더에쿼티≥{MIN_LEADER_EQ:.0%})'}")

    # 수익률 행렬
    all_sel, R = build_returns_matrix(filtered, min_pts, max_pts)
    print(f"  [PE] 수익률 행렬: {R.shape}")
    if R.shape[0] < 2:
        return {"error": "수익률 데이터 부족 (alltime_pnl 저장 후 재실행 필요)"}

    # 상관관계
    corr = calc_corr(R)

    # 저상관 볼트 선택
    sel_vaults, sel_idx, sel_R = select_low_corr_vaults(
        all_sel, R, corr, top_k=top_k, max_corr=max_corr)
    if len(sel_vaults) < 2:
        sel_vaults, sel_idx = all_sel[:top_k], list(range(min(top_k, len(all_sel))))
        sel_R = R[:len(sel_vaults)]
    names = [v["name"] for v in sel_vaults]
    sel_corr = corr[np.ix_(sel_idx, sel_idx)]
    print(f"  [PE] 저상관 선택: {len(sel_vaults)}개")

    # 4가지 최적화
    w_sh, st_sh = optimize_max_sharpe(sel_R, names)
    w_mv, st_mv = optimize_min_variance(sel_R, names)
    w_rp, st_rp = optimize_risk_parity(sel_R, names)
    w_cv, st_cv = optimize_min_cvar(sel_R, names)

    # 백테스팅
    bt_sh = backtest(w_sh, sel_R)
    bt_mv = backtest(w_mv, sel_R)
    bt_rp = backtest(w_rp, sel_R)
    bt_cv = backtest(w_cv, sel_R)

    # 전체 필터 볼트 상관관계 (상위 20개)
    top20     = all_sel[:20]
    top20_idx = list(range(min(20, len(all_sel))))
    top20_corr= corr[np.ix_(top20_idx, top20_idx)]
    top20_names=[v["name"] for v in top20]

    # 히스토리 로드
    history, hist_dates = load_all_history(max_days=90)

    # ★ 포트폴리오 이력 요약 (portfolio_history.json 기반)
    pf_history = load_portfolio_history()
    pf_summary = get_portfolio_summary(pf_history) if pf_history else {}

    return {
        "date":        date,
        "n_total":     len(vaults),
        "n_valid":     len(valid),
        "n_filtered":  len(filtered),
        "n_analyzed":  R.shape[0],
        "n_selected":  len(sel_vaults),
        "analysis_days": R.shape[1],

        # 저상관 선택 볼트
        "selected_vaults": [
            {
                "address":            v["address"],
                "name":               v["name"],
                "tvl":                v["tvl"],
                "apr_30d":            v.get("apr_30d", 0),
                "sharpe_ratio":       v.get("sharpe_ratio", 0),
                "max_drawdown":       v.get("max_drawdown", 0),
                "robustness_score":   v.get("robustness_score", 0),
                "equity_curve_grade": v.get("equity_curve_grade", "-"),
                "score":              v.get("score", 0),
                "alloc_sh": round(float(w_sh[i]) * 100, 1),
                "alloc_mv": round(float(w_mv[i]) * 100, 1),
                "alloc_rp": round(float(w_rp[i]) * 100, 1),
                "alloc_cv": round(float(w_cv[i]) * 100, 1),
            }
            for i, v in enumerate(sel_vaults)
        ],

        # 상관관계 행렬 (선택 볼트)
        "corr_selected": {
            "names":  names,
            "matrix": [[round(float(sel_corr[i, j]), 3) for j in range(len(names))]
                       for i in range(len(names))]
        },

        # 전체 상위 20 상관관계
        "corr_top20": {
            "names":  top20_names,
            "matrix": [[round(float(top20_corr[i, j]), 3) for j in range(len(top20_names))]
                       for i in range(len(top20_names))]
        },

        # 4가지 포트폴리오
        "portfolios": {
            "max_sharpe":   {"label": "최대 샤프",   "emoji": "📈", "stats": st_sh, "backtest": bt_sh},
            "min_variance": {"label": "최소 분산",   "emoji": "🛡️", "stats": st_mv, "backtest": bt_mv},
            "risk_parity":  {"label": "위험 균형",   "emoji": "⚖️", "stats": st_rp, "backtest": bt_rp},
            "min_cvar":     {"label": "원금보호(CVaR)","emoji":"🔒", "stats": st_cv, "backtest": bt_cv},
        },

        # 히스토리 요약 (추적관리 데이터)
        "history_days":   len(hist_dates),
        "history_dates":  hist_dates,
        "history_vaults": len(history),

        # ★ 포트폴리오 타임프레임 추적 (요구사항 9번)
        "portfolio_history_days": len(pf_history),
        "portfolio_summary":      pf_summary,

        # ★ 200개 볼트 전체 필터 결과 (필터 통과/탈락 이유 포함)
        "filter_details": [
            {
                "rank":              v.get("rank", 0),
                "name":              v.get("name", "")[:40],
                "address":           v.get("address", ""),
                "tvl":               v.get("tvl", 0),
                "apr_30d":           v.get("apr_30d", 0),
                "sharpe_ratio":      v.get("sharpe_ratio", 0),
                "max_drawdown":      v.get("max_drawdown", 0),
                "robustness_score":  v.get("robustness_score", 0),
                "equity_curve_grade":v.get("equity_curve_grade", "-"),
                "allow_deposits":    v.get("allow_deposits", True),
                "leader_equity_ratio": v.get("leader_equity_ratio", -1),
                "leader_equity_usd": v.get("leader_equity_usd", 0),
                "score":             v.get("score", 0),
                "data_points":       len(v.get("alltime_pnl", [])),
                "_ok_deposit":       v.get("_ok_deposit", True),
                "_ok_leader":        v.get("_ok_leader", False),
                "_filter_pass":      v.get("_filter_pass", False),
            }
            for v in filter_details
        ],
    }


if __name__ == "__main__":
    result = run_portfolio_analysis()
    if "error" in result:
        print("오류:", result["error"])
    else:
        print(f"\n분석 완료: {result['date']}")
        print(f"전체: {result['n_total']}개 → 필터: {result['n_filtered']}개 → 선택: {result['n_selected']}개")
        print(f"분석 기간: {result['analysis_days']}일")
        print("\n=== 포트폴리오 비교 ===")
        for key, pf in result["portfolios"].items():
            bt = pf["backtest"]
            st = pf["stats"]
            print(f"\n{pf['emoji']} {pf['label']}")
            print(f"  연수익: {st['annual_return_pct']:.1f}%  변동성: {st['annual_vol_pct']:.1f}%  Sharpe: {st['sharpe']:.2f}")
            print(f"  백테스팅: ${bt.get('final_value',0):,.0f} (수익: ${bt.get('total_profit',0):,.0f}) MDD: {bt.get('max_drawdown_pct',0):.1f}%")
