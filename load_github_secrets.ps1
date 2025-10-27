# GitHub Secrets to Environment Variables
# This script fetches secret names from GitHub and prompts you to set them
# Usage: . .\load_github_secrets.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "🔐 GitHub Secrets Loader" -ForegroundColor Cyan  
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$ghPath = "C:\Program Files\GitHub CLI\gh.exe"
$repo = "Yoha02/agent4good"

# Check if gh is installed
if (-not (Test-Path $ghPath)) {
    Write-Host "❌ GitHub CLI not found" -ForegroundColor Red
    Write-Host "💡 Install with: winget install --id GitHub.cli" -ForegroundColor Yellow
    exit 1
}

# Check authentication
$authStatus = & $ghPath auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Not authenticated with GitHub" -ForegroundColor Red
    Write-Host "💡 Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ GitHub CLI authenticated" -ForegroundColor Green

# Fetch secret names
Write-Host "🔍 Fetching secrets from $repo..." -ForegroundColor Cyan
$secretsList = & $ghPath secret list --repo $repo 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to fetch secrets" -ForegroundColor Red
    Write-Host $secretsList -ForegroundColor Red
    exit 1
}

# Parse secret names
$secrets = @()
$secretsList -split "`n" | ForEach-Object {
    if ($_ -match '^(\S+)\s+') {
        $secretName = $Matches[1]
        if ($secretName -ne "NAME") {
            $secrets += $secretName
        }
    }
}

Write-Host "✅ Found $($secrets.Count) secrets" -ForegroundColor Green
Write-Host ""

# Load from .env file if it exists
$envFile = ".env"
$envVars = @{}

if (Test-Path $envFile) {
    Write-Host "📄 Loading values from .env file..." -ForegroundColor Cyan
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=(.+)$') {
            $key = $Matches[1]
            $value = $Matches[2]
            if ($value -notmatch '<SECRET_VALUE_FROM_GITHUB>') {
                $envVars[$key] = $value
            }
        }
    }
    Write-Host "✅ Loaded $($envVars.Count) values from .env" -ForegroundColor Green
}

# Set environment variables for this session
$setCount = 0
foreach ($secret in $secrets) {
    if ($envVars.ContainsKey($secret)) {
        $value = $envVars[$secret]
        [Environment]::SetEnvironmentVariable($secret, $value, "Process")
        Write-Host "   ✓ $secret = $($value.Substring(0, [Math]::Min(10, $value.Length)))..." -ForegroundColor Green
        $setCount++
    } else {
        Write-Host "   ✗ $secret (not in .env)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✅ Set $setCount environment variables" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Now you can run your Flask app:" -ForegroundColor Cyan
Write-Host "   python app_local.py" -ForegroundColor White
Write-Host ""
Write-Host "🔄 These variables are available in THIS terminal session only" -ForegroundColor Yellow
Write-Host ""
