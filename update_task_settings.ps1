$taskName = "HyperliquidDailyUpdate"
$task = Get-ScheduledTask -TaskName $taskName

# Principal 설정: 관리자 권한(Highest) 부여, LogonType을 Interactive로 변경
$principal = New-ScheduledTaskPrincipal -UserId $task.Principal.UserId -LogonType Interactive -RunLevel Highest

# Settings 설정: 미실행 시 즉시 실행, 배터리 무시, 절전 해제 등
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable

try {
    Set-ScheduledTask -TaskName $taskName -Principal $principal -Settings $settings | Out-File task_update.log
    Write-Host "Task '$taskName' updated successfully with Highest Privileges and StartWhenAvailable."
    "Success" | Out-File -Append task_update.log
} catch {
    $_.Exception.Message | Out-File -Append task_update.log
}
