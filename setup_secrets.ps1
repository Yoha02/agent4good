# Interactive GitHub Secrets Loader
# Load secrets from .env file into environment variables
# Run with: . .\setup_secrets.ps1

Write-Host "`n================================" -ForegroundColor Cyan
Write-Host "Setup Secrets from GitHub" -ForegroundColor Cyan  
Write-Host "================================`n" -ForegroundColor Cyan

Write-Host "Opening GitHub Secrets page..." -ForegroundColor Cyan
Start-Process "https://github.com/Yoha02/agent4good/settings/secrets/actions"

Write-Host "`nCopy each secret value from GitHub and update your .env file"
Write-Host "Then run this script with -FromFile flag`n" -ForegroundColor Yellow

    Write-Host "Loading from .env file..." -ForegroundColor Green
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=(.+)$') {
            $key = $Matches[1]
            $value = $Matches[2]
            if ($value -notmatch '<SECRET_VALUE_FROM_GITHUB>') {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
                Write-Host "   Set: $key" -ForegroundColor Green
            }
        }
    }
    Write-Host "`nEnvironment variables loaded!`n" -ForegroundColor Green
} else {
    Write-Host ".env file not found" -ForegroundColor Red
}

Write-Host "To run your app: python app_local.py" -ForegroundColor Cyan
