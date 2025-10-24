# Deployment Script for New GCP Project
# Project: qwiklabs-gcp-00-4a7d408c735c

$PROJECT_ID = "qwiklabs-gcp-00-4a7d408c735c"
$API_KEY = "AIzaSyAcq1AUFa-n4l_vmwtb3-DP1YpXzOj-zGM"
$REGION = "us-central1"
$SERVICE_NAME = "community-health-agent"

Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host "DEPLOYING TO NEW GCP PROJECT" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host ""
Write-Host "Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Region: $REGION" -ForegroundColor Yellow
Write-Host ""

# Check if in Cloud SDK Shell
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] gcloud not found!" -ForegroundColor Red
    Write-Host "Please run this script in Google Cloud SDK Shell" -ForegroundColor Yellow
    Write-Host "Or open a NEW PowerShell window (to get updated PATH)" -ForegroundColor Yellow
    exit 1
}

Write-Host "[1/6] Setting project..." -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

Write-Host ""
Write-Host "[2/6] Enabling APIs..." -ForegroundColor Cyan
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable run.googleapis.com --quiet
gcloud services enable bigquery.googleapis.com --quiet
Write-Host "  [OK] APIs enabled" -ForegroundColor Green

Write-Host ""
Write-Host "[3/6] Checking authentication..." -ForegroundColor Cyan
$authStatus = gcloud auth application-default print-access-token 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARNING] Need to authenticate" -ForegroundColor Yellow
    Write-Host "  Running: gcloud auth application-default login" -ForegroundColor Gray
    gcloud auth application-default login
}
else {
    Write-Host "  [OK] Already authenticated" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/6] Building and deploying to Cloud Run..." -ForegroundColor Cyan
Write-Host "  This will take 6-8 minutes..." -ForegroundColor Gray
Write-Host ""

gcloud run deploy $SERVICE_NAME `
  --source . `
  --region $REGION `
  --allow-unauthenticated `
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_API_KEY=$API_KEY,GOOGLE_GENAI_USE_VERTEXAI=FALSE,BIGQUERY_DATASET=BQ_EPA_Air_Data" `
  --memory 2Gi `
  --timeout 300 `
  --max-instances 10

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Deployment failed" -ForegroundColor Red
    Write-Host "Check the error messages above" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[5/6] Getting service URL..." -ForegroundColor Cyan
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'

Write-Host ""
Write-Host "[6/6] Testing deployment..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "$SERVICE_URL/health" -UseBasicParsing -TimeoutSec 10
    Write-Host "  [OK] Service is responding!" -ForegroundColor Green
}
catch {
    Write-Host "  [WARNING] Service not responding yet, may need a moment to start" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host "[SUCCESS] DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=" -NoNewline; Write-Host ("=" * 79)
Write-Host ""
Write-Host "Your app is live at:" -ForegroundColor Cyan
Write-Host "  $SERVICE_URL" -ForegroundColor Green
Write-Host ""
Write-Host "Opening in browser..." -ForegroundColor Yellow
Start-Process $SERVICE_URL
Write-Host ""
Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  gcloud run services logs read $SERVICE_NAME --region $REGION" -ForegroundColor Gray
Write-Host ""

