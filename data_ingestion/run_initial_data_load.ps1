# Quick Start Script for BigQuery Data Updates
# This script runs the initial data load for all updated CDC data sources

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "BigQuery CDC Data Updates - Initial Load" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if we're in the right directory
if (-not (Test-Path (Join-Path $scriptPath "fetch_respiratory_rates.py"))) {
    Write-Host "❌ Error: Please run this script from the data_ingestion directory" -ForegroundColor Red
    exit 1
}

Write-Host "📋 This script will:" -ForegroundColor Yellow
Write-Host "  1. Load CDC COVID data (updated source)" -ForegroundColor White
Write-Host "  2. Load NREVSS respiratory data (updated source)" -ForegroundColor White
Write-Host "  3. Load NEW respiratory disease rates data" -ForegroundColor White
Write-Host "  4. Setup weekly schedule for respiratory rates" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Continue? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host "`n" -ForegroundColor White

# 1. Load CDC COVID data
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "1️⃣  Loading CDC COVID Data..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

python fetch_external_feeds.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ CDC COVID data loaded successfully`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  CDC COVID data load had errors (check logs)`n" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# 2. Load NREVSS data
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "2️⃣  Loading NREVSS Respiratory Data..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

python fetch_cdc_nrevss.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ NREVSS data loaded successfully`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  NREVSS data load had errors (check logs)`n" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# 3. Load respiratory disease rates data (NEW)
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "3️⃣  Loading Respiratory Disease Rates (NEW)..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

python fetch_respiratory_rates.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Respiratory disease rates loaded successfully`n" -ForegroundColor Green
} else {
    Write-Host "⚠️  Respiratory rates load had errors (check logs)`n" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# 4. Setup weekly schedule
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "4️⃣  Setting up Weekly Schedule..." -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan

Write-Host "Do you want to setup the weekly automatic ingestion? (y/n): " -NoNewline -ForegroundColor Yellow
$setupSchedule = Read-Host
if ($setupSchedule -eq 'y') {
    .\setup_weekly_respiratory_schedule.ps1
    Write-Host "✅ Weekly schedule configured`n" -ForegroundColor Green
} else {
    Write-Host "⏭️  Skipped schedule setup`n" -ForegroundColor Yellow
    Write-Host "   To setup later, run: .\setup_weekly_respiratory_schedule.ps1`n" -ForegroundColor Gray
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✨ Initial Data Load Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Verify data in BigQuery console" -ForegroundColor White
Write-Host "  2. Test the new API endpoint:" -ForegroundColor White
Write-Host "     http://localhost:5000/api/respiratory-disease-rates" -ForegroundColor Gray
Write-Host "  3. Add the new chart to your dashboard" -ForegroundColor White
Write-Host "  4. Review BQ_UPDATES_README.md for full documentation`n" -ForegroundColor White

Write-Host "Tables Updated:" -ForegroundColor Yellow
Write-Host "  • cdc_covid_data (updated source)" -ForegroundColor Green
Write-Host "  • nrevss_respiratory_data (updated source)" -ForegroundColor Green
Write-Host "  • respiratory_disease_rates (NEW!)" -ForegroundColor Green
Write-Host ""

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
