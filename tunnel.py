#!/usr/bin/env python3
"""
tunnel.py — 공개 URL로 모바일 접속 설정
=========================================
ngrok 또는 Cloudflare Tunnel을 사용해서
어디서든 접속 가능한 짧은 URL 생성

사용법:
  python tunnel.py          # ngrok으로 터널 시작
  python tunnel.py --cf     # Cloudflare Tunnel 사용 (더 안정적)
  python tunnel.py --qr     # QR코드 출력 (모바일로 바로 스캔)

요구사항:
  pip install pyngrok qrcode[pil]
  또는 Cloudflare: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/
"""

import sys, os, time, subprocess, threading, argparse, json
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATUS_FILE = BASE_DIR / "vault_data" / "status.json"


def update_public_url(url: str):
    """status.json에 공개 URL 저장 → 대시보드에서 표시"""
    os.makedirs(STATUS_FILE.parent, exist_ok=True)
    status = {}
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    status["public_url"]        = url
    status["public_mobile_url"] = url + "/m"
    STATUS_FILE.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ 공개 URL 저장됨: {url}")


def print_qr(url: str):
    """터미널에 QR 코드 출력"""
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        print("⚠️  QR 출력 불가: pip install qrcode[pil]")


def run_dashboard_background():
    """web_dashboard.py를 백그라운드로 실행"""
    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "web_dashboard.py")],
        cwd=str(BASE_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"  ✅ 대시보드 시작 (PID: {proc.pid})")
    return proc


def start_ngrok(port: int = 5000, show_qr: bool = False):
    """
    ngrok으로 로컬 서버를 공개 URL로 노출
    설치: pip install pyngrok
    """
    try:
        from pyngrok import ngrok, conf
    except ImportError:
        print("❌ pyngrok 미설치. 실행: pip install pyngrok")
        sys.exit(1)

    print("🚀 ngrok 터널 시작 중...")
    tunnel = ngrok.connect(port, "http")
    public_url = tunnel.public_url

    # https 강제
    if public_url.startswith("http://"):
        public_url = public_url.replace("http://", "https://", 1)

    mobile_url = public_url + "/m"

    print()
    print("=" * 55)
    print("  📱 모바일 접속 정보")
    print("=" * 55)
    print(f"  🌐 전체 대시보드:  {public_url}")
    print(f"  📱 모바일 페이지: {mobile_url}")
    print(f"  🔴 긴급 중단:     {public_url}/m")
    print("=" * 55)
    print()

    update_public_url(public_url)

    if show_qr:
        print("📷 QR 코드 (모바일 카메라로 스캔):")
        print_qr(mobile_url)

    print("💡 Ctrl+C 로 터널 종료")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 터널 종료 중...")
        ngrok.kill()


def start_cloudflare(port: int = 5000, show_qr: bool = False):
    """
    Cloudflare Tunnel (cloudflared) 사용
    설치: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/
    Windows: winget install cloudflare.cloudflared
    """
    print("🚀 Cloudflare Tunnel 시작 중...")
    print("(URL 생성까지 약 10초 소요)")

    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace",
    )

    public_url = None
    import re

    # stderr에서 URL 파싱 (cloudflared는 stderr에 URL 출력)
    for line in proc.stderr:
        sys.stdout.write("  " + line)
        # trycloudflare.com URL 패턴
        match = re.search(r"https://[a-z0-9\-]+\.trycloudflare\.com", line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        print("❌ Cloudflare URL 파싱 실패. cloudflared가 설치되어 있는지 확인하세요.")
        proc.kill()
        sys.exit(1)

    mobile_url = public_url + "/m"

    print()
    print("=" * 60)
    print("  📱 모바일 접속 정보 (Cloudflare)")
    print("=" * 60)
    print(f"  🌐 전체 대시보드:  {public_url}")
    print(f"  📱 모바일 페이지: {mobile_url}")
    print(f"  🔴 긴급 중단:     {mobile_url}  (하단 버튼)")
    print("=" * 60)
    print()

    update_public_url(public_url)

    if show_qr:
        print("📷 QR 코드 (모바일 카메라로 스캔):")
        print_qr(mobile_url)

    print("💡 Ctrl+C 로 터널 종료")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 터널 종료 중...")
        proc.kill()


def start_local_info(port: int = 5000, show_qr: bool = False):
    """같은 WiFi 환경일 때 로컬 IP 주소 안내"""
    import socket
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except Exception:
        local_ip = "192.168.x.x"

    mobile_url = f"http://{local_ip}:{port}/m"

    print()
    print("=" * 55)
    print("  📱 같은 WiFi 접속 정보")
    print("=" * 55)
    print(f"  📱 모바일 페이지: {mobile_url}")
    print(f"  💻 로컬 PC:       http://localhost:{port}/m")
    print()
    print("  ⚠️  같은 WiFi (집 안)에서만 접속 가능")
    print("  ⚠️  외부에서 접속하려면 ngrok 사용:")
    print("       pip install pyngrok")
    print("       python tunnel.py")
    print("=" * 55)

    update_public_url(f"http://{local_ip}:{port}")

    if show_qr:
        print("\n📷 QR 코드 (같은 WiFi에서 스캔):")
        print_qr(mobile_url)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="모바일 접속용 공개 URL 터널",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python tunnel.py           # ngrok (어디서든 접속)
  python tunnel.py --cf      # Cloudflare Tunnel
  python tunnel.py --local   # 같은 WiFi만 (로컬IP 안내)
  python tunnel.py --qr      # QR코드 함께 출력
        """
    )
    parser.add_argument("--cf",    action="store_true", help="Cloudflare Tunnel 사용")
    parser.add_argument("--local", action="store_true", help="로컬 IP 안내만 (터널 없음)")
    parser.add_argument("--qr",    action="store_true", help="QR 코드 출력")
    parser.add_argument("--port",  type=int, default=5000, help="포트 (기본: 5000)")
    parser.add_argument("--no-dashboard", action="store_true", help="대시보드 자동 시작 안 함")
    args = parser.parse_args()

    # 대시보드 자동 시작
    if not args.no_dashboard:
        print("🚀 대시보드 자동 시작 중...")
        run_dashboard_background()
        time.sleep(2)  # 서버 기동 대기

    if args.local:
        start_local_info(args.port, args.qr)
    elif args.cf:
        start_cloudflare(args.port, args.qr)
    else:
        start_ngrok(args.port, args.qr)
