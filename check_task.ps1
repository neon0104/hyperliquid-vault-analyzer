$tasks = Get-ScheduledTask | Where-Object { $_.TaskPath -notmatch '\\Microsoft\\' }
foreach ($task in $tasks) {
    $info = Get-ScheduledTaskInfo -TaskName $task.TaskName
    Write-Host "TaskName: $($task.TaskName)"
    Write-Host "State: $($task.State)"
    Write-Host "LastRunTime: $($info.LastRunTime)"
    Write-Host "LastTaskResult: $($info.LastTaskResult)"
    Write-Host "---"
}
