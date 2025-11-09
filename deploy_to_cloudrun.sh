#!/bin/bash
# Cloud Run Deployment Script for Agent4Good
# Project: qwiklabs-gcp-00-4a7d408c735c
# Existing Service: https://agent4good-776464277441.us-central1.run.app

gcloud run deploy agent4good \
  --source . \
  --platform managed \
  --region us-central1 \
  --project qwiklabs-gcp-00-4a7d408c735c \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars="\
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,\
GEMINI_API_KEY=AIzaSyD-NH9KzOLmSKJmdqszwILplZs3kGL64eA,\
GOOGLE_API_KEY=AIzaSyD-NH9KzOLmSKJmdqszwILplZs3kGL64eA,\
GOOGLE_GENAI_USE_VERTEXAI=TRUE,\
GOOGLE_CLOUD_LOCATION=us-central1,\
BIGQUERY_DATASET=CrowdsourceData,\
BIGQUERY_TABLE_REPORTS=CrowdSourceData,\
BIGQUERY_TABLE=air_quality_data,\
GCS_VIDEO_BUCKET=qwiklabs-gcp-00-4a7d408c735c-psa-videos,\
FLASK_ENV=production,\
AIRNOW_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,\
EPA_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,\
AQS_API_KEY=bolewren34,\
AQS_EMAIL=ai2communities@gmail.com,\
FIREBASE_API_KEY=AIzaSyDTK4NBTDymbXtuRpNhbU9gDH1yX60JGw0,\
FIREBASE_AUTH_DOMAIN=qwiklabs-gcp-00-4a7d408c735c.firebaseapp.com,\
FIREBASE_PROJECT_ID=qwiklabs-gcp-00-4a7d408c735c,\
FIREBASE_STORAGE_BUCKET=qwiklabs-gcp-00-4a7d408c735c.firebasestorage.app,\
FIREBASE_MESSAGING_SENDER_ID=776464277441,\
FIREBASE_APP_ID=1:776464277441:web:f4faf70781e429a4671940,\
FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase-service-account,\
TWITTER_API_KEY=j1GPTU3weLMzs3PvIvj4nJmel,\
TWITTER_API_SECRET=FEpSdSCgsTJTSKByeXA9acbKLy9ACpTkoC84sJDbMPEURiRfnv,\
TWITTER_ACCESS_TOKEN=1982143243111497728-1oboZufxqKFp9Usr24MzehlqNWwIs6,\
TWITTER_ACCESS_TOKEN_SECRET=j3M73CcJgGfeT6xsYbtLUiZyNvXYOHFnYuPFxz7PptXUi,\
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAAsb5AEAAAAASSxf2Ih%2B5%2FNAnlj7HluY22iF9YM%3DglqoGZDXONwArW7TCKuYgtNJIcrl70n7a9kjF03X61j8ZkMqBJ,\
TWITTER_USERNAME=AI_mmunity" \
  --update-secrets="/secrets/firebase-service-account=firebase-service-account:latest"

echo ""
echo "✅ Deployment command executed!"
echo "🔗 Service URL: https://agent4good-776464277441.us-central1.run.app"
echo ""
echo "To check deployment status:"
echo "gcloud run services describe agent4good --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c"

