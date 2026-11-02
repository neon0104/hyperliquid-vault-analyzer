@echo off
chcp 65001 >nul
cd /d "%~dp0"
python -X utf8 setup_wallet_key.py --gui
if %errorlevel% neq 0 (
    python -X utf8 setup_wallet_key.py
    pause
)
