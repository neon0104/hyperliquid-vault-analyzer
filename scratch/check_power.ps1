$events = Get-WinEvent -FilterHashtable @{LogName='System'; Id=@(1,42,107,6005,6006)} -MaxEvents 50 -ErrorAction SilentlyContinue
foreach ($e in $events) {
    Write-Host "$($e.TimeCreated) - ID: $($e.Id) - $($e.Message)"
}
