#!/bin/bash
# Cloud Run Deployment Script for Linux/macOS
# Usage: ./deploy.sh

set -e

echo "========================================"
echo "Air Quality Advisor - Cloud Run Deployment"
echo "========================================"
echo ""

# Check if gcloud is installed
echo "Checking for gcloud CLI..."
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed."
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "✓ gcloud CLI found"
echo ""

# Get project ID
read -p "Enter your Google Cloud Project ID: " PROJECT_ID
if [ -z "$PROJECT_ID" ]; then
    echo "Error: Project ID is required"
    exit 1
fi

# Get Gemini API Key
read -p "Enter your Gemini API Key: " GEMINI_API_KEY
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: Gemini API Key is required"
    exit 1
fi

# Set project
echo ""
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo ""
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com

# Build container
echo ""
echo "Building container image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/air-quality-advisor

echo "✓ Container built successfully"

# Deploy to Cloud Run
echo ""
echo "Deploying to Cloud Run..."
gcloud run deploy air-quality-advisor \
  --image gcr.io/$PROJECT_ID/air-quality-advisor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,BIGQUERY_DATASET=air_quality_dataset,BIGQUERY_TABLE=air_quality_data,GEMINI_API_KEY=$GEMINI_API_KEY"

echo ""
echo "========================================"
echo "✓ Deployment completed successfully!"
echo "========================================"
echo ""
echo "Your app is now live!"
echo ""
echo "To view your service URL, run:"
echo "  gcloud run services describe air-quality-advisor --region us-central1 --format='value(status.url)'"
echo ""
