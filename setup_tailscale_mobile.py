#!/usr/bin/env python3
"""
setup_tailscale_mobile.py — Tailscale 무료 사설망 1클릭 설치 및 휴대폰 직행 주소/QR 안내
"""
import os
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = int(os.environ.get("PORT", "5001"))


def find_tailscale_exe() -> str | None:
    w = shutil.which("tailscale")
    if w:
        return w
    for p in [
        r"C:\Program Files\Tailscale\tailscale.exe",
        r"C:\Program Files (x86)\Tailscale\tailscale.exe",
    ]:
        if Path(p).exists():
            return p
    return None


def get_tailscale_ip(ts_exe: str) -> str | None:
    try:
        out = subprocess.check_output([ts_exe, "ip", "-4"], text=True, timeout=4, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            s = line.strip()
            if s.startswith("100."):
                return s
    except Exception:
        pass
    return None


def print_ascii_qr(url: str) -> None:
    try:
        import qrcode
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except Exception:
        pass


def main() -> None:
    print("=" * 64)
    print("  📱 Hyperliquid 내 실제 포트폴리오 — Tailscale 모바일 직행 세팅")
    print("=" * 64)

    ts_exe = find_tailscale_exe()
    if not ts_exe:
        print("\n[1/3] PC에 Tailscale이 아직 설치되어 있지 않습니다. 자동 설치를 시작합니다...")
        print("      (Windows 관리자 권한 승인 창이 뜨면 [예]를 눌러주세요.)\n")
        subprocess.run(
            ["winget", "install", "--id", "Tailscale.Tailscale", "-e", "--accept-package-agreements", "--accept-source-agreements"],
            check=False,
        )
        time.sleep(2)
        ts_exe = find_tailscale_exe()

    if not ts_exe:
        print("\n⚠️ 자동 설치를 완료하지 못했습니다. https://tailscale.com/download/windows 에서 설치 후 다시 실행해주세요.")
        webbrowser.open("https://tailscale.com/download/windows")
        return

    print(f"\n✅ Tailscale 설치 확인됨: {ts_exe}")
    ts_ip = get_tailscale_ip(ts_exe)

    if not ts_ip:
        print("\n[2/3] Tailscale 로그인 창을 엽니다. 브라우저에서 구글/애플 계정으로 로그인해주세요...")
        gui_exe = Path(ts_exe).parent / "tailscale-ipn.exe"
        if gui_exe.exists():
            subprocess.Popen([str(gui_exe)])
        subprocess.Popen([ts_exe, "login"])
        print("      로그인 완료 대기 중 (최대 90초)...")
        for _ in range(45):
            time.sleep(2)
            ts_ip = get_tailscale_ip(ts_exe)
            if ts_ip:
                break

    if ts_ip:
        live_url = f"http://{ts_ip}:{PORT}/live"
        print("\n" + "=" * 64)
        print("  🎉 세팅 완료! 평생 바뀌지 않는 내 전용 휴대폰 직행 주소:")
        print(f"  👉  {live_url}")
        print("=" * 64)
        print("\n  [휴대폰 설정 방법]")
        print("  1) 아이폰/갤럭시에 'Tailscale' 앱 설치 후 PC와 같은 계정으로 로그인 & ON")
        print("  2) 아래 QR코드를 휴대폰 카메라로 스캔하여 접속")
        print("  3) Safari [공유 -> 홈 화면에 추가] 또는 Chrome [메뉴 -> 홈 화면에 추가]\n")
        print_ascii_qr(live_url)
        webbrowser.open(f"http://127.0.0.1:{PORT}/mobile-connect")
    else:
        print("\nℹ️ 작업표시줄 우측 하단 Tailscale 아이콘을 클릭해 로그인하신 뒤,")
        print(f"   브라우저에서 http://127.0.0.1:{PORT}/mobile-connect 를 열면 전용 QR코드가 표시됩니다.")
        webbrowser.open(f"http://127.0.0.1:{PORT}/mobile-connect")


if __name__ == "__main__":
    main()
