@echo off
chcp 65001 > nul
echo =====================================================
echo   Hyperliquid Vault Analyzer - 매일 자동 실행
echo   %DATE% %TIME%
echo =====================================================

cd /d "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"
python analyze_top_vaults.py

echo.
echo 분석 완료. 로그는 vault_data\logs\ 에 저장됩니다.
pause
