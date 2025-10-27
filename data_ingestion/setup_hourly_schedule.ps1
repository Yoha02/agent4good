# CDC NREVSS Data Ingestion - Hourly Scheduler (Windows Task Scheduler)
# 
# To set up hourly automatic ingestion on Windows:
#
# 1. Open Task Scheduler (taskschd.msc)
# 2. Create Basic Task
#    - Name: "CDC NREVSS Hourly Ingestion"
#    - Description: "Fetch CDC respiratory surveillance data every hour"
# 3. Trigger: "Daily" → Start at midnight, Repeat every: 1 hour, For a duration of: 1 day
# 4. Action: "Start a program"
#    - Program: C:\Users\semaa\OneDrive\Documents\Google\Agents4Impact-Improving-UI\.venv\Scripts\python.exe
#    - Arguments: fetch_cdc_nrevss.py
#    - Start in: C:\Users\semaa\OneDrive\Documents\Google\Agents4Impact-Improving-UI\data_ingestion
# 5. Finish and enter your Windows password if prompted
#
# IMPORTANT NOTES:
# - Hourly updates are NOT RECOMMENDED - CDC only updates this data weekly
# - Consider weekly or daily updates instead to avoid unnecessary API calls
# - Weekly schedule: Run once every Sunday at 2:00 AM
# - Daily schedule: Run once every day at 3:00 AM
#
# To create the task automatically, run this PowerShell script:

# Task details
$TaskName = "CDC_NREVSS_Hourly_Ingestion"
$Description = "Fetch CDC NREVSS respiratory surveillance data hourly"
$PythonExe = "C:\Users\semaa\OneDrive\Documents\Google\Agents4Impact-Improving-UI\.venv\Scripts\python.exe"
$ScriptPath = "C:\Users\semaa\OneDrive\Documents\Google\Agents4Impact-Improving-UI\data_ingestion\fetch_cdc_nrevss.py"
$WorkingDir = "C:\Users\semaa\OneDrive\Documents\Google\Agents4Impact-Improving-UI\data_ingestion"

# Create the action
$Action = New-ScheduledTaskAction `
    -Execute $PythonExe `
    -Argument $ScriptPath `
    -WorkingDirectory $WorkingDir

# Create the trigger - Run hourly
$Trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).Date `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration ([TimeSpan]::MaxValue)

# Create the task settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the scheduled task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $Description `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Force
    
    Write-Host "✓ Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The task will run hourly starting now." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To view the task:" -ForegroundColor Yellow
    Write-Host "  Task Scheduler → Task Scheduler Library → $TaskName" -ForegroundColor White
    Write-Host ""
    Write-Host "To run it manually now:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
    Write-Host "To disable hourly runs:" -ForegroundColor Yellow
    Write-Host "  Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠ WARNING: Hourly updates are NOT RECOMMENDED" -ForegroundColor Red
    Write-Host "CDC only updates this data weekly. Consider changing to weekly schedule." -ForegroundColor Red
}
catch {
    Write-Host "✗ Error creating scheduled task: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "You may need to run PowerShell as Administrator" -ForegroundColor Yellow
}
