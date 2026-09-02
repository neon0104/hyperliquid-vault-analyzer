#!/usr/bin/env python3
"""
sync_live_hl_mdds.py — Hyperliquid 공식 API에서 직접 전체 우량 볼트의 공식 Max MDD 연동
==================================================================================
Hyperliquid 공식 endpoint ('vaultDetails' -> 'portfolio' -> 'perpAllTime')를 호출하여
모든 우량 볼트의 생성일~현재까지 전체 실체 Max MDD 및 Current DD를 실시간으로 직접 동기화합니다.
"""

import requests, json, sys, os
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR      = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
DATA_DIR      = BASE_DIR / "vault_data"
SNAPSHOT_FILE = DATA_DIR / "snapshots" / "2026-08-13.json"
OUTPUT_FILE   = DATA_DIR / "official_vault_mdds.json"

API_URL = "https://api.hyperliquid.xyz/info"

def fetch_hl_vault_official_mdd(addr: str):
    payload = {"type": "vaultDetails", "vaultAddress": addr}
    try:
        res = requests.post(API_URL, json=payload, timeout=8)
        if res.status_code != 200:
            return None
        data = res.json()
        if not isinstance(data, dict) or "portfolio" not in data:
            return None

        portfolio = data["portfolio"]
        all_time_data = None
        for item in portfolio:
            if isinstance(item, list) and len(item) == 2:
                if item[0] in ["perpAllTime", "allTime"]:
                    all_time_data = item[1]
                    break
        if not all_time_data and portfolio:
            all_time_data = portfolio[-1][1] if isinstance(portfolio[-1], list) and len(portfolio[-1]) == 2 else None

        if not all_time_data or "accountValueHistory" not in all_time_data:
            return None

        history = all_time_data["accountValueHistory"]
        vals = [float(h[1]) for h in history if float(h[1]) > 0]
        if len(vals) < 2:
            return None

        vals_arr = np.array(vals)
        peaks = np.maximum.accumulate(vals_arr)
        drawdowns = (peaks - vals_arr) / peaks * 100.0
        max_mdd = float(np.max(drawdowns))
        curr_dd = float(drawdowns[-1])

        return {
            "address": addr,
            "name": data.get("name", addr[:10]),
            "leader": data.get("leader", ""),
            "tvl": float(data.get("followerState", {}).get("vaultEquity", 0.0) if data.get("followerState") else 0.0),
            "history_points": len(vals),
            "official_max_mdd": round(max_mdd, 2),
            "official_curr_dd": round(curr_dd, 2),
            "peak_value": round(float(np.max(vals_arr)), 2),
            "curr_value": round(float(vals_arr[-1]), 2)
        }
    except Exception as e:
        return None

def main():
    if not SNAPSHOT_FILE.exists():
        print("Snapshot file not found!")
        return

    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    print(f"📡 Hyperliquid 공식 서버 API에서 상위 {min(50, len(snapshot))}개 볼트의 공식 Max MDD 동기화 시작...")

    results = {}
    for i, v in enumerate(snapshot[:50], 1):
        addr = v["address"]
        name = v.get("name", addr[:10])
        mdd_info = fetch_hl_vault_official_mdd(addr)
        if mdd_info:
            results[addr] = mdd_info
            print(f"  [{i:2d}/50] ✅ {name[:25]:25s} -> Hyperliquid 공식 Max MDD: -{mdd_info['official_max_mdd']:>6.2f}% | 현재 DD: -{mdd_info['official_curr_dd']:>5.2f}%")
        else:
            print(f"  [{i:2d}/50] ⚠️ {name[:25]:25s} -> 공식 API 쿼리 대기 중")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 총 {len(results)}개 우량 볼트의 Hyperliquid 공식 Max MDD 동기화 완료!")
    print(f"  저장 위치: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
