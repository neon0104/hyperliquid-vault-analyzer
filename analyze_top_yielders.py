#!/usr/bin/env python3
import json, glob
import numpy as np

files = sorted(glob.glob("vault_data/snapshots/*.json"))
start_file = [f for f in files if "2026-04-09" in f][0]
end_file = files[-1]

with open(start_file, encoding="utf-8") as f:
    snap_start = json.load(f)
with open(end_file, encoding="utf-8") as f:
    snap_end = json.load(f)

map_start = {v["address"]: v for v in snap_start}
map_end = {v["address"]: v for v in snap_end}

results = []
for addr, v_e in map_end.items():
    v_s = map_start.get(addr)
    if not v_s:
        continue
    
    pnl_s = float(v_s.get("alltime_pnl", [0])[-1] if isinstance(v_s.get("alltime_pnl"), list) else v_s.get("alltime_pnl", 0) or 0)
    pnl_e = float(v_e.get("alltime_pnl", [0])[-1] if isinstance(v_e.get("alltime_pnl"), list) else v_e.get("alltime_pnl", 0) or 0)
    tvl_s = float(v_s.get("tvl", 1.0) or 1.0)
    
    pnl_diff = pnl_e - pnl_s
    ret_pct = (pnl_diff / tvl_s) * 100.0 if tvl_s > 1000 else 0.0
    
    l_rat = float(v_e.get("leader_equity_ratio", 0) or 0)
    l_usd = float(v_e.get("leader_equity_usd", 0) or 0)
    name = v_e.get("name", addr)
    
    results.append({
        "name": name,
        "address": addr,
        "tvl_start": tvl_s,
        "pnl_diff": pnl_diff,
        "ret_pct": ret_pct,
        "leader_usd": l_usd,
        "leader_rat": l_rat,
        "robustness": float(v_e.get("robustness_score", 0) or 0)
    })

results.sort(key=lambda x: x["ret_pct"], reverse=True)
print("=== Hyperliquid Top Performing Vaults (2026-04-09 ~ 2026-08-11) ===")
for r in results[:20]:
    print(f"[{r['name'][:30]:30s}] PnL Diff: ${r['pnl_diff']:>12,.2f} | Est Ret: {r['ret_pct']:>8.2f}% | TVL: ${r['tvl_start']:>10,.0f} | Leader USD: ${r['leader_usd']:>8,.0f}")
