#!/usr/bin/env python3
"""
스냅샷 JSON 파일에서 SQLite 데이터베이스(daily_pnl 및 vaults 테이블)로 누락된 데이터 백필(Backfill) 스크립트
========================================================================================
이 스크립트는 vault_data/snapshots/ 디렉토리에 있는 과거 JSON 파일을 읽어서
SQLite 데이터베이스(vault_data/pnl_history.db)에 누락된 날짜의 레코드를 자동으로 채워넣습니다.
"""

import os
import sys
import glob
import json
import sqlite3
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "vault_data" / "pnl_history.db"
SNAPSHOTS_DIR = BASE_DIR / "vault_data" / "snapshots"

def sf(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def backfill():
    if not DB_PATH.exists():
        print(f"[ERROR] DB file does not exist: {DB_PATH}")
        return

    # 스냅샷 파일 검색
    snapshot_files = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")))
    if not snapshot_files:
        print("[ERROR] No snapshot JSON files found.")
        return

    print("=" * 60)
    print("  Starting backfill of historical snapshot data into SQLite DB")
    print("=" * 60)

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    total_inserted = 0
    total_skipped = 0

    for file_path in snapshot_files:
        filename = os.path.basename(file_path)
        date_str = os.path.splitext(filename)[0] # YYYY-MM-DD
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                vaults_list = json.load(f)
        except Exception as e:
            print(f"  [WARN] Failed to read {filename}: {e}")
            continue

        print(f"  Parsing {date_str} ({len(vaults_list)} vaults)...")
        
        inserted_for_day = 0
        skipped_for_day = 0

        for v in vaults_list:
            addr = v.get("address")
            name = v.get("name", "Unknown")[:60]
            tvl = sf(v.get("tvl", 0))

            if not addr:
                continue

            # vaults 메타 테이블 업데이트
            c.execute("""
                INSERT INTO vaults (address, name, first_seen, last_seen)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    name=excluded.name,
                    last_seen=excluded.last_seen
            """, (addr, name, date_str, date_str))

            # PnL 리스트 추출
            alltime_pnl_list = v.get("alltime_pnl", [])
            month_pnl_list = v.get("month_pnl", [])

            # 리스트 정형화
            alltime_pnl_list = [sf(x) for x in alltime_pnl_list] if isinstance(alltime_pnl_list, list) else []
            month_pnl_list = [sf(x) for x in month_pnl_list] if isinstance(month_pnl_list, list) else []

            alltime_pnl_val = alltime_pnl_list[-1] if alltime_pnl_list else sf(v.get("pnl_alltime", 0.0))
            month_pnl_last = month_pnl_list[-1] if month_pnl_list else sf(v.get("pnl_30d", 0.0))
            month_pnl_max = max(month_pnl_list) if month_pnl_list else 0.0
            month_pnl_min = min(month_pnl_list) if month_pnl_list else 0.0
            month_mdd = sf(v.get("max_drawdown", 0.0))

            # DB 저장 (이미 존재하는 vault_address + date_str은 INSERT OR IGNORE 로 무시)
            try:
                c.execute("""
                    INSERT INTO daily_pnl (
                        vault_address, collected_at, tvl,
                        alltime_pnl,
                        day_pnl_max, day_pnl_min, day_pnl_last,
                        week_pnl_max, week_pnl_min, week_pnl_last,
                        month_pnl_max, month_pnl_min, month_pnl_last,
                        day_mdd_pct, week_mdd_pct, month_mdd_pct,
                        day_pnl_raw, week_pnl_raw, month_pnl_raw, alltime_pnl_raw
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    addr, date_str, tvl,
                    alltime_pnl_val,
                    0.0, 0.0, 0.0,  # day
                    0.0, 0.0, 0.0,  # week
                    month_pnl_max, month_pnl_min, month_pnl_last,
                    0.0, 0.0, month_mdd,
                    "[]", "[]", json.dumps(month_pnl_list), json.dumps(alltime_pnl_list)
                ))
                inserted_for_day += 1
            except sqlite3.IntegrityError:
                # UNIQUE 제약 조건(vault_address, collected_at) 충돌 시 무시됨
                skipped_for_day += 1
            except Exception as e:
                print(f"    [ERROR] SQLite error ({addr}): {e}")

        total_inserted += inserted_for_day
        total_skipped += skipped_for_day
        
        if inserted_for_day > 0:
            print(f"    -> Inserted: {inserted_for_day} / Skipped (existing): {skipped_for_day}")

    conn.commit()
    conn.close()

    print("=" * 60)
    print("  Backfill completed!")
    print(f"  - Total new records inserted: {total_inserted:,}")
    print(f"  - Total existing records skipped: {total_skipped:,}")
    print("=" * 60)

if __name__ == "__main__":
    backfill()
