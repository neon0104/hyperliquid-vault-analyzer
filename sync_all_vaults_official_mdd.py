#!/usr/bin/env python3
"""
sync_all_vaults_official_mdd.py — Hyperliquid 공식 API 기반 역대 Max MDD 동기화기
===================================================================================
Hyperliquid 공식 서버 API (https://api.hyperliquid.xyz/info, type: vaultDetails)
최초 볼트 생성일부터 오늘까지의 전체 계좌 가치 시계열(accountValueHistory)을 직접 수집하여,
각 볼트의 100% 실측 역대 최고 낙폭(Historical Max MDD) 및 현재 낙폭(Current DD)을 계산합니다.
"""

import sys, json, urllib.request
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR      = BASE_DIR / "vault_data"
SNAPSHOTS_DIR = DATA_DIR / "snapshots"
OUTPUT_FILE   = DATA_DIR / "official_vault_mdds.json"

# 스냅샷에서 대상 볼트 주소 수집
files = sorted(SNAPSHOTS_DIR.glob("*.json"))
target_addrs = {}
for f in files[-5:]: # 최신 스냅샷
    with open(f, "r", encoding="utf-8") as fd:
        snap = json.load(fd)
        for v in snap[:50]: # 상위 50개 볼트
            addr = v.get("address")
            name = v.get("name", "Unknown")
            if addr and addr not in target_addrs:
                target_addrs[addr] = name

print(f"📡 Hyperliquid 공식 서버 API로부터 {len(target_addrs)}개 볼트의 전기간 계좌 역사 데이터 동기화 중...")

official_mdd_data = {}

for idx, (addr, name) in enumerate(target_addrs.items(), 1):
    req_body = json.dumps({"type": "vaultDetails", "vaultAddress": addr}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.hyperliquid.xyz/info",
        data=req_body,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
        portfolio = data.get("portfolio", [])
        alltime = None
        for p in portfolio:
            if isinstance(p, list) and len(p) >= 2 and p[0] == "perpAllTime":
                alltime = p[1]
                break
            elif isinstance(p, dict) and p.get("period") == "perpAllTime":
                alltime = p
                break
                
        if not alltime and portfolio:
            alltime = portfolio[-1] if isinstance(portfolio[-1], dict) else None
            
        history = []
        if isinstance(alltime, dict):
            history = alltime.get("accountValueHistory", [])
            
        if history and len(history) > 1:
            vals = [float(h[1]) for h in history if float(h[1]) > 0]
            if len(vals) > 1:
                vals_arr = np.array(vals)
                peaks = np.maximum.accumulate(vals_arr)
                dds = (peaks - vals_arr) / peaks * 100.0
                max_mdd = float(dds.max())
                curr_dd = float(dds[-1])
                
                official_mdd_data[addr] = {
                    "name": name,
                    "address": addr,
                    "official_max_mdd": round(max_mdd, 2),
                    "current_dd": round(curr_dd, 2),
                    "dip_pct_of_max": round((curr_dd / max_mdd * 100.0), 1) if max_mdd > 0 else 0.0,
                    "is_dip_buy_recommended": bool(curr_dd >= 0.70 * max_mdd and max_mdd >= 8.0),
                    "data_points": len(vals),
                    "start_val": round(vals[0], 2),
                    "latest_val": round(vals[-1], 2),
                    "peak_val": round(float(peaks.max()), 2)
                }
                print(f"  [{idx}/{len(target_addrs)}] {name[:20]:<20} -> 역대 Max MDD: -{max_mdd:.2f}%, 현재 DD: -{curr_dd:.2f}% (저점 도달율: {curr_dd/max_mdd*100 if max_mdd>0 else 0:.1f}%)")
    except Exception as e:
        print(f"  [{idx}/{len(target_addrs)}] {name[:20]:<20} -> API 처리 중 오류 (기본값 유지)")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(official_mdd_data, f, ensure_ascii=False, indent=2)

print("=" * 80)
print(f"✅ Hyperliquid 공식 역대 Max MDD 데이터 저장 완료 ({len(official_mdd_data)}개 볼트 저장): {OUTPUT_FILE}")
print("=" * 80)
