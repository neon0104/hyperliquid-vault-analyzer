#!/usr/bin/env python3
"""
ensure_dashboard_running.py — 웹 대시보드(Port 5001) + Cloudflare 외부 HTTPS 터널 무중단 감시기
=============================================================================================
1) http://127.0.0.1:5001/manifest.json 헬스체크 → 미응답 시 web_dashboard.py 백그라운드 자동 기동
2) cloudflared.exe 실행 여부 확인 → 미실행 시 외부 LTE/5G 접속용 HTTPS 터널 자동 기동 및 URL 기록
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = r"C:\Users\USER\AppData\Local\Programs\Python\Python310\python.exe"
LOG_FILE = BASE_DIR / "vault_data" / "dashboard_server.log"
CF_LOG_FILE = BASE_DIR / "vault_data" / "cloudflared_tunnel.log"
STATUS_FILE = BASE_DIR / "vault_data" / "status.json"
LOCK_FILE = BASE_DIR / "vault_data" / "dashboard_keeper.lock"
HEALTH_URL = "http://127.0.0.1:5001/manifest.json"
CREATION_FLAGS = 0x08000000 | 0x00000008  # CREATE_NO_WINDOW | DETACHED_PROCESS


def is_dashboard_healthy(timeout: float = 2.5) -> bool:
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def find_cloudflared() -> str | None:
    w = shutil.which("cloudflared")
    if w:
        return w
    cand = Path(os.environ.get("LOCALAPPDATA", "")) / r"Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
    if cand.exists():
        return str(cand)
    return None


def is_cloudflared_running() -> bool:
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq cloudflared.exe"],
            text=True,
            errors="replace",
            creationflags=0x08000000,
        )
        return "cloudflared.exe" in out.lower()
    except Exception:
        return False


def _notify_telegram_new_url(mobile_url: str) -> None:
    cfg_file = BASE_DIR / "telegram_config.json"
    if not cfg_file.exists():
        return
    try:
        import urllib.parse
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        if not cfg.get("enabled", True):
            return
        token = cfg.get("bot_token", "")
        chat_id = cfg.get("chat_id", "")
        if not (token and chat_id):
            return
        msg = (
            "📱 [내 실제 포트폴리오] 외부(5G/LTE) 접속 주소 안내\n\n"
            f"👉 {mobile_url}\n\n"
            "• 안드로이드: 링크 터치 후 우측 상단(⋮) → [Chrome에서 열기] → 로그인 → [홈 화면에 추가(설치)]\n"
            "• PC 재부팅 등으로 주소가 갱신될 때마다 자동으로 다시 알려드립니다."
        )
        payload = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode("utf-8")
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=payload)
        urllib.request.urlopen(req, timeout=6).read()
    except Exception:
        pass


def sync_tunnel_url_from_log() -> str | None:
    if not CF_LOG_FILE.exists():
        return None
    try:
        txt = CF_LOG_FILE.read_text(encoding="utf-8", errors="replace")
        matches = re.findall(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", txt)
        if not matches:
            return None
        pub_url = matches[-1]
        st = {}
        if STATUS_FILE.exists():
            try:
                st = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            except Exception:
                st = {}
        if st.get("public_url") != pub_url:
            st["public_url"] = pub_url
            st["public_mobile_url"] = pub_url + "/live"
            st["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            STATUS_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")
            _notify_telegram_new_url(pub_url + "/live")
        return pub_url
    except Exception:
        return None


def is_public_tunnel_healthy() -> bool:
    if not CF_LOG_FILE.exists():
        return False
    try:
        txt = CF_LOG_FILE.read_text(encoding="utf-8", errors="replace")
        if "protocol=quic" in txt:
            return False
        matches = re.findall(r"https://[a-zA-Z0-9\-]+\.trycloudflare\.com", txt)
        if not matches:
            return False
        req = urllib.request.Request(
            matches[-1] + "/manifest.json",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            return resp.status == 200
    except Exception:
        return False


def main() -> None:
    open_browser = "--open-browser" in sys.argv
    dash_ok = is_dashboard_healthy()
    cf_exe = find_cloudflared()
    cf_ok = (is_cloudflared_running() and is_public_tunnel_healthy()) if cf_exe else True

    if dash_ok and cf_ok:
        sync_tunnel_url_from_log()
        if open_browser:
            webbrowser.open("http://localhost:5001")
        return

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    fh = open(LOCK_FILE, "a+b")
    try:
        import msvcrt
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except Exception:
        fh.close()
        return

    try:
        if not is_dashboard_healthy():
            if LOG_FILE.exists() and LOG_FILE.stat().st_size > 5 * 1024 * 1024:
                bak = LOG_FILE.with_suffix(".log.bak")
                try:
                    if bak.exists():
                        bak.unlink()
                    LOG_FILE.rename(bak)
                except Exception:
                    pass

            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            log_fp = open(LOG_FILE, "a", encoding="utf-8", errors="replace")
            log_fp.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting detached web_dashboard.py...\n")
            log_fp.flush()

            subprocess.Popen(
                [PYTHON_EXE, "-X", "utf8", str(BASE_DIR / "web_dashboard.py")],
                cwd=str(BASE_DIR),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=log_fp,
                stderr=log_fp,
                creationflags=CREATION_FLAGS,
                close_fds=True,
            )

            for _ in range(16):
                time.sleep(0.5)
                if is_dashboard_healthy(timeout=1.5):
                    break

        if cf_exe and not (is_cloudflared_running() and is_public_tunnel_healthy()):
            if is_cloudflared_running():
                subprocess.run(
                    ["taskkill", "/F", "/IM", "cloudflared.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=0x08000000,
                    check=False,
                )
                time.sleep(0.8)
            cf_fp = open(CF_LOG_FILE, "w", encoding="utf-8", errors="replace")
            subprocess.Popen(
                [cf_exe, "tunnel", "--protocol", "http2", "--no-autoupdate", "--url", "http://127.0.0.1:5001"],
                cwd=str(BASE_DIR),
                stdin=subprocess.DEVNULL,
                stdout=cf_fp,
                stderr=cf_fp,
                creationflags=CREATION_FLAGS,
                close_fds=True,
            )
            for _ in range(24):
                time.sleep(0.5)
                if sync_tunnel_url_from_log():
                    break
        else:
            sync_tunnel_url_from_log()

        if open_browser and is_dashboard_healthy():
            webbrowser.open("http://localhost:5001")
    finally:
        try:
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        fh.close()


if __name__ == "__main__":
    main()
