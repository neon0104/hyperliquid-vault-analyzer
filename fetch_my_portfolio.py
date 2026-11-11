#!/usr/bin/env python3
"""실제 Hyperliquid 포트폴리오를 가져와서 my_portfolio.json 및 virtual_portfolios.json에 동기화"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.utils import constants
from io_utils import atomic_write_json

BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=True)

cfg_path = BASE_DIR / "config.json"
config = {}
if cfg_path.exists():
    with open(cfg_path, encoding="utf-8") as f:
        config = json.load(f)

user_addr = (os.environ.get("HL_ACCOUNT_ADDRESS") or config.get("account_address") or "").strip()
print(f"지갑주소: {user_addr}")

info = Info(constants.MAINNET_API_URL, skip_ws=True)

# 볼트 에쿼티 조회
equities = info.post("/info", {"type": "userVaultEquities", "user": user_addr})

# 방어: 응답이 리스트가 아니면 기존 파일을 덮어쓰지 않고 종료
if not isinstance(equities, list):
    print(
        f"⚠️ 볼트 에쿼티 응답 형식 오류(type={type(equities).__name__}). "
        f"기존 my_portfolio.json 을 보존하고 종료합니다.",
        file=sys.stderr,
    )
    sys.exit(1)

portfolio = {}
holdings = []
total = 0.0

for item in (equities or []):
    addr = str(item.get("vaultAddress", "")).lower()
    equity = float(item.get("equity", 0) or 0)
    if not addr or equity <= 0.01:
        continue
    locked = item.get("lockedUntilTimestamp", 0)
    total += equity

    try:
        details = info.post("/info", {"type": "vaultDetails", "vaultAddress": addr, "user": user_addr}) or {}
        name = details.get("name", addr[:16])
        allow_dep = details.get("allowDeposits", True)
        fs = details.get("followerState") or {}
        cur_pnl = float(fs.get("pnl", 0.0) or 0.0)
        principal = round(max(0.0, float(fs.get("vaultEquity", equity) or equity) - cur_pnl), 2)
    except Exception:
        name = addr[:16]
        allow_dep = True
        principal = round(equity, 2)

    locked_dt = ""
    if locked:
        try:
            locked_dt = datetime.fromtimestamp(locked / 1000).strftime("%Y-%m-%d %H:%M")
        except Exception:
            locked_dt = str(locked)

    print(f"\n  볼트명  : {name}")
    print(f"  주소    : {addr}")
    print(f"  원금    : ${principal:,.2f} / 에쿼티: ${equity:,.4f}")
    print(f"  입금가능: {allow_dep}")
    print(f"  잠금해제: {locked_dt or '-'}")

    portfolio[addr] = principal if principal > 0.01 else round(equity, 2)
    holdings.append({
        "vault_address": addr,
        "name": name,
        "invested_usd": round(equity, 4),
        "locked_until": locked_dt,
        "allow_deposits": allow_dep,
    })

print(f"\n현재 볼트 평가액 합계: ${total:,.4f} ({len(portfolio)}개 볼트)")

# my_portfolio.json 저장 (최초 투입 원금 total_capital 및 invest_date 보존!)
pf_path = BASE_DIR / "my_portfolio.json"
old_data = {}
if pf_path.exists():
    with open(pf_path, encoding="utf-8") as f:
        try:
            old_data = json.load(f)
        except Exception:
            old_data = {}

old_cap = float(old_data.get("total_capital", 0.0) or 0.0)
same_wallet = str(old_data.get("account_address", "")).lower() == user_addr.lower()

ledger_inv_date = None
ledger_net_cap = 0.0
try:
    import hl_auto_vault_bot as _bot
    _lsum = _bot.fetch_wallet_vault_ledger_summary(user_addr, ttl_sec=0.0)
    if _lsum.get("ok"):
        ledger_inv_date = _lsum.get("invest_date")
        ledger_net_cap = float(_lsum.get("net_capital_usd", 0.0) or 0.0)
except Exception:
    pass

if ledger_net_cap >= 200.0:
    base_capital = round(ledger_net_cap, 2)
elif same_wallet and old_cap >= 200.0:
    base_capital = round(old_cap, 2)
else:
    base_capital = round(total, 2) if total > 0 else round(old_cap, 2)

if ledger_inv_date:
    inv_date = str(ledger_inv_date)
else:
    inv_date = str(old_data.get("invest_date") or datetime.now().strftime("%Y-%m-%d"))

pf_data = {
    "_comment": old_data.get("_comment", "SGRA+ 자동운용 봇 실시간 동기화 포트폴리오"),
    "account_address": user_addr,
    "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "total_capital": base_capital,
    "invest_date": inv_date,
    "positions": portfolio,
}

atomic_write_json(str(pf_path), pf_data, indent=2)
print("my_portfolio.json 저장 완료 (원금 보존:", base_capital, ")")

# virtual_portfolios.json 에도 실시간 싱크 처리 (원금 total_capital 덮어쓰기 방지!)
vp_path = BASE_DIR / "vault_data" / "virtual_portfolios.json"
if vp_path.exists():
    try:
        with open(vp_path, encoding="utf-8") as f:
            vp_data = json.load(f)

        updated = False
        for p in vp_data:
            if p.get("id") == "default":
                p["positions"] = portfolio
                p["total_capital"] = base_capital
                p["invest_date"] = inv_date
                updated = True
                break

        if updated:
            atomic_write_json(str(vp_path), vp_data, indent=2)
            print("virtual_portfolios.json 에 나의 실제 포트폴리오 싱크 완료")
    except Exception as e:
        print(f"virtual_portfolios.json 싱크 오류: {e}")
