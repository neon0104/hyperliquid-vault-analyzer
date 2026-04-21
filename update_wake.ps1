powercfg /SETACVALUEINDEX SCHEME_CURRENT 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 1
powercfg /SETDCVALUEINDEX SCHEME_CURRENT 238c9fa8-0aad-41ed-83f4-97be242c8f20 bd3b718a-0680-4d9d-8ab2-e1d2b4ac806d 1
powercfg /setactive scheme_current

$taskName = "HyperliquidDailyUpdate"
$task = Get-ScheduledTask -TaskName $taskName
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Set-ScheduledTask -TaskName $taskName -Settings $settings
Write-Host "Task WakeToRun settings and Power Configuration updated successfully."
