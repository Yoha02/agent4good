# Complete Google Cloud Setup Script
# Run this in Cloud SDK Shell or PowerShell

Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host "Completing Google Cloud Setup for Agent" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host ""

Write-Host "[Step 1/4] Setting up Application Default Credentials..." -ForegroundColor Yellow
Write-Host "This will open your browser to authenticate." -ForegroundColor Gray
Write-Host ""
Write-Host "Run this command:" -ForegroundColor White
Write-Host "gcloud auth application-default login" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key after you've completed authentication in the browser..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

Write-Host "[Step 2/4] Setting project..." -ForegroundColor Yellow
$project = "qwiklabs-gcp-00-86088b6278cb"
Write-Host "Run this command:" -ForegroundColor White
Write-Host "gcloud config set project $project" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key after running the command..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
Write-Host ""

Write-Host "[Step 3/4] Setting environment variable..." -ForegroundColor Yellow
$env:GOOGLE_CLOUD_PROJECT = $project
Write-Host "Set GOOGLE_CLOUD_PROJECT = $project" -ForegroundColor Green
Write-Host ""

Write-Host "[Step 4/4] Verification..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Please run these commands to verify:" -ForegroundColor White
Write-Host "gcloud config get-value project" -ForegroundColor Cyan
Write-Host "gcloud auth application-default print-access-token" -ForegroundColor Cyan
Write-Host ""

Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host "After verification, run the agent with:" -ForegroundColor Green
Write-Host "cd C:\Users\asggm\Agents4Good\agent4good" -ForegroundColor Yellow
Write-Host "python interactive_demo.py" -ForegroundColor Yellow
Write-Host "=" -NoNewline; Write-Host ("=" * 79)

