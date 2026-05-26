$taskName = "HyperliquidDailyUpdate"

# Principal 설정: 관리자 권한(Highest) 부여 및 대화형 실행 설정
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest

# Settings 설정: 미실행 시 즉시 실행, 배터리 작동 시에도 시작, 절전 모드 해제
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable

# Trigger 설정: 매일 오전 9시 15분 실행
$trigger = New-ScheduledTaskTrigger -Daily -At "9:15AM"

try {
    # 기존 작업의 트리거,Principal,Settings 업데이트
    Set-ScheduledTask -TaskName $taskName -Trigger $trigger -Principal $principal -Settings $settings -ErrorAction Stop
    
    Write-Host "`n========================================================" -ForegroundColor Green
    Write-Host " SUCCESS: '$taskName' 작업의 시작 시간이 오전 9시 15분으로 변경되었습니다!" -ForegroundColor Green
    Write-Host "========================================================`n" -ForegroundColor Green
} catch {
    Write-Host "`n========================================================" -ForegroundColor Red
    Write-Host " ERROR: 작업 변경에 실패했습니다." -ForegroundColor Red
    Write-Host " 원인: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host " 해결방법: 이 스크립트는 '관리자 권한'으로 실행해야 합니다." -ForegroundColor Yellow
    Write-Host "         PowerShell을 마우스 우클릭하여 '관리자 권한으로 실행'한 뒤 다시 구동하세요." -ForegroundColor Yellow
    Write-Host "========================================================`n" -ForegroundColor Red
}

Write-Host "아무 키나 누르면 창이 닫힙니다..."
$null = [System.Console]::ReadKey()
