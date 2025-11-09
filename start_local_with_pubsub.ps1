# Start local Flask app with Pub/Sub enabled
# Use this to test before deploying to Cloud Run

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Starting Local Flask App with Pub/Sub ENABLED" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Set environment variables
$env:USE_PUBSUB = "true"
$env:GOOGLE_CLOUD_PROJECT = "qwiklabs-gcp-00-4a7d408c735c"
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"

# Additional environment variables from Cloud Run
$env:BIGQUERY_DATASET = "CrowdsourceData"
$env:BIGQUERY_TABLE_REPORTS = "CrowdSourceData"

Write-Host ""
Write-Host "[OK] Environment Variables Set:" -ForegroundColor Green
Write-Host "  USE_PUBSUB: $env:USE_PUBSUB" -ForegroundColor Yellow
Write-Host "  GOOGLE_CLOUD_PROJECT: $env:GOOGLE_CLOUD_PROJECT" -ForegroundColor Yellow
Write-Host "  FLASK_ENV: $env:FLASK_ENV" -ForegroundColor Yellow
Write-Host ""
Write-Host "[INFO] Starting Flask app..." -ForegroundColor Cyan
Write-Host "  App will be available at: http://localhost:8080" -ForegroundColor White
Write-Host ""
Write-Host "[INFO] With Pub/Sub enabled, reports will be:" -ForegroundColor Cyan
Write-Host "  1. Published to Pub/Sub topic 'community-reports-submitted'" -ForegroundColor White
Write-Host "  2. Processed by Cloud Run worker 'bigquery-worker'" -ForegroundColor White
Write-Host "  3. Inserted into BigQuery by the worker" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Start Flask
python app_local.py

