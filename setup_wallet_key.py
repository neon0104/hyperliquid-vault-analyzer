#!/usr/bin/env python3
"""
setup_wallet_key.py — Hyperliquid 자동운용 지갑 서명키(.env) 로컬 보안 등록 도우미
=================================================================================
- GUI 모드 (`--gui`) 및 터미널 숨김입력 모드 모두 지원
- 입력한 Private Key는 화면/로그/외부로 절대 노출되지 않으며 로컬 `.env`에만 격리 저장됩니다.
"""
import argparse
import getpass
import json
import sys
from pathlib import Path
from typing import Tuple

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
CONFIG_JSON = BASE_DIR / "config.json"


def validate_and_save_key(raw_pk: str) -> Tuple[bool, str]:
    raw_pk = (raw_pk or "").strip()
    if not raw_pk:
        return False, "입력된 Private Key가 없습니다."

    pk_norm = raw_pk if raw_pk.startswith("0x") else ("0x" + raw_pk)
    try:
        import eth_account
        acct = eth_account.Account.from_key(pk_norm)
        derived_addr = acct.address
    except Exception:
        return False, "유효한 이더리움/메타마스크 Private Key 형식이 아닙니다.\n(0x로 시작하거나 64자리 16진수 문자열인지 확인해주세요)"
    finally:
        raw_pk = ""

    kept_lines = []
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("HL_ACCOUNT_ADDRESS=") or s.startswith("HL_BOT_PRIVATE_KEY="):
                continue
            kept_lines.append(line)

    kept_lines.append(f"HL_ACCOUNT_ADDRESS={derived_addr}")
    kept_lines.append(f"HL_BOT_PRIVATE_KEY={pk_norm}")
    ENV_FILE.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")
    pk_norm = ""

    # Sync public wallet address to config.json
    cfg = {}
    if CONFIG_JSON.exists():
        try:
            cfg = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    cfg["account_address"] = derived_addr
    CONFIG_JSON.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    bal_msg = ""
    try:
        from hl_auto_vault_bot import fetch_onchain_account_state, run_autobot_cycle
        oc = fetch_onchain_account_state(derived_addr)
        run_autobot_cycle(force_rebalance=False)
        if oc.get("connected"):
            bal_msg = (
                f"\n\n[실시간 확인된 Hyperliquid 잔고]\n"
                f"• 지갑 주소: {derived_addr}\n"
                f"• Spot USDC : ${oc.get('spot_usdc_usd', 0):,.2f}\n"
                f"• Perps USDC: ${oc.get('perp_withdrawable_usd', 0):,.2f}\n"
                f"• 총 자산   : ${oc.get('total_equity_usd', 0):,.2f}"
            )
    except Exception:
        bal_msg = f"\n• 연결된 지갑 주소: {derived_addr}"

    return True, (
        f"✅ 서명키(.env) 로컬 보안 등록이 완료되었습니다!{bal_msg}\n\n"
        f"이제 웹 브라우저(http://localhost:5001/autobot)로 돌아가서\n"
        f"초록색 [▶️ 자동운용 재개 실행] 버튼을 누르면 즉시 자동운용이 시작됩니다!"
    )


def run_gui() -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("🔑 Hyperliquid 자동운용 서명키 보안 등록")
    root.geometry("540x320")
    root.configure(bg="#0b0f1a")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    lbl_title = tk.Label(
        root,
        text="🛡️ 메타마스크 운용 지갑 Private Key 로컬 등록",
        bg="#0b0f1a", fg="#1abc9c", font=("Malgun Gothic", 12, "bold"),
    )
    lbl_title.pack(pady=(18, 6))

    lbl_desc = tk.Label(
        root,
        text=(
            "메타마스크에서 복사한 Private Key를 아래 칸에 붙여넣고 저장을 누르세요.\n"
            "입력값은 마스킹(•) 처리되며 내 PC의 .env 파일에만 안전하게 격리 저장됩니다."
        ),
        bg="#0b0f1a", fg="#cbd5e1", font=("Malgun Gothic", 9), justify="center",
    )
    lbl_desc.pack(pady=(0, 14))

    frame_in = tk.Frame(root, bg="#0b0f1a")
    frame_in.pack(padx=24, fill="x")

    pk_var = tk.StringVar()
    entry = tk.Entry(
        frame_in, textvariable=pk_var, show="•",
        bg="#131928", fg="#ffffff", insertbackground="#ffffff",
        relief="solid", bd=1, font=("Consolas", 11),
    )
    entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 8))
    entry.focus_set()

    def paste_clip():
        try:
            clip = root.clipboard_get().strip()
            pk_var.set(clip)
        except Exception:
            messagebox.showwarning("클립보드 비어있음", "클립보드에 복사된 텍스트가 없습니다.\n먼저 메타마스크에서 개인키를 복사해주세요.", parent=root)

    btn_paste = tk.Button(
        frame_in, text="📋 붙여넣기", command=paste_clip,
        bg="#1e293b", fg="#7cb3ff", activebackground="#334155", activeforeground="#ffffff",
        relief="flat", font=("Malgun Gothic", 9, "bold"), padx=12, pady=6, cursor="hand2",
    )
    btn_paste.pack(side="right")

    status_lbl = tk.Label(root, text="", bg="#0b0f1a", fg="#fbbf24", font=("Malgun Gothic", 9))
    status_lbl.pack(pady=(10, 6))

    def on_save():
        val = pk_var.get().strip()
        if not val:
            messagebox.showwarning("입력 필요", "Private Key를 붙여넣어 주세요.", parent=root)
            return
        status_lbl.config(text="⏳ 지갑 주소 검증 및 Hyperliquid 잔고 확인 중...")
        root.update_idletasks()
        ok, msg = validate_and_save_key(val)
        pk_var.set("")
        if ok:
            try:
                root.clipboard_clear()  # 보안을 위해 클립보드에 남은 개인키도 자동 비움
            except Exception:
                pass
            messagebox.showinfo("등록 완료", msg, parent=root)
            root.destroy()
        else:
            status_lbl.config(text="❌ 형식 오류 — 다시 확인해주세요.")
            messagebox.showerror("등록 실패", msg, parent=root)

    btn_save = tk.Button(
        root, text="💾 보안 저장 및 지갑 연결하기", command=on_save,
        bg="#059669", fg="#ffffff", activebackground="#10b981", activeforeground="#ffffff",
        relief="flat", font=("Malgun Gothic", 11, "bold"), padx=22, pady=9, cursor="hand2",
    )
    btn_save.pack(pady=(6, 14))

    entry.bind("<Return>", lambda _e: on_save())
    root.mainloop()


def run_cli() -> None:
    print("=" * 72)
    print("🛡️  Hyperliquid 자동운용 지갑 서명키(.env) 로컬 보안 등록")
    print("=" * 72)
    print("• 보안을 위해 입력하시는 Private Key는 화면에 표시되지 않습니다.")
    print("• 복사한 Private Key를 마우스 우클릭(또는 Ctrl+V)으로 붙여넣고 Enter를 누르세요.\n")
    raw_pk = getpass.getpass("🔑 운용 지갑 Private Key 입력 (화면 숨김): ").strip()
    ok, msg = validate_and_save_key(raw_pk)
    raw_pk = ""
    print("\n" + msg)
    print("=" * 72)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui", action="store_true", help="Windows GUI 입력창 실행")
    args = parser.parse_args()
    if args.gui:
        run_gui()
    else:
        run_cli()
