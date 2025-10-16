# Google Cloud SDK Installation Script for Windows
# Run this script in PowerShell to download and install Google Cloud SDK

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Google Cloud SDK Installation Script" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[WARNING] Not running as Administrator. Installation may require elevation." -ForegroundColor Yellow
    Write-Host ""
}

# Download URL
$installerUrl = "https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe"
$installerPath = "$env:TEMP\GoogleCloudSDKInstaller.exe"

Write-Host "[1/4] Downloading Google Cloud SDK installer..." -ForegroundColor Cyan
Write-Host "      From: $installerUrl" -ForegroundColor Gray
Write-Host "      To: $installerPath" -ForegroundColor Gray
Write-Host ""

try {
    # Download the installer
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    Write-Host "[SUCCESS] Download completed!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] Failed to download installer: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please download manually from:" -ForegroundColor Yellow
    Write-Host "https://cloud.google.com/sdk/docs/install-sdk#windows" -ForegroundColor Cyan
    exit 1
}

Write-Host "[2/4] Starting installer..." -ForegroundColor Cyan
Write-Host "      Please follow the installation wizard" -ForegroundColor Gray
Write-Host "      IMPORTANT: Check 'Start Cloud SDK Shell' and 'Run gcloud init'" -ForegroundColor Yellow
Write-Host ""

# Run the installer
try {
    Start-Process -FilePath $installerPath -Wait
    Write-Host "[SUCCESS] Installation completed!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "[ERROR] Installation failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host "[3/4] Cleaning up..." -ForegroundColor Cyan
Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
Write-Host "[SUCCESS] Cleanup completed!" -ForegroundColor Green
Write-Host ""

Write-Host "[4/4] Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. If the Cloud SDK Shell didn't open automatically, open a NEW PowerShell window" -ForegroundColor White
Write-Host "2. Run these commands to complete setup:" -ForegroundColor White
Write-Host ""
Write-Host "   # Authenticate with Google Cloud" -ForegroundColor Gray
Write-Host "   gcloud auth application-default login" -ForegroundColor Yellow
Write-Host ""
Write-Host "   # Set your project (replace with your project ID)" -ForegroundColor Gray
Write-Host "   gcloud config set project your-project-id" -ForegroundColor Yellow
Write-Host ""
Write-Host "   # Or for qwiklabs project:" -ForegroundColor Gray
Write-Host "   gcloud config set project qwiklabs-gcp-00-86088b6278cb" -ForegroundColor Yellow
Write-Host ""
Write-Host "   # Set environment variable" -ForegroundColor Gray
Write-Host "   `$env:GOOGLE_CLOUD_PROJECT = 'your-project-id'" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Test the agent:" -ForegroundColor White
Write-Host "   cd C:\Users\asggm\Agents4Good\agent4good" -ForegroundColor Yellow
Write-Host "   python interactive_demo.py" -ForegroundColor Yellow
Write-Host ""

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Installation script completed!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host ""
Write-Host "For detailed instructions, see: GOOGLE_CLOUD_SDK_SETUP.md" -ForegroundColor Cyan
Write-Host ""

