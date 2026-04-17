$StartTime = Get-Date "2026-04-17 08:20:00"
$EndTime = Get-Date "2026-04-17 08:40:00"

try {
    $events = Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$StartTime; EndTime=$EndTime} -ErrorAction Stop
    foreach ($event in $events) {
        if ($event.Id -eq 1 -or $event.Id -eq 42 -or $event.Id -eq 107 -or $event.Id -eq 6005 -or $event.Id -eq 6006) {
            Write-Host "$($event.TimeCreated) - ID: $($event.Id) - $($event.Message)"
        }
    }
} catch {
    Write-Host "Error or no events found."
}
