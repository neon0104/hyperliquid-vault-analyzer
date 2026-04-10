import os
import sys
import glob
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'vault_data'
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'

def check_data_health():
    print('=' * 55)
    print('[Data Health Hook] Data Collection Integrity Check Started')
    print('=' * 55)
    
    if not SNAPSHOTS_DIR.exists():
        print('ERROR: vault_data/snapshots folder does not exist.')
        sys.exit(1)

    # KST (UTC+9) 기준 날짜 사용 (pre_run_check.py와 동일)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d')
    
    snaps = sorted(glob.glob(str(SNAPSHOTS_DIR / '*.json')))
    
    if len(snaps) == 0:
        print('ERROR: No data saved.')
        sys.exit(1)

    today_file = SNAPSHOTS_DIR / f'{today_str}.json'
    if not today_file.exists():
        print(f'ERROR: Today ({today_str}) data was not collected!')
        sys.exit(1)

    file_size = os.path.getsize(today_file)
    if file_size < 50000:
        print(f'ERROR: Data size is too small! ({file_size} Bytes)')
        sys.exit(1)

    print(f'SUCCESS: {today_str} data collected correctly. ({file_size / 1024:.1f} KB)')
    sys.exit(0)

if __name__ == '__main__':
    check_data_health()
