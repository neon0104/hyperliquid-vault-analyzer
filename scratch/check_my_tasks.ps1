Get-ScheduledTask | Where-Object {$_.TaskName -match 'Daily' -or $_.TaskName -match 'Hyperliquid' -or $_.TaskName -match 'Vault'} | ForEach-Object {
    $info = Get-ScheduledTaskInfo -TaskName $_.TaskName
    Write-Host "Task: $($_.TaskName)"
    Write-Host "State: $($_.State)"
    Write-Host "LastRun: $($info.LastRunTime)"
    Write-Host "Result: $($info.LastTaskResult)"
    Write-Host "---"
}
