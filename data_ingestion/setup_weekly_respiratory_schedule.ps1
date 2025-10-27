# Schedule CDC Respiratory Disease Rates Data Ingestion (Weekly)
# This script sets up a weekly Windows Task Scheduler job to fetch respiratory disease rates

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptPath "fetch_respiratory_rates.py"

# Get Python executable path
$pythonPath = (Get-Command python).Source

# Task name
$taskName = "CDC_Respiratory_Rates_Weekly_Ingestion"

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Removing old task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create action to run Python script
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $pythonScript -WorkingDirectory $scriptPath

# Create trigger - Weekly on Monday at 3 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 3am

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Fetches CDC Respiratory Disease Rates data weekly and loads to BigQuery"

Write-Host "`n✓ Successfully scheduled weekly task: $taskName"
Write-Host "  Script: $pythonScript"
Write-Host "  Schedule: Every Monday at 3:00 AM"
Write-Host "`nTo view the task:"
Write-Host "  Get-ScheduledTask -TaskName '$taskName'"
Write-Host "`nTo run the task immediately:"
Write-Host "  Start-ScheduledTask -TaskName '$taskName'"
Write-Host "`nTo remove the task:"
Write-Host "  Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false"
