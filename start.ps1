# ============================================================
#  Hyperliquid Vault Dashboard - 시작 스크립트
#  포트 5000 점유 프로세스를 먼저 종료하고 대시보드를 실행합니다.
# ============================================================

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Hyperliquid Vault Dashboard 시작 준비 중..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 포트 5000을 사용 중인 프로세스 모두 강제 종료
$pids = (netstat -ano | Select-String ":5000 " | ForEach-Object {
    ($_ -split '\s+')[-1]
}) | Select-Object -Unique

if ($pids) {
    Write-Host "  기존 프로세스 종료 중: PID $($pids -join ', ')" -ForegroundColor Yellow
    foreach ($p in $pids) {
        try { Stop-Process -Id $p -Force -ErrorAction SilentlyContinue } catch {}
    }
    Start-Sleep -Milliseconds 500
    Write-Host "  완료!" -ForegroundColor Green
} else {
    Write-Host "  기존 프로세스 없음 - 바로 시작합니다." -ForegroundColor Green
}

# 대시보드 실행
Write-Host ""
Write-Host "  브라우저: http://localhost:5000" -ForegroundColor Cyan
Write-Host "  종료: Ctrl+C" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Set-Location $PSScriptRoot
python web_dashboard.py
