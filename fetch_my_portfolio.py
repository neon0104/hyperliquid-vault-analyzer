#!/usr/bin/env python3
"""실제 Hyperliquid 포트폴리오를 가져와서 my_portfolio.json 저장"""
import json, os, sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hyperliquid.info import Info
from hyperliquid.utils import constants

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

user_addr = config["account_address"]
print(f"지갑주소: {user_addr}")

info = Info(constants.MAINNET_API_URL, skip_ws=True)

# 볼트 에쿼티 조회
equities = info.post("/info", {"type": "userVaultEquities", "user": user_addr})
print(f"\n볼트 수: {len(equities) if equities else 0}개")

portfolio = {}
holdings  = []
total     = 0.0

for item in (equities or []):
    addr   = item.get("vaultAddress", "")
    equity = float(item.get("equity", 0))
    locked = item.get("lockedUntilTimestamp", 0)
    total += equity

    # 볼트 상세 정보
    try:
        details = info.post("/info", {"type": "vaultDetails", "vaultAddress": addr})
        name = details.get("name", addr[:16]) if details else addr[:16]
        allow_dep = details.get("allowDeposits", True) if details else True
    except Exception as e:
        name = addr[:16]
        allow_dep = True
        details = {}

    locked_dt = ""
    if locked:
        try:
            locked_dt = datetime.fromtimestamp(locked / 1000).strftime("%Y-%m-%d %H:%M")
        except Exception:
            locked_dt = str(locked)

    print(f"\n  볼트명  : {name}")
    print(f"  주소    : {addr}")
    print(f"  에쿼티  : ${equity:,.4f}")
    print(f"  입금가능: {allow_dep}")
    print(f"  잠금해제: {locked_dt or '-'}")

    portfolio[addr] = equity
    holdings.append({
        "vault_address": addr,
        "name": name,
        "invested_usd": equity,
        "locked_until": locked_dt,
        "allow_deposits": allow_dep,
    })

print(f"\n총 투자금: ${total:,.4f}")

# vault_data/my_portfolio.json 저장
os.makedirs("vault_data", exist_ok=True)
pf_data = {
    "account_address": user_addr,
    "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "total_invested_usd": round(total, 4),
    "holdings": holdings,
    # rebalance_engine이 읽는 형식 (vault_address -> usd amount)
    "positions": portfolio,
}
with open("vault_data/my_portfolio.json", "w", encoding="utf-8") as f:
    json.dump(pf_data, f, ensure_ascii=False, indent=2)

print("\nvault_data/my_portfolio.json 저장 완료")
print(json.dumps(pf_data, ensure_ascii=False, indent=2))
