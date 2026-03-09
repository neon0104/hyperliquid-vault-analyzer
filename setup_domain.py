#!/usr/bin/env python3
"""
setup_domain.py — 나만의 도메인으로 대시보드 접속
====================================================
DuckDNS 무료 도메인 + Cloudflare Tunnel 조합으로
  http://myvault.duckdns.org
같은 주소로 어디서든 접속 가능하게 설정

사전 준비:
  1. https://duckdns.org 에서 도메인 등록 (무료)
     예: myvault → myvault.duckdns.org
  2. winget install cloudflare.cloudflared

실행:
  python setup_domain.py
"""

import os, sys, json, time, subprocess, threading
import urllib.request, urllib.parse
from pathlib import Path

BASE_DIR    = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "vault_data" / "domain_config.json"
STATUS_FILE = BASE_DIR / "vault_data" / "status.json"

# ──────────────────────────────────────────────────────────────────────────────

def save_config(cfg: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def update_status(patch: dict):
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    status.update(patch)
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")


# ── DuckDNS IP 업데이트 ───────────────────────────────────────────────────────

def duckdns_update(subdomain: str, token: str) -> bool:
    """DuckDNS에 현재 공인 IP 업데이트"""
    url = (
        f"https://www.duckdns.org/update"
        f"?domains={subdomain}&token={token}&ip="
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            result = r.read().decode().strip()
        if result == "OK":
            print(f"  ✅ DuckDNS 업데이트 성공: {subdomain}.duckdns.org")
            return True
        else:
            print(f"  ❌ DuckDNS 업데이트 실패: {result}")
            return False
    except Exception as e:
        print(f"  ❌ DuckDNS 연결 오류: {e}")
        return False


def duckdns_updater_loop(subdomain: str, token: str, interval: int = 300):
    """5분마다 IP 갱신 (IP가 바뀌어도 도메인 유지)"""
    while True:
        duckdns_update(subdomain, token)
        time.sleep(interval)


# ── Cloudflare Tunnel ─────────────────────────────────────────────────────────

def start_cloudflare_tunnel(port: int = 5000):
    """
    Cloudflare Quick Tunnel 시작
    (도메인 등록 없이도 임시 URL 생성)
    """
    print("  🚀 Cloudflare Tunnel 시작 중...")
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    return proc


def parse_cloudflare_url(proc) -> str | None:
    """cloudflared 출력에서 URL 파싱"""
    import re
    for line in proc.stdout:
        line = line.strip()
        if line:
            print(f"    {line}")
        match = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", line)
        if match:
            return match.group(0)
    return None


# ── Main Setup ────────────────────────────────────────────────────────────────

def setup_interactive():
    print()
    print("=" * 60)
    print("  🌐 나만의 URL 설정 마법사")
    print("=" * 60)
    print()

    # 기존 설정 확인
    cfg = load_config()
    if cfg.get("subdomain"):
        print(f"  📌 기존 설정: {cfg['subdomain']}.duckdns.org")
        ans = input("  기존 설정 사용? [Y/n]: ").strip().lower()
        if ans != "n":
            return run_with_config(cfg)

    # DuckDNS 설정
    print()
    print("  📋 STEP 1: DuckDNS 설정")
    print("  ─────────────────────────")
    print("  1. https://www.duckdns.org 접속")
    print("  2. Google 또는 GitHub으로 로그인")
    print("  3. 원하는 이름 입력 (예: myvault) → [add domain] 클릭")
    print("  4. 페이지 상단의 token 값 복사")
    print()

    subdomain = input("  원하는 주소 입력 (예: myvault): ").strip().lower()
    if not subdomain:
        print("  ❌ 취소")
        return

    token = input("  DuckDNS token 입력: ").strip()
    if not token:
        print("  ❌ 토큰 없이는 진행 불가")
        return

    # 설정 저장
    cfg = {"subdomain": subdomain, "token": token, "port": 5000}
    save_config(cfg)
    print(f"\n  ✅ 설정 저장 완료: vault_data/domain_config.json")

    run_with_config(cfg)


def run_with_config(cfg: dict):
    subdomain = cfg["subdomain"]
    token     = cfg["token"]
    port      = cfg.get("port", 5000)
    domain    = f"{subdomain}.duckdns.org"

    print()
    print(f"  🎯 목표 주소: http://{domain}")
    print()

    # 1. 대시보드 시작
    print("  STEP 1: 대시보드 시작")
    dash_proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "web_dashboard.py")],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"         ✅ 대시보드 실행 (PID: {dash_proc.pid})")
    time.sleep(2)

    # 2. DuckDNS IP 업데이트
    print(f"\n  STEP 2: DuckDNS IP 업데이트 중...")
    duckdns_update(subdomain, token)

    # 3. 백그라운드 IP 갱신 스레드
    t = threading.Thread(
        target=duckdns_updater_loop,
        args=(subdomain, token, 300),
        daemon=True
    )
    t.start()
    print("         ✅ 5분마다 자동 IP 갱신 시작")

    # 4. Cloudflare Tunnel 시작
    print(f"\n  STEP 3: Cloudflare Tunnel 연결 중...")
    print("         (약 10~20초 소요...)")
    cf_proc = start_cloudflare_tunnel(port)

    # URL 파싱
    cf_url = None
    import re
    for line in cf_proc.stdout:
        line = line.strip()
        match = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", line)
        if match:
            cf_url = match.group(0)
            break

    if not cf_url:
        print("  ⚠️  Cloudflare URL 파싱 실패. cloudflared 설치 확인:")
        print("      winget install cloudflare.cloudflared")
        # fallback: 로컬 IP 안내
        import socket
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "192.168.x.x"
        cf_url = f"http://{local_ip}:{port}"

    # 5. 결과 출력
    mobile_url     = cf_url + "/m"
    duckdns_note   = (
        f"  ⚠️  DuckDNS({domain})는 포트포워딩 필요 (공유기 설정)\n"
        f"  → 지금 당장 사용: {mobile_url}"
    )

    update_status({
        "public_url":        cf_url,
        "public_mobile_url": mobile_url,
        "duckdns_domain":    domain,
    })

    print()
    print("=" * 60)
    print("  ✅ 설정 완료!")
    print("=" * 60)
    print()
    print(f"  📱 지금 바로 접속 (Cloudflare):")
    print(f"     {mobile_url}")
    print()
    print(f"  🌐 DuckDNS 고정 주소:")
    print(f"     http://{domain}/m")
    print()
    print("  💡 DuckDNS 주소는 공유기에서 포트포워딩(5000번)")
    print("     설정 후 사용 가능합니다.")
    print()

    # QR코드 출력
    try:
        import qrcode
        print("  📷 QR코드 (카메라로 스캔):")
        qr = qrcode.QRCode(border=1)
        qr.add_data(mobile_url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print("  (QR 출력: pip install qrcode[pil])")

    print()
    print("  🛑 종료: Ctrl+C")
    print("  🔴 긴급중단: 모바일 페이지 하단 버튼")
    print()

    # 대기
    try:
        cf_proc.wait()
    except KeyboardInterrupt:
        print("\n  🛑 종료 중...")
        cf_proc.kill()
        dash_proc.kill()


# ── 진단 모드 ─────────────────────────────────────────────────────────────────

def check_requirements():
    """필수 프로그램 확인"""
    print("\n  🔍 환경 체크:")

    # cloudflared
    try:
        r = subprocess.run(["cloudflared", "--version"],
                          capture_output=True, text=True, timeout=5)
        print(f"  ✅ cloudflared: {r.stdout.strip()}")
    except FileNotFoundError:
        print("  ❌ cloudflared 미설치")
        print("     설치: winget install cloudflare.cloudflared")

    # qrcode
    try:
        import qrcode
        print("  ✅ qrcode: 설치됨")
    except ImportError:
        print("  ⚠️  qrcode 미설치 (선택사항)")
        print("     설치: pip install qrcode[pil]")

    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="나만의 URL 설정")
    parser.add_argument("--check", action="store_true", help="환경 체크만")
    parser.add_argument("--run",   action="store_true", help="기존 설정으로 바로 실행")
    args = parser.parse_args()

    if args.check:
        check_requirements()
    elif args.run:
        cfg = load_config()
        if not cfg:
            print("❌ 설정 없음. python setup_domain.py 로 먼저 설정하세요.")
        else:
            run_with_config(cfg)
    else:
        check_requirements()
        setup_interactive()
