#!/usr/bin/env python3
"""
scheduler.py — Hyperliquid Portfolio 자동 스케줄러
====================================================
매일 오전 9시 자동 분석 + 리밸런싱 알림 + 긴급중단 감지

실행:
  python scheduler.py          # 계속 실행 (매일 09:00 자동 분석)
  python scheduler.py --now    # 즉시 1회 실행 후 종료
  python scheduler.py --stop   # 긴급 중단 플래그 설정

긴급 중단:
  emergency_stop.flag 파일 생성 → 즉시 분석 중단
  또는 python scheduler.py --stop
"""

import os, sys, json, time, logging, argparse, subprocess
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 설정 ──────────────────────────────────────────────────────────────────────
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "vault_data"
SNAPSHOTS_DIR  = DATA_DIR / "snapshots"
REPORTS_DIR    = DATA_DIR / "reports"
LOG_DIR        = DATA_DIR / "logs"
PORTFOLIO_FILE = DATA_DIR / "my_portfolio.json"   # 내 현재 포트폴리오
STATUS_FILE    = DATA_DIR / "status.json"          # 대시보드용 상태
STOP_FLAG      = BASE_DIR / "emergency_stop.flag"  # 긴급 중단 트리거

SCHEDULE_HOUR   = 9    # 오전 9시
SCHEDULE_MINUTE = 0

# ── 로깅 설정 ─────────────────────────────────────────────────────────────────
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "scheduler.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("scheduler")


# ── 긴급 중단 ─────────────────────────────────────────────────────────────────
def is_emergency_stopped() -> bool:
    return STOP_FLAG.exists()


def set_emergency_stop(reason: str = "Manual stop"):
    STOP_FLAG.write_text(
        json.dumps({"reason": reason, "time": datetime.now().isoformat()}),
        encoding="utf-8"
    )
    log.warning(f"🔴 긴급 중단 플래그 설정: {reason}")
    _update_status({"emergency": True, "emergency_reason": reason})


def clear_emergency_stop():
    if STOP_FLAG.exists():
        STOP_FLAG.unlink()
    log.info("✅ 긴급 중단 플래그 해제")
    _update_status({"emergency": False, "emergency_reason": None})


# ── 상태 파일 ─────────────────────────────────────────────────────────────────
def _update_status(patch: dict):
    """대시보드가 읽는 status.json 업데이트 (부분 업데이트)"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    status.update(patch)
    status["last_updated"] = datetime.now().isoformat()
    STATUS_FILE.write_text(
        json.dumps(status, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8"
    )


def load_status() -> dict:
    if STATUS_FILE.exists():
        try:
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def load_portfolio() -> dict:
    """내 포트폴리오 로드: {vault_address: invested_usd}"""
    if PORTFOLIO_FILE.exists():
        try:
            return json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_portfolio(portfolio: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PORTFOLIO_FILE.write_text(
        json.dumps(portfolio, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


# ── 분석 실행 ─────────────────────────────────────────────────────────────────
def run_analysis() -> dict:
    """analyze_top_vaults.py 실행 → 결과 스냅샷 반환"""
    if is_emergency_stopped():
        log.warning("🔴 긴급 중단 상태 — 분석 스킵")
        return {}

    log.info("=" * 55)
    log.info("📊 일일 볼트 분석 시작")
    log.info("=" * 55)

    _update_status({"running": True, "last_run_start": datetime.now().isoformat()})

    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "analyze_top_vaults.py"), "--force"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        if result.returncode != 0:
            log.error(f"분석 실패 (returncode={result.returncode})")
            log.error(result.stderr[:500] if result.stderr else "")
            _update_status({"running": False, "last_run_status": "FAILED"})
            return {}

        log.info("✅ 분석 완료")

        # 최신 스냅샷 로드
        import glob
        snaps = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")), reverse=True)
        if not snaps:
            return {}
        with open(snaps[0], encoding="utf-8") as f:
            vaults = json.load(f)

        date_str = Path(snaps[0]).stem
        _update_status({
            "running": False,
            "last_run_status": "OK",
            "last_run_date": date_str,
            "vault_count": len(vaults),
        })
        return {"vaults": vaults, "date": date_str}

    except subprocess.TimeoutExpired:
        log.error("❌ 분석 타임아웃 (10분 초과)")
        _update_status({"running": False, "last_run_status": "TIMEOUT"})
        return {}
    except Exception as e:
        log.error(f"❌ 분석 오류: {e}")
        _update_status({"running": False, "last_run_status": f"ERROR: {e}"})
        return {}


# ── 포트폴리오 평가 ───────────────────────────────────────────────────────────
def evaluate_portfolio(vaults: list, portfolio: dict) -> dict:
    """
    현재 내 포트폴리오의 성과 평가 + 리밸런싱 필요 여부 판단

    Returns:
        {
          "total_invested": float,
          "estimated_value": float,
          "unrealized_pnl": float,
          "holdings": [...],
          "needs_rebalance": bool,
          "rebalance_reason": str,
          "withdrawal_plan": [...]   ← D-1 출금 예정 목록
        }
    """
    if not vaults or not portfolio:
        return {}

    vault_map = {v["address"]: v for v in vaults}
    total_invested = sum(portfolio.values())

    # 보유 볼트 평가
    holdings = []
    total_monthly_return = 0.0
    has_danger = False

    for addr, invested_usd in portfolio.items():
        v = vault_map.get(addr, {})
        apr_30d = v.get("apr_30d", 0)
        mdd     = v.get("max_drawdown", 0)
        name    = v.get("name", addr[:12] + "...")
        monthly_est = invested_usd * apr_30d / 100 / 12
        total_monthly_return += monthly_est

        # 위험 감지: MDD > 20% or APR < 0
        danger = mdd > 20 or apr_30d < 0 or not v.get("allow_deposits", True)
        if danger:
            has_danger = True

        holdings.append({
            "address":       addr,
            "name":          name,
            "invested_usd":  round(invested_usd, 2),
            "pct":           round(invested_usd / total_invested * 100, 1) if total_invested else 0,
            "apr_30d":       apr_30d,
            "mdd":           mdd,
            "monthly_est":   round(monthly_est, 2),
            "danger":        danger,
            "allow_deposits": v.get("allow_deposits", True),
            "robustness":    v.get("robustness_score", 0),
        })

    # 리밸런싱 필요 여부 판단
    needs_rebalance = False
    rebalance_reason = ""

    if has_danger:
        needs_rebalance = True
        rebalance_reason = "🔴 위험 볼트 발견 (MDD>20% or APR<0)"

    # 최적 포트폴리오와 비중 차이가 10% 이상인 볼트 있으면 리밸런싱
    from analyze_top_vaults import get_recommendations
    recs = get_recommendations(vaults, top_k=15)
    rec_map = {r["address"]: r for r in recs}

    for h in holdings:
        target_pct = rec_map.get(h["address"], {}).get("suggested_allocation", 0)
        if abs(h["pct"] - target_pct) > 10:
            needs_rebalance = True
            rebalance_reason = rebalance_reason or f"📊 {h['name']} 비중 조정 권고 ({h['pct']:.1f}% → {target_pct:.1f}%)"

    # D-1 출금 계획 (리밸런싱 권고 시 — 내일 리밸런싱이면 오늘 출금 시작해야 함)
    withdrawal_plan = []
    if needs_rebalance:
        for h in holdings:
            target_pct = rec_map.get(h["address"], {}).get("suggested_allocation", 0)
            current_pct = h["pct"]
            if current_pct - target_pct > 5:  # 비중 줄여야 하는 볼트
                reduce_usd = (current_pct - target_pct) / 100 * total_invested
                withdrawal_plan.append({
                    "address":    h["address"],
                    "name":       h["name"],
                    "action":     "WITHDRAW",
                    "amount_usd": round(reduce_usd, 2),
                    "reason":     f"비중 {current_pct:.1f}% → {target_pct:.1f}% 축소",
                    "deadline":   "⚠️ 오늘 출금 신청 필요 (1일 지연)",
                })

    result = {
        "total_invested":       round(total_invested, 2),
        "estimated_monthly":    round(total_monthly_return, 2),
        "estimated_annual":     round(total_monthly_return * 12, 2),
        "holdings":             holdings,
        "needs_rebalance":      needs_rebalance,
        "rebalance_reason":     rebalance_reason,
        "withdrawal_plan":      withdrawal_plan,
        "recommendations":      recs[:15],
        "evaluated_at":         datetime.now().isoformat(),
    }

    _update_status({
        "portfolio_eval": result,
        "total_invested": total_invested,
        "needs_rebalance": needs_rebalance,
        "rebalance_reason": rebalance_reason,
    })

    return result


# ── 알림 로그 ─────────────────────────────────────────────────────────────────
def send_alert(title: str, message: str, level: str = "INFO"):
    """
    알림 전송 (현재: 로그 파일 + status.json)
    향후 확장: 텔레그램, 이메일, Slack 등
    """
    alert = {
        "time":    datetime.now().isoformat(),
        "level":   level,
        "title":   title,
        "message": message,
    }

    # 로그
    fn = getattr(log, level.lower(), log.info)
    fn(f"🔔 [{title}] {message}")

    # status.json에 최근 알림 5개 유지
    status = load_status()
    alerts = status.get("recent_alerts", [])
    alerts.insert(0, alert)
    alerts = alerts[:5]
    _update_status({"recent_alerts": alerts})

    # 알림 파일 기록
    alert_file = DATA_DIR / "alerts.jsonl"
    with open(alert_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(alert, ensure_ascii=False) + "\n")


# ── 일일 작업 ─────────────────────────────────────────────────────────────────
def daily_job():
    """매일 실행되는 핵심 작업"""
    if is_emergency_stopped():
        log.warning("🔴 긴급 중단 상태 — 일일 작업 스킵")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    log.info(f"🗓️ 일일 작업 시작 ({today})")

    # 1. 분석 실행
    result = run_analysis()
    if not result:
        send_alert("분석 실패", "오늘 볼트 분석에 실패했습니다.", "ERROR")
        return

    vaults = result["vaults"]

    # 2. 포트폴리오 평가
    portfolio = load_portfolio()
    if portfolio:
        eval_result = evaluate_portfolio(vaults, portfolio)

        total = eval_result.get("total_invested", 0)
        monthly = eval_result.get("estimated_monthly", 0)
        log.info(f"💰 포트폴리오: ${total:,.0f} 투자 | 예상 월수익: ${monthly:,.0f}")

        # 위험 알림
        if eval_result.get("needs_rebalance"):
            reason = eval_result.get("rebalance_reason", "")
            send_alert("리밸런싱 권고", reason, "WARNING")

            # D-1 출금 알림
            wp = eval_result.get("withdrawal_plan", [])
            if wp:
                details = "\n".join(
                    f"  - {w['name']}: ${w['amount_usd']:,.0f} ({w['reason']})"
                    for w in wp
                )
                send_alert(
                    "⚠️ 오늘 출금 신청 필요",
                    f"리밸런싱 D-1:\n{details}",
                    "WARNING"
                )
        else:
            send_alert("포트폴리오 정상", f"총 투자: ${total:,.0f} | 예상 월수익: ${monthly:,.0f}", "INFO")
    else:
        log.info("⚠️ 포트폴리오 미설정 — vault_data/my_portfolio.json 에 투자 현황 입력하세요")
        send_alert(
            "포트폴리오 미설정",
            "vault_data/my_portfolio.json 파일에 투자 현황을 입력하세요.\n"
            '예: {"0xVaultAddress": 5000}  (주소: 투자금액)',
            "INFO"
        )

    # 3. 30일 리밸런싱 카운트다운
    status = load_status()
    last_rebalance = status.get("last_rebalance_date")
    if last_rebalance:
        days_since = (datetime.now() - datetime.fromisoformat(last_rebalance)).days
        days_left  = max(0, 30 - days_since)
        _update_status({"days_to_rebalance": days_left})
        if days_left <= 2:
            send_alert(
                f"리밸런싱 D-{days_left}",
                f"30일 리밸런싱 예정일까지 {days_left}일 남았습니다. 출금 준비 필요.",
                "WARNING"
            )
    else:
        _update_status({
            "last_rebalance_date": today,
            "days_to_rebalance": 30
        })

    log.info(f"✅ 일일 작업 완료 ({today})")


# ── 스케줄러 메인 루프 ────────────────────────────────────────────────────────
def run_scheduler():
    log.info("🚀 Hyperliquid Portfolio 스케줄러 시작")
    log.info(f"   매일 {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} 자동 분석")
    log.info(f"   긴급 중단: python scheduler.py --stop")
    log.info(f"   또는 emergency_stop.flag 파일 생성")

    _update_status({"scheduler_running": True, "emergency": False})

    while True:
        if is_emergency_stopped():
            log.warning("🔴 긴급 중단 감지 — 스케줄러 종료")
            _update_status({"scheduler_running": False})
            break

        now = datetime.now()
        next_run = now.replace(
            hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, second=0, microsecond=0
        )
        if next_run <= now:
            next_run += timedelta(days=1)

        wait_sec = (next_run - now).total_seconds()
        log.info(f"⏳ 다음 실행: {next_run.strftime('%Y-%m-%d %H:%M')} (대기 {wait_sec/3600:.1f}시간)")
        _update_status({"next_run": next_run.isoformat()})

        # 1분마다 긴급 중단 플래그 확인하면서 대기
        while wait_sec > 0:
            sleep_time = min(60, wait_sec)
            time.sleep(sleep_time)
            wait_sec -= sleep_time
            if is_emergency_stopped():
                log.warning("🔴 긴급 중단 감지 — 대기 중단")
                _update_status({"scheduler_running": False})
                return

        daily_job()


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperliquid Portfolio Scheduler")
    parser.add_argument("--now",   action="store_true", help="즉시 1회 실행")
    parser.add_argument("--stop",  action="store_true", help="긴급 중단 플래그 설정")
    parser.add_argument("--clear", action="store_true", help="긴급 중단 플래그 해제")
    parser.add_argument("--status",action="store_true", help="현재 상태 출력")
    args = parser.parse_args()

    if args.stop:
        set_emergency_stop("CLI --stop command")
        print("🔴 긴급 중단 완료. 웹 대시보드에서도 확인 가능합니다.")
    elif args.clear:
        clear_emergency_stop()
        print("✅ 긴급 중단 해제 완료.")
    elif args.status:
        status = load_status()
        print(json.dumps(status, ensure_ascii=False, indent=2, default=str))
    elif args.now:
        log.info("⚡ 즉시 실행 모드")
        daily_job()
    else:
        run_scheduler()
