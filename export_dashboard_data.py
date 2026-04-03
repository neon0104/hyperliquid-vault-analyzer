#!/usr/bin/env python3
"""
export_dashboard_data.py  v2.0
===============================
Flask 대시보드(web_dashboard.py)의 **전체 기능**을 GitHub Pages 정적 사이트에서
동일하게 제공하기 위한 종합 JSON 데이터 내보내기.

출력: docs/data.json
"""
import json, os, glob, sys
import numpy as np
from datetime import datetime
from pathlib import Path

BASE_DIR       = Path(__file__).parent
SNAPSHOTS_DIR  = BASE_DIR / "vault_data" / "snapshots"
PORTFOLIO_FILE = BASE_DIR / "my_portfolio.json"
PORTFOLIO_CFG  = BASE_DIR / "my_portfolio_config.json"
OUT_FILE       = BASE_DIR / "docs" / "data.json"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 스냅샷 로드 ────────────────────────────────────────────────────────
def load_snapshots():
    """최신 + 이전 스냅샷 로드, 볼트 히스토리 수집"""
    files = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")), reverse=True)
    if not files:
        return [], None, {}, None, {}

    with open(files[0], encoding="utf-8") as f:
        latest = json.load(f)
        latest_date = Path(files[0]).stem

    prev_vaults, prev_date = {}, None
    if len(files) > 1:
        try:
            with open(files[1], encoding="utf-8") as f:
                prev_data = json.load(f)
                prev_date = Path(files[1]).stem
                for i, p in enumerate(prev_data):
                    p["rank"] = p.get("rank", i + 1)
                    prev_vaults[p["address"]] = p
        except Exception:
            pass

    vault_hist = {}
    for fp in reversed(files):
        dt = Path(fp).stem
        try:
            with open(fp, encoding="utf-8") as fd:
                data = json.load(fd)
                for v in data:
                    addr = v["address"]
                    if addr not in vault_hist:
                        vault_hist[addr] = {"dates": [], "mdd": [], "sharpe": [], "robust": [], "score": []}
                    vault_hist[addr]["dates"].append(dt[5:])
                    vault_hist[addr]["mdd"].append(v.get("max_drawdown", 0))
                    vault_hist[addr]["sharpe"].append(v.get("sharpe_ratio", 0))
                    vault_hist[addr]["robust"].append(v.get("robustness_score", 0))
                    vault_hist[addr]["score"].append(v.get("score", 0))
        except Exception:
            pass

    return latest, latest_date, prev_vaults, prev_date, vault_hist


def build_vault_changes(v, prev_vaults):
    """이전 스냅샷 대비 변화 계산"""
    if v["address"] not in prev_vaults:
        return False, {}, {}

    p = prev_vaults[v["address"]]
    cr = p["rank"] - v["rank"]
    cs = round(v.get("score", 0) - p.get("score", 0), 3)
    cm = round(v.get("max_drawdown", 0) - p.get("max_drawdown", 0), 2)
    cp = round(v.get("pnl_alltime", 0) - p.get("pnl_alltime", 0), 2)
    cv = round(v.get("tvl", 0) - p.get("tvl", 0), 2)
    ce = round((v.get("leader_equity_ratio", 0) - p.get("leader_equity_ratio", 0)) * 100, 2)
    csh = round(v.get("sharpe_ratio", 0) - p.get("sharpe_ratio", 0), 3)

    def d(val): return "up" if val > 0 else "down" if val < 0 else "same"

    chg = {
        "rank_val": abs(cr), "rank_dir": d(cr),
        "score_val": abs(cs), "score_dir": d(cs),
        "mdd_val": abs(cm), "mdd_dir": d(cm),
        "pnl_val": abs(cp), "pnl_dir": d(cp),
        "tvl_val": abs(cv), "tvl_dir": d(cv),
        "eq_val": abs(ce), "eq_dir": d(ce),
        "sharpe_val": abs(csh), "sharpe_dir": d(csh),
    }

    def pt(c_val, pr_val):
        return round((c_val - pr_val) / abs(pr_val) * 100, 2) if pr_val != 0 else 0

    chg_pct = {
        "tvl": pt(v.get("tvl", 0), p.get("tvl", 0)),
        "eq": pt(v.get("leader_equity_ratio", 0), p.get("leader_equity_ratio", 0)),
        "pnl": pt(v.get("pnl_alltime", 0), p.get("pnl_alltime", 0)),
        "mdd": pt(v.get("max_drawdown", 0), p.get("max_drawdown", 0)),
        "sharpe": pt(v.get("sharpe_ratio", 0), p.get("sharpe_ratio", 0)),
        "score": pt(v.get("score", 0), p.get("score", 0)),
    }
    return True, chg, chg_pct


# ── 포트폴리오 분석 (pre-compute) ──────────────────────────────────────
def run_portfolio_for_date(snapshot_date=None):
    """특정 날짜 스냅샷으로 포트폴리오 분석 실행"""
    try:
        from portfolio_engine import run_portfolio_analysis
        return run_portfolio_analysis(top_k=25, max_corr=0.55, snapshot_date=snapshot_date)
    except Exception as e:
        print(f"  [WARN] Portfolio analysis failed ({snapshot_date}): {e}")
        return None


def get_valid_snapshot_dates():
    """유효한 스냅샷 날짜 목록 반환 (손상 파일 제외)"""
    files = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")))
    valid = []
    for f in files:
        size = os.path.getsize(f)
        if size < 50000:  # 50KB 미만은 손상/부분 데이터
            print(f"  [Export] Skipping {Path(f).stem} (size: {size:,}B - damaged/partial)")
            continue
        valid.append(Path(f).stem)
    return valid


def export_portfolio_result(portfolio_data, slim=False):
    """포트폴리오 분석 결과를 JSON 내보내기용 dict로 변환. slim=True이면 큰 데이터 생략."""
    if not portfolio_data or "error" in portfolio_data:
        return None
    pf = portfolio_data
    result = {
        "date": pf.get("date", ""),
        "n_total": pf.get("n_total", 0),
        "n_valid": pf.get("n_valid", 0),
        "n_filtered": pf.get("n_filtered", 0),
        "n_analyzed": pf.get("n_analyzed", 0),
        "n_selected": pf.get("n_selected", 0),
        "analysis_days": pf.get("analysis_days", 0),
        "selected_vaults": pf.get("selected_vaults", []),
        "corr_selected": pf.get("corr_selected", {}),
        "portfolios": {},
    }
    # 전체 데이터는 최신 날짜에만 포함 (파일 크기 절약)
    if not slim:
        result["history_dates"] = pf.get("history_dates", [])
        result["portfolio_summary"] = pf.get("portfolio_summary", {})
        result["filter_details"] = [
            {
                "name": fd.get("name", ""),
                "address": fd.get("address", ""),
                "apr_30d": fd.get("apr_30d", 0),
                "max_drawdown": fd.get("max_drawdown", 0),
            }
            for fd in pf.get("filter_details", [])
        ]
    for key, p in pf.get("portfolios", {}).items():
        result["portfolios"][key] = {
            "label": p.get("label", ""),
            "emoji": p.get("emoji", ""),
            "stats": p.get("stats", {}),
            "backtest": p.get("backtest", {}),
        }
    return result


# ── 내 포트폴리오 ──────────────────────────────────────────────────────
def load_my_portfolio(vault_map):
    """내 포트폴리오 보유 현황"""
    if not PORTFOLIO_FILE.exists():
        return {}

    try:
        with open(PORTFOLIO_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {}

    # Load config for invest_date
    invest_date = None
    if PORTFOLIO_CFG.exists():
        try:
            with open(PORTFOLIO_CFG, encoding="utf-8") as f:
                cfg = json.load(f)
                invest_date = cfg.get("invest_date")
        except Exception:
            pass

    positions = raw.get("positions", {}) if isinstance(raw, dict) else {}

    holdings = []
    total_invested = 0
    for addr, usd in positions.items():
        usd = float(usd)
        v = vault_map.get(addr, {})
        apr = float(v.get("apr_30d", 0) or 0)
        mdd = float(v.get("max_drawdown", 0) or 0)
        monthly = usd * apr / 100 / 12

        # Calculate days held
        days = 0
        if invest_date:
            try:
                d0 = datetime.strptime(invest_date, "%Y-%m-%d")
                days = (datetime.now() - d0).days
            except Exception:
                pass

        # Estimate PnL based on APR
        pnl = usd * apr / 100 * (days / 365) if days > 0 else 0
        pnl_pct = round(pnl / usd * 100, 2) if usd > 0 else 0

        total_invested += usd
        holdings.append({
            "address": addr,
            "name": v.get("name", addr[:12] + "..."),
            "invested_usd": round(usd, 2),
            "apr_30d": round(apr, 2),
            "mdd": round(mdd, 2),
            "monthly_est": round(monthly, 2),
            "robustness": round(v.get("robustness_score", 0), 3),
            "grade": v.get("equity_curve_grade", "-"),
            "pnl": round(pnl, 2),
            "pnl_pct": pnl_pct,
            "days_held": days,
            "danger": mdd > 20 or apr < 0,
        })

    for h in holdings:
        h["weight_pct"] = round(h["invested_usd"] / total_invested * 100, 1) if total_invested else 0

    net_pnl_total = sum(h["pnl"] * 0.9 if h["pnl"] > 0 else h["pnl"] for h in holdings)
    gross_pnl = sum(h["pnl"] for h in holdings)

    return {
        "holdings": holdings,
        "total_invested": round(total_invested, 2),
        "gross_pnl": round(gross_pnl, 2),
        "gross_pnl_pct": round(gross_pnl / total_invested * 100, 2) if total_invested else 0,
        "net_pnl": round(net_pnl_total, 2),
        "net_pnl_pct": round(net_pnl_total / total_invested * 100, 2) if total_invested else 0,
        "days_held": holdings[0]["days_held"] if holdings else 0,
        "needs_rebalance": any(h["danger"] for h in holdings),
    }


# ── 메인 ──────────────────────────────────────────────────────────────
def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    vaults, date_str, prev_vaults, prev_date, vault_hist = load_snapshots()
    if not vaults:
        print("No snapshots found.")
        return

    print(f"  [Export] {len(vaults)} vaults from {date_str}")

    # ── 볼트 데이터 가공 (Flask 대시보드와 동일) ──
    vault_map = {}
    export_vaults = []
    for i, v in enumerate(vaults):
        v["rank"] = v.get("rank", i + 1)

        # alltime ROI
        if v.get("apr_pct") and v.get("age_days"):
            v["alltime_roi_pct"] = round(v.get("apr_pct", 0) * (v.get("age_days", 0) / 365.0), 1)
        else:
            v["alltime_roi_pct"] = 0.0

        has_history, chg, chg_pct = build_vault_changes(v, prev_vaults)
        history = vault_hist.get(v["address"], {})

        # Truncate alltime_pnl for size (keep last 100 points)
        atp = v.get("alltime_pnl", [])
        if len(atp) > 100:
            atp = atp[-100:]

        ev = {
            "rank": v["rank"],
            "name": v.get("name", ""),
            "address": v.get("address", ""),
            "tvl": round(v.get("tvl", 0), 0),
            "leader_equity_ratio": round(v.get("leader_equity_ratio", 0), 4),
            "leader_equity_usd": round(v.get("leader_equity_usd", 0), 0),
            "pnl_alltime": round(v.get("pnl_alltime", 0), 0),
            "alltime_roi_pct": v["alltime_roi_pct"],
            "max_drawdown": round(v.get("max_drawdown", 0), 2),
            "sharpe_ratio": round(v.get("sharpe_ratio", 0), 3),
            "apr_30d": round(v.get("apr_30d", 0), 2),
            "score": round(v.get("score", 0), 3),
            "robustness_score": round(v.get("robustness_score", 0), 3),
            "allow_deposits": v.get("allow_deposits", True),
            "age_days": v.get("age_days", 0),
            "alltime_pnl": [round(float(x), 2) for x in atp],
            "has_history": has_history,
        }
        if has_history:
            ev["chg"] = chg
            ev["chg_pct"] = chg_pct
        if history:
            ev["history"] = history

        # Score breakdown components
        ev["calc_sharpe"] = round(v.get("sharpe_ratio", 0), 3)
        ev["calc_apr"] = round(v.get("apr_30d", 0), 2)
        ev["calc_mdd"] = round(v.get("max_drawdown", 0), 2)
        ev["calc_rob"] = round(v.get("robustness_score", 0), 3)

        export_vaults.append(ev)
        vault_map[v["address"]] = v

    # ── 통계 ──
    avg_mdd = sum(v.get("max_drawdown", 0) for v in vaults) / len(vaults) if vaults else 0
    stats = {
        "total": len(vaults),
        "avg_apr": round(sum(v.get("apr_30d", 0) for v in vaults) / len(vaults), 1) if vaults else 0,
        "avg_mdd": round(avg_mdd, 2),
        "prev_date": prev_date,
    }

    # ── 포트폴리오 분석 (날짜별 사전 계산) ──
    valid_dates = get_valid_snapshot_dates()
    portfolio_by_date = {}
    portfolio_export = None

    print(f"  [Export] Valid snapshot dates: {valid_dates}")
    for snap_date in valid_dates:
        is_latest = (snap_date == date_str)
        print(f"  [Export] Running portfolio analysis for {snap_date}{'  ★ latest' if is_latest else ''}...")
        pf_data = run_portfolio_for_date(snapshot_date=snap_date)
        pf_export_item = export_portfolio_result(pf_data, slim=not is_latest)
        if pf_export_item:
            portfolio_by_date[snap_date] = pf_export_item
            print(f"  [Export] {snap_date}: {pf_export_item.get('n_selected', 0)} vaults, "
                  f"{pf_export_item.get('analysis_days', 0)} data points")
        else:
            print(f"  [Export] {snap_date}: skipped (analysis failed)")

    # 기본 포트폴리오 = 최신 날짜
    if portfolio_by_date:
        latest_key = list(portfolio_by_date.keys())[-1]  # 가장 최근 날짜
        portfolio_export = portfolio_by_date[latest_key]

    # ── 내 포트폴리오 ──
    my_portfolio = load_my_portfolio(vault_map)
    print(f"  [Export] My Portfolio: {len(my_portfolio.get('holdings', []))} holdings")

    # ── 시장 현황 ──
    valid = [v for v in vaults if v.get("data_points", 0) >= 3]
    market = {}
    if valid:
        market = {
            "avg_apr": round(float(np.mean([v["apr_30d"] for v in valid])), 1),
            "median_apr": round(float(np.median([v["apr_30d"] for v in valid])), 1),
            "avg_sharpe": round(float(np.mean([v["sharpe_ratio"] for v in valid])), 2),
            "avg_mdd": round(float(np.mean([v["max_drawdown"] for v in valid])), 1),
            "vault_count": len(vaults),
        }

    # ── 최종 출력 ──
    out = {
        "generated_at": datetime.now().isoformat(),
        "analysis_date": date_str,
        "prev_date": prev_date,
        "stats": stats,
        "vaults": export_vaults,
        "portfolio": portfolio_export,
        "portfolio_by_date": portfolio_by_date,
        "available_dates": valid_dates,
        "my_portfolio": my_portfolio,
        "market": market,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, default=float)

    size_mb = os.path.getsize(OUT_FILE) / 1024 / 1024
    print(f"  [Export] Saved → {OUT_FILE} ({size_mb:.1f} MB)")
    print(f"  [Export] Vaults: {len(export_vaults)}, Portfolio: {'✅' if portfolio_export else '❌'}")


if __name__ == "__main__":
    main()
