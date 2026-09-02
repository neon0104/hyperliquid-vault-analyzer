import json
import os
import glob
import numpy as np
from pathlib import Path

BASE_DIR = Path(r"c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer")
SNAPSHOTS_DIR = BASE_DIR / "vault_data" / "snapshots"
SIM_RESULTS_PATH = BASE_DIR / "vault_data" / "walkforward_sim_results.json"

def get_vault_return(addr: str, from_date: str, to_date: str, snapshots_cache: dict) -> float:
    snap_to = snapshots_cache.get(to_date)
    if not snap_to:
        return 0.0

    vault_to = next((v for v in snap_to if v.get("address") == addr), None)
    if not vault_to:
        return 0.0

    pnl_to = vault_to.get("alltime_pnl", [])
    tvl    = float(vault_to.get("tvl", 1) or 1)

    snap_from = snapshots_cache.get(from_date)
    vault_from = None
    if snap_from:
        vault_from = next((v for v in snap_from if v.get("address") == addr), None)

    if not pnl_to or len(pnl_to) < 2:
        return 0.0

    if not vault_from:
        delta = pnl_to[-1] - pnl_to[-2] if len(pnl_to) >= 2 else 0
        return float(np.clip(delta / (tvl + abs(pnl_to[-2]) + 1e-9), -0.3, 0.3))

    pnl_from = vault_from.get("alltime_pnl", [])
    if not pnl_from:
        return 0.0

    val_to   = float(pnl_to[-1])
    val_from = float(pnl_from[-1])
    delta    = val_to - val_from
    denom    = tvl + abs(val_from) + 1e-9
    return float(np.clip(delta / denom, -0.3, 0.3))

def main():
    if not SIM_RESULTS_PATH.exists():
        print(f"Error: walkforward_sim_results.json not found at {SIM_RESULTS_PATH}")
        return

    with open(SIM_RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. 스냅샷 데이터 캐싱
    snapshot_files = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")))
    snapshots_cache = {}
    for f in snapshot_files:
        date_str = os.path.splitext(os.path.basename(f))[0]
        try:
            with open(f, "r", encoding="utf-8") as fd:
                snapshots_cache[date_str] = json.load(fd)
        except Exception as e:
            print(f"Error loading {date_str}: {e}")

    # 2. 확장할 날짜 찾기
    all_dates = sorted(snapshots_cache.keys())
    existing_dates = data["dates"]
    last_existing_date = existing_dates[-1]  # 2026-07-13
    print(f"Last existing date in walkforward: {last_existing_date}")

    ext_dates = [d for d in all_dates if d > last_existing_date]
    print(f"Dates to extend: {ext_dates}")

    if not ext_dates:
        print("No new dates to extend.")
        return

    baseline_addrs = [
        "0xc2ca95ce3eb285d58a811b80f6937a127b4f52ba", # Infinite Vault Robot
        "0xba939edf38c0ae0cc689c98b492e0535f43e4550", # 22Cap
        "0x8e72bb69abd6f0cf7907fac5ad6fb3f66870e0c6", # Hyperliquid Banana
        "0xa1222c3590709cd9bce80ae04c2fd07e89e8ab2a"  # GeorgV Copytrading
    ]

    prev_date = last_existing_date

    # 각 확장 대상 날짜에 대해 연산 진행
    for curr_date in ext_dates:
        # a) 벤치마크 업데이트
        bench_vals = data["benchmark"]["values"]
        # baseline 포트폴리오의 일별 평균 수익률 계산
        returns = []
        for addr in baseline_addrs:
            r = get_vault_return(addr, prev_date, curr_date, snapshots_cache)
            returns.append(r)
        avg_r = sum(returns) / len(returns)
        new_bench_val = bench_vals[-1] * (1 + avg_r)
        bench_vals.append(new_bench_val)

        # b) 각 전략 업데이트
        for strat_name, strat_data in data["strategies"].items():
            prev_details = strat_data["daily_details"][prev_date]
            holdings = []
            total_val = 0.0

            for prev_h in prev_details["holdings"]:
                addr = prev_h["address"]
                cost = prev_h["cost"]
                
                # 2026-07-12 (마지막 리밸런싱 날짜) 기준 수익률 계산
                # 7월 12일 이후로는 리밸런싱이 없었으므로 계속 7월 12일 기준
                r_since_rebalance = get_vault_return(addr, "2026-07-12", curr_date, snapshots_cache)
                amount = cost * (1 + r_since_rebalance)
                profit = amount - cost
                return_pct = (profit / cost * 100) if cost > 0 else 0.0

                holdings.append({
                    "name": prev_h["name"],
                    "address": addr,
                    "amount": round(amount, 2),
                    "cost": round(cost, 2),
                    "profit": round(profit, 2),
                    "return_pct": round(return_pct, 2)
                })
                total_val += amount

            total_val += prev_details.get("cash", 0.0)
            total_return = (total_val / 100000.0 - 1) * 100

            strat_data["values"].append(total_val)
            strat_data["daily_details"][curr_date] = {
                "total_value": round(total_val, 2),
                "total_return": round(total_return, 2),
                "cash": prev_details.get("cash", 0.0),
                "holdings": holdings
            }

        existing_dates.append(curr_date)
        prev_date = curr_date

    # 3. 요약 지표 재계산
    days = len(existing_dates) - 1
    data["days"] = days
    data["period"] = f"2026-04-09 to {existing_dates[-1]}"

    # Benchmark 지표 재계산
    bench_values = data["benchmark"]["values"]
    bench_final = bench_values[-1]
    data["benchmark"]["final_value"] = bench_final
    data["benchmark"]["total_return"] = (bench_final / 100000.0 - 1) * 100
    data["benchmark"]["cagr"] = ((bench_final / 100000.0) ** (365.0 / days) - 1) * 100
    
    peak = np.maximum.accumulate(bench_values)
    dd = (peak - bench_values) / peak * 100
    data["benchmark"]["mdd"] = -float(dd.max())
    
    rets = np.diff(bench_values) / bench_values[:-1]
    data["benchmark"]["sharpe"] = float(np.mean(rets) / (np.std(rets) + 1e-9) * np.sqrt(365))

    # 각 전략 지표 재계산
    for strat_name, strat_data in data["strategies"].items():
        strat_values = strat_data["values"]
        strat_final = strat_values[-1]
        
        strat_data["final_value"] = strat_final
        strat_data["total_return"] = (strat_final / 100000.0 - 1) * 100
        strat_data["cagr"] = ((strat_final / 100000.0) ** (365.0 / days) - 1) * 100
        
        peak = np.maximum.accumulate(strat_values)
        dd = (peak - strat_values) / peak * 100
        strat_data["mdd"] = -float(dd.max())
        
        rets = np.diff(strat_values) / strat_values[:-1]
        strat_data["sharpe"] = float(np.mean(rets) / (np.std(rets) + 1e-9) * np.sqrt(365))

    # 4. JSON 저장
    # 안전하게 원본 백업 후 원자적 쓰기 진행
    backup_path = SIM_RESULTS_PATH.with_suffix(".json.bak")
    try:
        if SIM_RESULTS_PATH.exists():
            import shutil
            shutil.copy2(SIM_RESULTS_PATH, backup_path)
    except Exception as e:
        print(f"Warning: Failed to create backup: {e}")

    with open(SIM_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Successfully extended walkforward simulation to {existing_dates[-1]} ({days} days total).")

if __name__ == "__main__":
    main()
