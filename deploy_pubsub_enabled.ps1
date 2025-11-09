# Deploy updated application to Cloud Run with Pub/Sub enabled
# This deploys the full application with all Pub/Sub code changes

Write-Host "================================" -ForegroundColor Cyan
Write-Host "DEPLOYING UPDATED APPLICATION" -ForegroundColor Cyan
Write-Host "With Pub/Sub Integration" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$PROJECT_ID = "qwiklabs-gcp-00-4a7d408c735c"
$REGION = "us-central1"
$SERVICE_NAME = "agent4good"

Write-Host "[INFO] Deployment Configuration:" -ForegroundColor Cyan
Write-Host "  Project: $PROJECT_ID" -ForegroundColor White
Write-Host "  Region: $REGION" -ForegroundColor White
Write-Host "  Service: $SERVICE_NAME" -ForegroundColor White
Write-Host "  Pub/Sub: ENABLED (USE_PUBSUB=true)" -ForegroundColor Green
Write-Host ""

# Confirm deployment
Write-Host "[WARNING] This will deploy a NEW revision with updated code" -ForegroundColor Yellow
Write-Host "  - All Pub/Sub code changes will be deployed" -ForegroundColor Yellow
Write-Host "  - USE_PUBSUB will be set to 'true'" -ForegroundColor Yellow
Write-Host "  - New container will be built (~5-15 minutes)" -ForegroundColor Yellow
Write-Host ""
$confirmation = Read-Host "Continue with deployment? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host ""
    Write-Host "[CANCELLED] Deployment cancelled by user" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "STEP 1: Building and Deploying" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] This may take 10-20 minutes..." -ForegroundColor Yellow
Write-Host ""

# Deploy with all environment variables
gcloud run deploy $SERVICE_NAME `
  --source . `
  --region $REGION `
  --platform managed `
  --allow-unauthenticated `
  --memory 4Gi `
  --cpu 2 `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 10 `
  --set-env-vars="USE_PUBSUB=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_PROJECT_ID=$PROJECT_ID,BIGQUERY_DATASET_ID=CrowdsourceData,BIGQUERY_TABLE_NAME_COMMUNITY_REPORTS=CrowdSourceData,FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase-service-account" `
  --update-secrets="/secrets/firebase-service-account=firebase-service-account:latest"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Green
    Write-Host "DEPLOYMENT SUCCESS!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    
    # Get service URL
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
    
    Write-Host "[SUCCESS] Application deployed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[INFO] New Features:" -ForegroundColor Cyan
    Write-Host "  - Pub/Sub publishing for community reports" -ForegroundColor White
    Write-Host "  - Asynchronous BigQuery writes via worker" -ForegroundColor White
    Write-Host "  - Faster response times for users" -ForegroundColor White
    Write-Host "  - Feature flag enabled (USE_PUBSUB=true)" -ForegroundColor White
    Write-Host ""
    Write-Host "[INFO] Verification Steps:" -ForegroundColor Cyan
    Write-Host "  1. Visit: $SERVICE_URL" -ForegroundColor White
    Write-Host "  2. Submit a test report" -ForegroundColor White
    Write-Host "  3. Check worker logs:" -ForegroundColor White
    Write-Host "     gcloud logging read `"resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker`" --limit 10 --freshness=5m" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[INFO] Rollback if needed:" -ForegroundColor Cyan
    Write-Host "     gcloud run services update $SERVICE_NAME --region $REGION --update-env-vars=`"USE_PUBSUB=false`"" -ForegroundColor Gray
    Write-Host ""
    
} else {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Red
    Write-Host "DEPLOYMENT FAILED!" -ForegroundColor Red
    Write-Host "================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "[ERROR] Deployment encountered an error" -ForegroundColor Red
    Write-Host ""
    Write-Host "[INFO] Common issues:" -ForegroundColor Yellow
    Write-Host "  1. Build timeout (large codebase)" -ForegroundColor White
    Write-Host "     Solution: Try again, Cloud Build may succeed on retry" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2. Permission errors" -ForegroundColor White
    Write-Host "     Solution: Check IAM permissions" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3. Network issues" -ForegroundColor White
    Write-Host "     Solution: Check internet connection and retry" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[INFO] To retry deployment, run this script again" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Deployment completed at $(Get-Date)" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

