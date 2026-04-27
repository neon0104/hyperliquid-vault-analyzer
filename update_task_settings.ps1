$taskName = "HyperliquidDailyUpdate"
$task = Get-ScheduledTask -TaskName $taskName

# Principal 설정: 관리자 권한(Highest) 부여
$principal = New-ScheduledTaskPrincipal -UserId $task.Principal.UserId -LogonType $task.Principal.LogonType -RunLevel Highest

# Settings 설정: 미실행 시 즉시 실행, 배터리 무시, 절전 해제 등
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable

Set-ScheduledTask -TaskName $taskName -Principal $principal -Settings $settings
Write-Host "Task '$taskName' updated successfully with Highest Privileges and StartWhenAvailable."
