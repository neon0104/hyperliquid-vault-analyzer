@echo off
setlocal enabledelayedexpansion
cd /d "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"

:: 로그 파일 설정
set LOG_FILE=auto_run.log
echo ======================================================== >> %LOG_FILE%
echo [%date% %time%] Starting daily data update... >> %LOG_FILE%

:: 관리자 권한 체크 (참고용)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [INFO] Running with Admin privileges. >> %LOG_FILE%
) else (
    echo [WARN] Not running as Admin. Some commands might fail. >> %LOG_FILE%
)

echo Pulling latest changes from GitHub... >> %LOG_FILE%
git pull origin main >> %LOG_FILE% 2>&1

echo Checking if data is already collected... >> %LOG_FILE%
python pre_run_check.py > tmp_check.txt
findstr /C:"OK: Data for" tmp_check.txt > nul
if %errorlevel%==0 (
    echo [SKIPPED] Data already collected by GitHub Actions. >> %LOG_FILE%
    goto skip_collect
)

echo Running analyze_top_vaults.py... >> %LOG_FILE%
python analyze_top_vaults.py >> %LOG_FILE% 2>&1

echo Running daily_pnl_collector.py... >> %LOG_FILE%
python daily_pnl_collector.py >> %LOG_FILE% 2>&1

:skip_collect
echo Pushing updated data to GitHub... >> %LOG_FILE%
git add . >> %LOG_FILE% 2>&1
git commit -m "Auto-update daily data [%date%]" >> %LOG_FILE% 2>&1
echo Syncing before push to avoid conflicts... >> %LOG_FILE%
git pull --rebase origin main >> %LOG_FILE% 2>&1
git push >> %LOG_FILE% 2>&1

echo [%date% %time%] Update completed. >> %LOG_FILE%

:: 작업 완료 알림 (선택 사항)
echo Update finished at %time%

:: 10초 대기 후 절전 모드 진입 (작업 예약 시 WakeToRun과 짝을 이룸)
:: 관리자 권한이 없을 경우를 대비해 전력 관리 도구 사용 시도
timeout /t 10 /nobreak > nul
echo Entering sleep mode... >> %LOG_FILE%
powershell -NoProfile -Command "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)" >> %LOG_FILE% 2>&1

