# BigQuery Data Verification Script
# Quick checks to verify all CDC data sources are working correctly

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "BigQuery CDC Data Verification" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to test Python script
function Test-PythonScript {
    param (
        [string]$Name,
        [string]$Script,
        [string]$TestCode
    )
    
    Write-Host "Testing $Name..." -ForegroundColor Yellow -NoNewline
    
    try {
        $output = python -c $TestCode 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host " ✅" -ForegroundColor Green
            if ($output) {
                Write-Host "  └─ $output" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host " ❌" -ForegroundColor Red
            Write-Host "  └─ $output" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "  └─ $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Test 1: CDC COVID Data Fetcher
Write-Host "`n1️⃣  CDC COVID Data Source" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$test1 = Test-PythonScript `
    -Name "COVID data fetcher" `
    -Script "fetch_external_feeds.py" `
    -TestCode "import sys; sys.path.insert(0, '.'); from fetch_external_feeds import CDCCovidDataFetcher; f = CDCCovidDataFetcher(); data = f.fetch_data(); print(f'{len(data)} records fetched') if data else print('No data')"

# Test 2: NREVSS Data Fetcher
Write-Host "`n2️⃣  NREVSS Respiratory Data Source" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$test2 = Test-PythonScript `
    -Name "NREVSS data fetcher" `
    -Script "fetch_cdc_nrevss.py" `
    -TestCode "import sys; sys.path.insert(0, '.'); from fetch_cdc_nrevss import fetch_nrevss_data; data = fetch_nrevss_data(100); print(f'{len(data)} records fetched') if data else print('No data')"

# Test 3: Respiratory Rates Fetcher
Write-Host "`n3️⃣  Respiratory Disease Rates (NEW)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
$test3 = Test-PythonScript `
    -Name "Respiratory rates fetcher" `
    -Script "fetch_respiratory_rates.py" `
    -TestCode "import sys; sys.path.insert(0, '.'); from fetch_respiratory_rates import fetch_respiratory_rates_data; data = fetch_respiratory_rates_data(100); print(f'{len(data)} records fetched') if data else print('No data')"

# Test 4: Check scheduled task
Write-Host "`n4️⃣  Weekly Schedule Status" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Checking scheduled task..." -ForegroundColor Yellow -NoNewline

$task = Get-ScheduledTask -TaskName "CDC_Respiratory_Rates_Weekly_Ingestion" -ErrorAction SilentlyContinue
if ($task) {
    Write-Host " ✅" -ForegroundColor Green
    Write-Host "  └─ Status: $($task.State)" -ForegroundColor Gray
    Write-Host "  └─ Next run: $($task.State)" -ForegroundColor Gray
    $test4 = $true
} else {
    Write-Host " ⚠️" -ForegroundColor Yellow
    Write-Host "  └─ Task not found. Run setup_weekly_respiratory_schedule.ps1 to create it." -ForegroundColor Yellow
    $test4 = $false
}

# Test 5: API Endpoint (requires Flask app to be running)
Write-Host "`n5️⃣  API Endpoint Test" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "Testing API endpoint..." -ForegroundColor Yellow -NoNewline

try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/respiratory-disease-rates?limit=10" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        Write-Host " ✅" -ForegroundColor Green
        Write-Host "  └─ Status: $($data.status)" -ForegroundColor Gray
        Write-Host "  └─ Records: $($data.count)" -ForegroundColor Gray
        $test5 = $true
    } else {
        Write-Host " ❌" -ForegroundColor Red
        Write-Host "  └─ Status code: $($response.StatusCode)" -ForegroundColor Red
        $test5 = $false
    }
} catch {
    Write-Host " ⚠️" -ForegroundColor Yellow
    Write-Host "  └─ Could not connect. Is Flask app running?" -ForegroundColor Yellow
    $test5 = $false
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Verification Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$passed = 0
$total = 5

if ($test1) { $passed++ }
if ($test2) { $passed++ }
if ($test3) { $passed++ }
if ($test4) { $passed++ }
if ($test5) { $passed++ }

Write-Host "Tests Passed: $passed / $total" -ForegroundColor $(if ($passed -eq $total) { "Green" } elseif ($passed -ge 3) { "Yellow" } else { "Red" })

Write-Host "`nStatus by Component:" -ForegroundColor Yellow
Write-Host "  COVID Data Source:       $(if ($test1) { '✅ Working' } else { '❌ Failed' })" -ForegroundColor $(if ($test1) { "Green" } else { "Red" })
Write-Host "  NREVSS Data Source:      $(if ($test2) { '✅ Working' } else { '❌ Failed' })" -ForegroundColor $(if ($test2) { "Green" } else { "Red" })
Write-Host "  Respiratory Rates:       $(if ($test3) { '✅ Working' } else { '❌ Failed' })" -ForegroundColor $(if ($test3) { "Green" } else { "Red" })
Write-Host "  Weekly Schedule:         $(if ($test4) { '✅ Configured' } else { '⚠️  Not Setup' })" -ForegroundColor $(if ($test4) { "Green" } else { "Yellow" })
Write-Host "  API Endpoint:            $(if ($test5) { '✅ Working' } else { '⚠️  Not Running' })" -ForegroundColor $(if ($test5) { "Green" } else { "Yellow" })

Write-Host "`nNext Steps:" -ForegroundColor Yellow

if (-not $test4) {
    Write-Host "  • Run: .\setup_weekly_respiratory_schedule.ps1" -ForegroundColor White
}

if (-not $test5) {
    Write-Host "  • Start Flask app: python app_local.py" -ForegroundColor White
}

if ($passed -lt 3) {
    Write-Host "  • Check error messages above" -ForegroundColor White
    Write-Host "  • Verify BigQuery credentials are configured" -ForegroundColor White
    Write-Host "  • Check internet connection to CDC API" -ForegroundColor White
}

if ($passed -eq $total) {
    Write-Host "`n🎉 All systems working! Your BQ data sources are ready." -ForegroundColor Green
}

Write-Host "`nFor detailed documentation, see:" -ForegroundColor Gray
Write-Host "  • QUICK_SUMMARY.md" -ForegroundColor Gray
Write-Host "  • BQ_UPDATES_README.md" -ForegroundColor Gray

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
