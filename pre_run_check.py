import os
from datetime import datetime, timedelta
from pathlib import Path
import sys

def main():
    # KST 기준 오늘 날짜 계산 (UTC + 9)
    kst_now = datetime.utcnow() + timedelta(hours=9)
    today_str = kst_now.strftime('%Y-%m-%d')
    
    snap_file = Path(__file__).parent / "vault_data" / "snapshots" / f"{today_str}.json"
    
    skip = False
    if snap_file.exists():
        size = os.path.getsize(snap_file)
        if size > 50000:
            print(f"✅ Data for {today_str} already fully collected ({size} bytes). Skipping further analysis.")
            skip = True
        else:
            print(f"⚠️ Data for {today_str} exists but is too small ({size} bytes). Proceeding with retry.")
    else:
        print(f"⏳ Data for {today_str} not yet collected. Proceeding with analysis.")
        
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"skip={'true' if skip else 'false'}\n")

if __name__ == "__main__":
    main()
