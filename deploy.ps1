# Cloud Run Deployment Script for Windows PowerShell
# Usage: .\deploy.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Air Quality Advisor - Cloud Run Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
Write-Host "Checking for gcloud CLI..." -ForegroundColor Yellow
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI is not installed." -ForegroundColor Red
    Write-Host "Please install it from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

Write-Host "✓ gcloud CLI found" -ForegroundColor Green
Write-Host ""

# Get project ID
$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
if ([string]::IsNullOrWhiteSpace($PROJECT_ID)) {
    Write-Host "Error: Project ID is required" -ForegroundColor Red
    exit 1
}

# Get Gemini API Key
$GEMINI_API_KEY = Read-Host "Enter your Gemini API Key"
if ([string]::IsNullOrWhiteSpace($GEMINI_API_KEY)) {
    Write-Host "Error: Gemini API Key is required" -ForegroundColor Red
    exit 1
}

# Set project
Write-Host ""
Write-Host "Setting project to $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Enable required APIs
Write-Host ""
Write-Host "Enabling required APIs..." -ForegroundColor Yellow
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com

# Build container
Write-Host ""
Write-Host "Building container image..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/$PROJECT_ID/air-quality-advisor

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Container build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Container built successfully" -ForegroundColor Green

# Deploy to Cloud Run
Write-Host ""
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy air-quality-advisor `
  --image gcr.io/$PROJECT_ID/air-quality-advisor `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=air_quality_dataset,BIGQUERY_TABLE=air_quality_data,GEMINI_API_KEY=$GEMINI_API_KEY"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Deployment failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Deployment completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your app is now live!" -ForegroundColor Cyan
Write-Host ""
Write-Host "To view your service URL, run:" -ForegroundColor Yellow
Write-Host "  gcloud run services describe air-quality-advisor --region us-central1 --format='value(status.url)'" -ForegroundColor White
Write-Host ""
