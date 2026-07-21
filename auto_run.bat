@echo off
setlocal enabledelayedexpansion
cd /d "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"

:: Log file
set LOG_FILE=auto_run.log
echo ======================================================== >> %LOG_FILE%
echo [%date% %time%] Starting 4-hour data update... >> %LOG_FILE%

:: Check admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with Admin privileges. >> %LOG_FILE%
) else (
    echo [WARN] Not running as Admin. Some commands might fail. >> %LOG_FILE%
)

:: Abort any stuck rebase before pulling
git rebase --abort >nul 2>&1

:: Pull latest from GitHub (merge strategy to avoid rebase conflicts)
echo Pulling latest changes from GitHub... >> %LOG_FILE%
git pull origin main --no-rebase >> %LOG_FILE% 2>&1

:: Run data collection (no skip check - collect every 4 hours)
echo Running fetch_my_portfolio.py... >> %LOG_FILE%
python fetch_my_portfolio.py >> %LOG_FILE% 2>&1

echo Running analyze_top_vaults.py... >> %LOG_FILE%
python analyze_top_vaults.py >> %LOG_FILE% 2>&1

echo Running daily_pnl_collector.py... >> %LOG_FILE%
python daily_pnl_collector.py >> %LOG_FILE% 2>&1

:: Push to GitHub
echo Pushing updated data to GitHub... >> %LOG_FILE%
git add . >> %LOG_FILE% 2>&1
git commit -m "Auto-update vault data [%date% %time%]" >> %LOG_FILE% 2>&1

:: Use merge pull to avoid rebase conflicts
git pull origin main --no-rebase >> %LOG_FILE% 2>&1
git push origin main >> %LOG_FILE% 2>&1

:: 강제푸시(force push) 폴백 제거:
:: 원격의 더 최신 데이터(예: GitHub Actions 커밋)를 덮어써 유실시킬 수 있어 삭제했습니다.
:: 푸시가 실패하면 그대로 두고 다음 주기에 pull 후 재시도하는 것이 안전합니다.
if %errorlevel% neq 0 (
    echo [WARN] Push failed. 다음 주기에 pull 후 재시도합니다. 반복되면 수동 확인 필요. >> %LOG_FILE%
)

echo [%date% %time%] Update completed. >> %LOG_FILE%
echo Update finished at %time%
