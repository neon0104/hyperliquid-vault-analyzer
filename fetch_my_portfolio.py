#!/usr/bin/env python3
"""실제 Hyperliquid 포트폴리오를 가져와서 my_portfolio.json 저장"""
import json, os, sys
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hyperliquid.info import Info
from hyperliquid.utils import constants
from io_utils import atomic_write_json

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

user_addr = config["account_address"]
print(f"지갑주소: {user_addr}")

info = Info(constants.MAINNET_API_URL, skip_ws=True)

# 볼트 에쿼티 조회
equities = info.post("/info", {"type": "userVaultEquities", "user": user_addr})

# 방어: 응답이 리스트가 아니면(None=일시적 실패, dict=오류 응답) 기존 파일을 덮어쓰지 않고 종료.
# 예전엔 None 응답 시 positions={} 가 저장되어 실제 포트폴리오가 사라지고
# rebalance_engine 이 $100k 시뮬 모드로 오작동했다. (빈 리스트=실제 무포지션은 정상 진행)
if not isinstance(equities, list):
    print(f"⚠️ 볼트 에쿼티 응답 형식 오류(type={type(equities).__name__}). "
          f"기존 my_portfolio.json 을 보존하고 종료합니다.", file=sys.stderr)
    sys.exit(1)

print(f"\n볼트 수: {len(equities)}개")

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

# my_portfolio.json 저장 (기존 정보 유지)
pf_path = "my_portfolio.json"
old_data = {}
if os.path.exists(pf_path):
    with open(pf_path, encoding="utf-8") as f:
        try:
            old_data = json.load(f)
        except:
            pass

pf_data = {
    "_comment": old_data.get("_comment", "내 실제 로드된 포트폴리오"),
    "account_address": user_addr,
    "fetched_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "total_capital": old_data.get("total_capital", round(total, 4)),
    "invest_date": old_data.get("invest_date", datetime.now().strftime("%Y-%m-%d")),
    "positions": portfolio,
}

atomic_write_json(pf_path, pf_data, indent=2)

print("\nmy_portfolio.json 저장 완료")

# virtual_portfolios.json 에도 실시간 싱크 처리
vp_path = os.path.join("vault_data", "virtual_portfolios.json")
if os.path.exists(vp_path):
    try:
        with open(vp_path, encoding="utf-8") as f:
            vp_data = json.load(f)
        
        updated = False
        for p in vp_data:
            if p.get("id") == "default":
                p["positions"] = portfolio
                p["total_capital"] = round(total, 4)
                updated = True
                break
        
        if updated:
            atomic_write_json(vp_path, vp_data, indent=2)
            print("virtual_portfolios.json 에 나의 실제 포트폴리오 싱크 완료")
    except Exception as e:
        print(f"virtual_portfolios.json 싱크 오류: {e}")

print(json.dumps(pf_data, ensure_ascii=False, indent=2))
