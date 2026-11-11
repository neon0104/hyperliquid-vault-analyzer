@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"

set LOG_FILE=auto_run.log
echo ======================================================== >> %LOG_FILE%
echo [%date% %time%] Starting 4-hour data and SGRA+ autobot update... >> %LOG_FILE%

git rebase --abort >nul 2>&1

echo [0/9] Pulling latest changes from GitHub... >> %LOG_FILE%
git pull origin main --no-rebase --autostash >> %LOG_FILE% 2>&1

echo [1/9] Running fetch_my_portfolio.py... >> %LOG_FILE%
python -X utf8 fetch_my_portfolio.py >> %LOG_FILE% 2>&1

echo [2/9] Running analyze_top_vaults.py... >> %LOG_FILE%
python -X utf8 analyze_top_vaults.py >> %LOG_FILE% 2>&1

echo [3/9] Running daily_pnl_collector.py... >> %LOG_FILE%
python -X utf8 daily_pnl_collector.py >> %LOG_FILE% 2>&1

echo [4/9] Running hl_auto_vault_bot.py... >> %LOG_FILE%
python -X utf8 hl_auto_vault_bot.py >> %LOG_FILE% 2>&1

echo [5/9] Running auto_rebalancer.py... >> %LOG_FILE%
python -X utf8 auto_rebalancer.py >> %LOG_FILE% 2>&1

echo [6/9] Running autonomous_loop_engine.py... >> %LOG_FILE%
python -X utf8 autonomous_loop_engine.py >> %LOG_FILE% 2>&1

echo [7/9] Running autonomous_researcher.py... >> %LOG_FILE%
python -X utf8 autonomous_researcher.py >> %LOG_FILE% 2>&1

echo [8/9] Running master_portfolio_manager.py... >> %LOG_FILE%
python -X utf8 master_portfolio_manager.py >> %LOG_FILE% 2>&1

echo [9/9] Running export_dashboard_data.py... >> %LOG_FILE%
python -X utf8 export_dashboard_data.py >> %LOG_FILE% 2>&1

echo Pushing public analytics data to GitHub... >> %LOG_FILE%
git add vault_data/snapshots/*.json vault_data/master_portfolio_recommendation.json vault_data/loop_engine_summary.json vault_data/active_quant_strategy.json vault_data/auto_rebalance_sim.json vault_data/RESEARCH_DIARY.md vault_data/research_learning_log.json vault_data/loop_evaluation_history.json docs/data.json >> %LOG_FILE% 2>&1
git commit -m "Auto-update vault data [%date% %time%]" >> %LOG_FILE% 2>&1

git pull origin main --no-rebase --autostash >> %LOG_FILE% 2>&1
git push origin main >> %LOG_FILE% 2>&1

if %errorlevel% neq 0 (
    echo [WARN] Push failed - will retry next cycle. >> %LOG_FILE%
)

echo [%date% %time%] Update completed. >> %LOG_FILE%
echo Update finished at %time%
