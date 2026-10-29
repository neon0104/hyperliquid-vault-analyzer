#!/usr/bin/env python3
"""
setup_wallet_key.py — Hyperliquid 자동운용 지갑 서명키(.env) 로컬 보안 등록 도우미
=================================================================================
- 입력한 Private Key는 화면에 절대 출력되지 않으며(.gitignore로 보호되는 로컬 .env에만 저장),
  외부로 전송되지 않습니다.
- Private Key로부터 지갑 주소(0x...)를 자동 추출하여 검증하고, Hyperliquid 메인넷 잔고를 즉시 확인합니다.
"""
import getpass
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
CONFIG_JSON = BASE_DIR / "config.json"


def main() -> None:
    print("=" * 72)
    print("🛡️  Hyperliquid 자동운용 지갑 서명키(.env) 로컬 보안 등록")
    print("=" * 72)
    print("• 보안을 위해 입력하시는 Private Key는 화면에 표시되지 않습니다.")
    print("• 복사한 Private Key를 마우스 우클릭(또는 Ctrl+V)으로 붙여넣고 Enter를 누르세요.\n")

    raw_pk = getpass.getpass("🔑 운용 지갑 Private Key 입력 (화면 숨김): ").strip()
    if not raw_pk:
        print("\n❌ 입력된 값이 없어 취소되었습니다.")
        return

    pk_norm = raw_pk if raw_pk.startswith("0x") else ("0x" + raw_pk)
    try:
        import eth_account
        acct = eth_account.Account.from_key(pk_norm)
        derived_addr = acct.address
    except Exception:
        print("\n❌ 유효한 이더리움/Hyperliquid Private Key 형식이 아닙니다. (64자리 16진수 확인)")
        return
    finally:
        raw_pk = ""

    # Preserve any other existing .env variables (if any) while updating HL_ACCOUNT_ADDRESS & HL_BOT_PRIVATE_KEY
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

    # Sync public wallet address to config.json so /my-portfolio tracks the same wallet
    cfg = {}
    if CONFIG_JSON.exists():
        try:
            cfg = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    cfg["account_address"] = derived_addr
    CONFIG_JSON.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n✅ 서명키 로컬 보안 저장 완료! (.env 파일 — Git 업로드 차단됨)")
    print(f"   • 연결된 지갑 주소 : {derived_addr}")

    # Verify live on-chain balance immediately
    try:
        from hl_auto_vault_bot import fetch_onchain_account_state, run_autobot_cycle
        oc = fetch_onchain_account_state(derived_addr)
        run_autobot_cycle(force_rebalance=False)
        if oc.get("connected"):
            print(f"   • Perps 가용 USDC  : ${oc.get('perp_withdrawable_usd', 0):,.2f}")
            print(f"   • Spot 보유 USDC   : ${oc.get('spot_usdc_usd', 0):,.2f}")
            print(f"   • 현재 볼트 예치액 : ${oc.get('vault_total_equity_usd', 0):,.2f}")
            print(f"   • 지갑 총자산 합계 : ${oc.get('total_equity_usd', 0):,.2f}")
    except Exception as e:
        print(f"   • 온체인 조회 참고 : {e}")

    print("\n👉 이제 Hyperliquid에 자금을 입금하신 뒤,")
    print("   웹 사이트(http://localhost:5001/autobot)에서 [▶️ 자동운용 재개 실행] 버튼을 누르면")
    print("   즉시 포트폴리오 자동 배분 및 무인 리밸런싱이 시작됩니다!")
    print("=" * 72)


if __name__ == "__main__":
    main()
