@echo off
cd /d "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"

echo ======================================================== >> auto_run.log
echo [%date% %time%] Starting daily data update... >> auto_run.log

echo Running analyze_top_vaults.py... >> auto_run.log
python analyze_top_vaults.py >> auto_run.log 2>&1

echo Running daily_pnl_collector.py... >> auto_run.log
python daily_pnl_collector.py >> auto_run.log 2>&1

echo Pushing updated data to GitHub... >> auto_run.log
git add . >> auto_run.log 2>&1
git commit -m "Auto-update daily data [%date%]" >> auto_run.log 2>&1
git push >> auto_run.log 2>&1

echo [%date% %time%] Update completed. Entering sleep mode... >> auto_run.log

rem 작업이 끝나면 10초 대기 후 강제로 절전 모드(Sleep) 진입
timeout /t 10 /nobreak > nul
powershell -NoProfile -Command "Add-Type -Assembly System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState('Suspend', $false, $false)"
