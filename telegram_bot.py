#!/usr/bin/env python3
"""
telegram_bot.py — Hyperliquid 볼트 분석기 텔레그램 봇
=====================================================
텔레그램으로 현재 상태, 포트폴리오, 추천 볼트 등을 실시간으로 확인합니다.

설정:
  1) BotFather에서 봇 생성 → BOT_TOKEN 획득
  2) getUpdates로 CHAT_ID 확인
  3) 아래 두 가지 방법 중 하나로 설정:
     a) 환경변수: set TELEGRAM_BOT_TOKEN=... && set TELEGRAM_CHAT_ID=...
     b) telegram_config.json 파일 생성

실행:
  python telegram_bot.py         # 봇 시작 (polling)
  python telegram_bot.py --test  # 테스트 메시지 전송

명령어:
  /status    — 현재 시스템 상태
  /portfolio — 내 포트폴리오 현황
  /vaults    — 추천 볼트 목록
  /alerts    — 최근 알림
  /log       — 최근 실행 로그
  /run       — 즉시 분석 실행
  /stop      — 긴급 중단
  /resume    — 긴급 중단 해제
  /help      — 명령어 목록
"""

import os, sys, json, time, logging, argparse, subprocess, glob, threading
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    print("❌ requests 패키지가 필요합니다: pip install requests")
    sys.exit(1)

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "vault_data"
SNAPSHOTS_DIR   = DATA_DIR / "snapshots"
STATUS_FILE     = DATA_DIR / "status.json"
STOP_FLAG       = BASE_DIR / "emergency_stop.flag"
ALERTS_FILE     = DATA_DIR / "alerts.jsonl"
LOG_FILE        = DATA_DIR / "logs" / "scheduler.log"
CONFIG_FILE     = BASE_DIR / "telegram_config.json"

# ── 로깅 ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("tg_bot")


# ── 설정 로드 ─────────────────────────────────────────────────────────────────
def load_config():
    """BOT_TOKEN, CHAT_ID 로드 (환경변수 우선, 그 다음 telegram_config.json)"""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            token = token or cfg.get("bot_token", "")
            chat_id = chat_id or cfg.get("chat_id", "")
        except Exception:
            pass

    return token.strip(), str(chat_id).strip()


BOT_TOKEN, CHAT_ID = load_config()


# ── Telegram API 헬퍼 ─────────────────────────────────────────────────────────
def tg_request(method: str, payload: dict, timeout: int = 10) -> dict:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        return r.json()
    except Exception as e:
        log.error(f"Telegram API 오류: {e}")
        return {}


def send_message(text: str, chat_id: str = None, parse_mode: str = "HTML") -> bool:
    """텔레그램 메시지 전송"""
    cid = chat_id or CHAT_ID
    if not BOT_TOKEN or not cid:
        log.error("BOT_TOKEN 또는 CHAT_ID 미설정")
        return False

    # 메시지 4096자 제한 분할
    for chunk in _split_message(text):
        result = tg_request("sendMessage", {
            "chat_id": cid,
            "text": chunk,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        })
        if not result.get("ok"):
            log.error(f"전송 실패: {result}")
            return False
    return True


def _split_message(text: str, max_len: int = 4000):
    """긴 메시지를 청크로 분할"""
    if len(text) <= max_len:
        yield text
        return
    lines = text.split("\n")
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > max_len:
            yield chunk
            chunk = line + "\n"
        else:
            chunk += line + "\n"
    if chunk:
        yield chunk


# ── 데이터 로더 ───────────────────────────────────────────────────────────────
def load_status() -> dict:
    try:
        if STATUS_FILE.exists():
            return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def load_latest_snapshot() -> list:
    snaps = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")), reverse=True)
    if not snaps:
        return []
    try:
        with open(snaps[0], encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_recent_alerts(n: int = 5) -> list:
    alerts = []
    try:
        if ALERTS_FILE.exists():
            lines = ALERTS_FILE.read_text(encoding="utf-8").strip().splitlines()
            for line in reversed(lines[-50:]):
                try:
                    alerts.append(json.loads(line))
                except Exception:
                    pass
                if len(alerts) >= n:
                    break
    except Exception:
        pass
    return alerts


def load_recent_log(lines: int = 20) -> str:
    try:
        if LOG_FILE.exists():
            content = LOG_FILE.read_text(encoding="utf-8", errors="replace")
            log_lines = content.strip().splitlines()
            return "\n".join(log_lines[-lines:])
    except Exception:
        pass
    return "(로그 없음)"


# ── 메시지 포맷터 ─────────────────────────────────────────────────────────────
def fmt_status() -> str:
    s = load_status()
    if not s:
        return "⚠️ status.json 없음 — 아직 분석이 실행되지 않았습니다."

    now = datetime.now()
    emergency = s.get("emergency", False) or s.get("emergency_stopped", False)
    running   = s.get("running", False)

    # 시스템 상태
    if emergency:
        state_icon = "🔴"
        state_text = "긴급 중단"
    elif running:
        state_icon = "🔄"
        state_text = "분석 실행 중"
    else:
        state_icon = "✅"
        state_text = "정상 대기"

    last_run  = s.get("last_run_date", "없음")
    next_run  = s.get("next_run", "")
    vault_cnt = s.get("vault_count", 0)
    days_rb   = s.get("days_to_rebalance", "?")

    lines = [
        f"<b>🤖 시스템 상태</b>",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"{state_icon} 상태: <b>{state_text}</b>",
        f"📅 마지막 분석: {last_run}",
        f"⏰ 다음 분석: {_fmt_next_run(next_run)}",
        f"📊 추적 볼트 수: {vault_cnt}개",
        f"🔄 리밸런싱: {days_rb}일 후",
        f"⏱ 조회 시각: {now.strftime('%m/%d %H:%M:%S')}",
    ]

    # 포트폴리오 요약
    total = s.get("total_invested", 0)
    if total:
        monthly = s.get("portfolio_eval", {}).get("estimated_monthly", 0)
        lines += [
            f"",
            f"<b>💰 포트폴리오</b>",
            f"투자금: ${total:,.0f}",
            f"예상 월수익: ${monthly:,.0f}",
        ]
        if s.get("needs_rebalance"):
            lines.append(f"⚠️ {s.get('rebalance_reason', '리밸런싱 권고')}")

    # 최근 알림
    alerts = load_recent_alerts(3)
    if alerts:
        lines.append("")
        lines.append("<b>🔔 최근 알림</b>")
        for a in alerts:
            t = a.get("time", "")[:16].replace("T", " ")
            lvl = "🔴" if a.get("level") == "ERROR" else "⚠️" if a.get("level") == "WARNING" else "ℹ️"
            lines.append(f"{lvl} [{t}] {a.get('title', '')}")

    return "\n".join(lines)


def fmt_portfolio() -> str:
    s = load_status()
    pe = s.get("portfolio_eval", {})
    holdings = pe.get("holdings", [])

    if not holdings:
        return "⚠️ 포트폴리오 데이터 없음\n<code>my_portfolio.json</code>을 설정하고 분석을 실행하세요."

    total    = pe.get("total_invested", 0)
    monthly  = pe.get("estimated_monthly", 0)
    annual   = pe.get("estimated_annual", 0)
    need_rb  = pe.get("needs_rebalance", False)
    rb_reason = pe.get("rebalance_reason", "")
    evaluated = pe.get("evaluated_at", "")[:16].replace("T", " ")

    lines = [
        f"<b>💼 내 포트폴리오</b>",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"💵 총 투자금: <b>${total:,.0f}</b>",
        f"📈 예상 월수익: <b>${monthly:,.0f}</b>",
        f"📊 예상 연수익: <b>${annual:,.0f}</b>",
        f"🕐 평가 시각: {evaluated}",
        f"",
        f"<b>📋 보유 볼트</b>",
    ]

    for h in holdings:
        danger_icon = "🔴" if h.get("danger") else "✅"
        name = h.get("name", "?")[:20]
        pct  = h.get("pct", 0)
        inv  = h.get("invested_usd", 0)
        apr  = h.get("apr_30d", 0)
        mdd  = h.get("mdd", 0)
        lines.append(
            f"{danger_icon} <b>{name}</b> ({pct:.0f}%)\n"
            f"   💵 ${inv:,.0f} | APR {apr:+.1f}% | MDD {mdd:.1f}%"
        )

    if need_rb:
        lines += ["", f"⚠️ <b>리밸런싱 권고</b>", rb_reason]

        wp = pe.get("withdrawal_plan", [])
        if wp:
            lines.append("")
            lines.append("🏦 <b>출금 필요 볼트</b>")
            for w in wp:
                lines.append(f"  • {w['name']}: ${w['amount_usd']:,.0f}")
                lines.append(f"    {w['reason']}")

    return "\n".join(lines)


def fmt_vaults(top: int = 10) -> str:
    vaults = load_latest_snapshot()
    if not vaults:
        return "⚠️ 스냅샷 없음 — /run 명령으로 분석을 먼저 실행하세요."

    # 추천 볼트 (robustness 상위)
    core = [v for v in vaults if v.get("barbell_group") == "CORE"]
    sat  = [v for v in vaults if v.get("barbell_group") == "SATELLITE"]

    if not core:
        # 바벨 전략 없으면 robustness 상위
        vaults_sorted = sorted(vaults, key=lambda x: x.get("robustness_score", 0), reverse=True)
        core = vaults_sorted[:top // 2]
        sat  = vaults_sorted[top // 2: top]

    lines = [
        f"<b>🏆 추천 볼트 (바벨 전략)</b>",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"<b>🛡 CORE (안정, 50%)</b>",
    ]
    for i, v in enumerate(core[:5], 1):
        name = v.get("name", "?")[:18]
        apr  = v.get("apr_30d", 0)
        mdd  = v.get("max_drawdown", 0)
        tvl  = v.get("tvl", 0)
        rob  = v.get("robustness_score", 0)
        alloc = v.get("suggested_allocation", 0)
        lines.append(
            f"{i}. <b>{name}</b> | 배분 {alloc:.0f}%\n"
            f"   APR {apr:+.1f}% | MDD {mdd:.1f}% | TVL ${tvl:,.0f} | R²={rob:.2f}"
        )

    lines += ["", "<b>🚀 SATELLITE (성장, 50%)</b>"]
    for i, v in enumerate(sat[:5], 1):
        name = v.get("name", "?")[:18]
        apr  = v.get("apr_30d", 0)
        mdd  = v.get("max_drawdown", 0)
        tvl  = v.get("tvl", 0)
        alloc = v.get("suggested_allocation", 0)
        under = v.get("undervalue_score", 0)
        lines.append(
            f"{i}. <b>{name}</b> | 배분 {alloc:.0f}%\n"
            f"   APR {apr:+.1f}% | MDD {mdd:.1f}% | 저평가 {under:.2f}"
        )

    snaps = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")), reverse=True)
    if snaps:
        lines.append(f"\n📅 데이터: {Path(snaps[0]).stem}")

    return "\n".join(lines)


def fmt_alerts(n: int = 10) -> str:
    alerts = load_recent_alerts(n)
    if not alerts:
        return "📭 최근 알림 없음"

    lines = [f"<b>🔔 최근 알림 {len(alerts)}개</b>", "━━━━━━━━━━━━━━━━━━━━"]
    for a in alerts:
        t    = a.get("time", "")[:16].replace("T", " ")
        lvl  = a.get("level", "INFO")
        icon = "🔴" if lvl == "ERROR" else "⚠️" if lvl == "WARNING" else "ℹ️"
        title = a.get("title", "")
        msg   = a.get("message", "")[:80]
        lines.append(f"{icon} <b>{title}</b> [{t}]")
        if msg:
            lines.append(f"   {msg}")
    return "\n".join(lines)


def fmt_log() -> str:
    log_text = load_recent_log(25)
    lines = log_text.strip().splitlines()
    # 최신 20줄만
    recent = lines[-20:] if len(lines) > 20 else lines
    return f"<b>📋 최근 로그</b>\n━━━━━━━━━━━━━━━━━━━━\n<code>" + "\n".join(recent) + "</code>"


def _fmt_next_run(next_run_str: str) -> str:
    if not next_run_str:
        return "미정"
    try:
        dt = datetime.fromisoformat(next_run_str)
        now = datetime.now()
        diff = dt - now
        h = int(diff.total_seconds() // 3600)
        m = int((diff.total_seconds() % 3600) // 60)
        if h < 0:
            return "곧"
        return f"{dt.strftime('%H:%M')} (약 {h}시간 {m}분 후)"
    except Exception:
        return next_run_str[:16]


# ── 명령어 핸들러 ─────────────────────────────────────────────────────────────
HELP_TEXT = """<b>📌 명령어 목록</b>
━━━━━━━━━━━━━━━━━━━━
/status    — 시스템 현재 상태
/portfolio — 내 포트폴리오 현황
/vaults    — 추천 볼트 목록
/alerts    — 최근 알림 10개
/log       — 최근 실행 로그
/run       — 즉시 분석 실행 🔄
/stop      — 긴급 중단 🔴
/resume    — 긴급 중단 해제 ✅
/help      — 이 도움말"""


def handle_command(text: str, chat_id: str) -> None:
    """텍스트 명령어 처리"""
    text = text.strip().lower().split()[0] if text.strip() else ""

    if text in ("/start", "/help"):
        send_message(HELP_TEXT, chat_id)

    elif text == "/status":
        send_message(fmt_status(), chat_id)

    elif text == "/portfolio":
        send_message(fmt_portfolio(), chat_id)

    elif text == "/vaults":
        send_message(fmt_vaults(), chat_id)

    elif text == "/alerts":
        send_message(fmt_alerts(), chat_id)

    elif text == "/log":
        send_message(fmt_log(), chat_id)

    elif text == "/run":
        send_message("🔄 분석 실행 중... 잠시만 기다려 주세요 (최대 10분)", chat_id)
        threading.Thread(target=_run_analysis_async, args=(chat_id,), daemon=True).start()

    elif text == "/stop":
        reason = "텔레그램 명령 /stop"
        STOP_FLAG.write_text(
            json.dumps({"reason": reason, "time": datetime.now().isoformat()}),
            encoding="utf-8"
        )
        send_message("🔴 <b>긴급 중단 완료</b>\n분석이 중단되었습니다. /resume 으로 해제할 수 있습니다.", chat_id)

    elif text == "/resume":
        if STOP_FLAG.exists():
            STOP_FLAG.unlink()
        send_message("✅ <b>긴급 중단 해제 완료</b>\n다음 스케줄 시각에 분석이 재개됩니다.", chat_id)

    else:
        send_message(f"❓ 알 수 없는 명령어: <code>{text}</code>\n/help 로 명령어를 확인하세요.", chat_id)


def _run_analysis_async(chat_id: str):
    """백그라운드에서 분석 실행 후 결과 전송"""
    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "scheduler.py"), "--now"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=700,
        )
        if result.returncode == 0:
            send_message("✅ <b>분석 완료!</b>\n/status 또는 /portfolio 로 결과를 확인하세요.", chat_id)
        else:
            err = result.stderr[:300] if result.stderr else "알 수 없는 오류"
            send_message(f"❌ <b>분석 실패</b>\n<code>{err}</code>", chat_id)
    except subprocess.TimeoutExpired:
        send_message("⏰ 분석 타임아웃 (10분 초과)", chat_id)
    except Exception as e:
        send_message(f"❌ 오류: {e}", chat_id)


# ── Polling 루프 ──────────────────────────────────────────────────────────────
def run_polling():
    """텔레그램 long-polling으로 메시지 수신"""
    log.info("🤖 텔레그램 봇 시작 (polling)")
    log.info(f"   CHAT_ID: {CHAT_ID or '(미설정)'}")

    if not BOT_TOKEN:
        log.error("❌ BOT_TOKEN 미설정!")
        log.error("   telegram_config.json 에 bot_token, chat_id 를 설정하세요.")
        sys.exit(1)

    # 시작 알림
    if CHAT_ID:
        send_message(
            "🟢 <b>Hyperliquid 모니터 봇 시작!</b>\n"
            "/help 로 명령어를 확인하세요.",
            CHAT_ID
        )

    offset = 0
    retry_delay = 5

    while True:
        try:
            result = tg_request("getUpdates", {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message"],
            }, timeout=40)

            if not result.get("ok"):
                log.warning(f"getUpdates 실패: {result}")
                time.sleep(retry_delay)
                continue

            for update in result.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message", {})
                if not msg:
                    continue

                text    = msg.get("text", "")
                chat_id = str(msg.get("chat", {}).get("id", ""))
                user    = msg.get("from", {}).get("first_name", "?")

                if not text:
                    continue

                log.info(f"📩 [{user}] {text[:50]}")

                # 보안: 등록된 chat_id만 허용
                if CHAT_ID and chat_id != CHAT_ID:
                    send_message("⛔ 인증되지 않은 사용자입니다.", chat_id)
                    continue

                handle_command(text, chat_id)

            retry_delay = 5  # 성공 시 리셋

        except requests.exceptions.ReadTimeout:
            continue  # long-poll timeout은 정상
        except requests.exceptions.ConnectionError:
            log.warning(f"연결 오류 — {retry_delay}초 후 재시도")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
        except KeyboardInterrupt:
            log.info("🛑 봇 종료")
            if CHAT_ID:
                send_message("🔴 봇이 종료되었습니다.", CHAT_ID)
            break
        except Exception as e:
            log.error(f"예외: {e}")
            time.sleep(retry_delay)


# ── 알림 전송 (scheduler.py 에서 호출 가능) ───────────────────────────────────
def notify(title: str, message: str, level: str = "INFO"):
    """
    scheduler.py의 send_alert()에서 호출되도록 설계된 함수.
    scheduler.py에 아래 코드를 추가하면 자동 텔레그램 알림:

        try:
            from telegram_bot import notify
            notify(title, message, level)
        except Exception:
            pass
    """
    global BOT_TOKEN, CHAT_ID
    if not BOT_TOKEN or not CHAT_ID:
        BOT_TOKEN, CHAT_ID = load_config()

    icon = "🔴" if level == "ERROR" else "⚠️" if level == "WARNING" else "ℹ️"
    text = f"{icon} <b>{title}</b>\n{message}"
    send_message(text, CHAT_ID)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperliquid 텔레그램 봇")
    parser.add_argument("--test",   action="store_true", help="테스트 메시지 전송")
    parser.add_argument("--status", action="store_true", help="상태 메시지 전송")
    args = parser.parse_args()

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN 미설정!")
        print("")
        print("설정 방법 (둘 중 하나):")
        print("  1) 환경변수:")
        print("     set TELEGRAM_BOT_TOKEN=your_token")
        print("     set TELEGRAM_CHAT_ID=your_chat_id")
        print("")
        print("  2) telegram_config.json 파일 생성:")
        print('     {"bot_token": "your_token", "chat_id": "your_chat_id"}')
        print("")
        print("BotFather에서 봇 생성: https://t.me/BotFather")
        sys.exit(1)

    if args.test:
        print("📤 테스트 메시지 전송 중...")
        ok = send_message(
            "✅ <b>Hyperliquid 봇 연결 성공!</b>\n"
            f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "/help 로 명령어를 확인하세요.",
            CHAT_ID
        )
        print("✅ 전송 성공!" if ok else "❌ 전송 실패!")

    elif args.status:
        print("📤 상태 메시지 전송 중...")
        send_message(fmt_status(), CHAT_ID)
        print("✅ 완료")

    else:
        run_polling()
