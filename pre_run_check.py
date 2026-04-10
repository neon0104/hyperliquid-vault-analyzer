#!/usr/bin/env python3
"""GitHub Actions 실행 전 중복 수집 방지 체크"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

KST = timezone(timedelta(hours=9))

def main():
    today_str = datetime.now(KST).strftime('%Y-%m-%d')
    snap_file = Path(__file__).parent / "vault_data" / "snapshots" / f"{today_str}.json"

    skip = False
    if snap_file.exists():
        size = os.path.getsize(snap_file)
        if size > 50000:
            print(f"OK: Data for {today_str} already collected ({size:,} bytes). Skipping.")
            skip = True
        else:
            print(f"WARN: {today_str} exists but too small ({size} bytes). Retrying.")
    else:
        print(f"RUN: {today_str} not yet collected. Proceeding.")

    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"skip={'true' if skip else 'false'}\n")

if __name__ == "__main__":
    main()
