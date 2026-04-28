#!/usr/bin/env python3
"""스냅샷 데이터 무결성 검증 (GitHub Actions용 hook)"""
import os, sys, glob
from pathlib import Path
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
BASE_DIR = Path(__file__).parent
SNAPSHOTS_DIR = BASE_DIR / 'vault_data' / 'snapshots'

def check_data_health():
    print('=' * 55)
    print('[Data Health Check] Integrity Verification')
    print('=' * 55)

    if not SNAPSHOTS_DIR.exists():
        print('ERROR: vault_data/snapshots/ does not exist.')
        sys.exit(1)

    today_str = datetime.now(KST).strftime('%Y-%m-%d')
    snaps = sorted(glob.glob(str(SNAPSHOTS_DIR / '*.json')))

    if not snaps:
        print('ERROR: No snapshots found.')
        sys.exit(1)

    today_file = SNAPSHOTS_DIR / f'{today_str}.json'
    if not today_file.exists():
        print(f'ERROR: Today ({today_str}) data missing!')
        sys.exit(1)

    file_size = os.path.getsize(today_file)
    if file_size < 50000:
        print(f'ERROR: Data too small ({file_size:,} bytes)')
        sys.exit(1)

    print(f'OK: {today_str} - {file_size / 1024:.1f} KB')
    sys.exit(0)

if __name__ == '__main__':
    check_data_health()
