# Simple Script to Load Secrets from .env
# Run: . .\load_env.ps1

Write-Host "Loading secrets from .env file..." -ForegroundColor Cyan

if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=(.+)$') {
            $key = $Matches[1]
            $value = $Matches[2]
            if ($value -notmatch '<SECRET_VALUE_FROM_GITHUB>') {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
                Write-Host "Set: $key" -ForegroundColor Green
            }
        }
    }
    Write-Host "`nDone! Run: python app_local.py" -ForegroundColor Green
} else {
    Write-Host "Error: .env file not found" -ForegroundColor Red
}
