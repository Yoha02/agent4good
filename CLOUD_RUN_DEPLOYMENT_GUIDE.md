# Cloud Run Deployment Guide - Agent4Good

**Date**: October 27, 2025  
**Branch**: `main` (production-ready)

---

## 🚀 Quick Deploy Command

```bash
gcloud run services update agent4good \
  --region us-central1 \
  --update-env-vars GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,BIGQUERY_TABLE=air_quality_data,BIGQUERY_DATASET=CrowdsourceData,BIGQUERY_TABLE_REPORTS=CrowdSourceData,GEMINI_API_KEY=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk,FLASK_ENV=production,SECRET_KEY=your-secret-key-here,GOOGLE_API_KEY=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=us-central1,GCS_VIDEO_BUCKET=qwiklabs-gcp-00-4a7d408c735c-psa-videos,TWITTER_API_KEY=j1GPTU3weLMzs3PvIvj4nJmel,TWITTER_API_SECRET=FEpSdSCgsTJTSKByeXA9acbKLy9ACpTkoC84sJDbMPEURiRfnv,TWITTER_ACCESS_TOKEN=1982143243111497728-1oboZufxqKFp9Usr24MzehlqNWwIs6,TWITTER_ACCESS_TOKEN_SECRET=j3M73CcJgGfeT6xsYbtLUiZyNvXYOHFnYuPFxz7PptXUi,TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAAsb5AEAAAAASSxf2Ih%2B5%2FNAnlj7HluY22iF9YM%3DglqoGZDXONwArW7TCKuYgtNJIcrl70n7a9kjF03X61j8ZkMqBJ,TWITTER_USERNAME=AI_mmunity,AIRNOW_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,EPA_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,AQS_API_KEY=bolewren34,AQS_EMAIL=ai2communities@gmail.com
```

---

## 📋 Step-by-Step Deployment

### **Step 1: Verify You're on Main Branch**
```bash
git status
# Should show: On branch main
# Should show: Your branch is up to date with 'origin/main'
```

### **Step 2: Build and Deploy (First Time)**
If this is your first deployment or you need to rebuild the container:

```bash
# Build the container image
gcloud builds submit --tag gcr.io/qwiklabs-gcp-00-4a7d408c735c/agent4good

# Deploy to Cloud Run
gcloud run deploy agent4good \
  --image gcr.io/qwiklabs-gcp-00-4a7d408c735c/agent4good \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,BIGQUERY_TABLE=air_quality_data,BIGQUERY_DATASET=CrowdsourceData,BIGQUERY_TABLE_REPORTS=CrowdSourceData,GEMINI_API_KEY=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk,FLASK_ENV=production,SECRET_KEY=your-secret-key-here,GOOGLE_API_KEY=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=us-central1,GCS_VIDEO_BUCKET=qwiklabs-gcp-00-4a7d408c735c-psa-videos,TWITTER_API_KEY=j1GPTU3weLMzs3PvIvj4nJmel,TWITTER_API_SECRET=FEpSdSCgsTJTSKByeXA9acbKLy9ACpTkoC84sJDbMPEURiRfnv,TWITTER_ACCESS_TOKEN=1982143243111497728-1oboZufxqKFp9Usr24MzehlqNWwIs6,TWITTER_ACCESS_TOKEN_SECRET=j3M73CcJgGfeT6xsYbtLUiZyNvXYOHFnYuPFxz7PptXUi,TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAAsb5AEAAAAASSxf2Ih%2B5%2FNAnlj7HluY22iF9YM%3DglqoGZDXONwArW7TCKuYgtNJIcrl70n7a9kjF03X61j8ZkMqBJ,TWITTER_USERNAME=AI_mmunity,AIRNOW_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,EPA_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,AQS_API_KEY=bolewren34,AQS_EMAIL=ai2communities@gmail.com \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

### **Step 3: Update Existing Service (Faster)**
If the service already exists and you just want to update environment variables:

```bash
gcloud run services update agent4good \
  --region us-central1 \
  --update-env-vars GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,BIGQUERY_TABLE=air_quality_data,BIGQUERY_DATASET=CrowdsourceData,BIGQUERY_TABLE_REPORTS=CrowdSourceData,GEMINI_API_KEY=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk,FLASK_ENV=production,SECRET_KEY=your-secret-key-here,GOOGLE_API_KEY=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=us-central1,GCS_VIDEO_BUCKET=qwiklabs-gcp-00-4a7d408c735c-psa-videos,TWITTER_API_KEY=j1GPTU3weLMzs3PvIvj4nJmel,TWITTER_API_SECRET=FEpSdSCgsTJTSKByeXA9acbKLy9ACpTkoC84sJDbMPEURiRfnv,TWITTER_ACCESS_TOKEN=1982143243111497728-1oboZufxqKFp9Usr24MzehlqNWwIs6,TWITTER_ACCESS_TOKEN_SECRET=j3M73CcJgGfeT6xsYbtLUiZyNvXYOHFnYuPFxz7PptXUi,TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAAsb5AEAAAAASSxf2Ih%2B5%2FNAnlj7HluY22iF9YM%3DglqoGZDXONwArW7TCKuYgtNJIcrl70n7a9kjF03X61j8ZkMqBJ,TWITTER_USERNAME=AI_mmunity,AIRNOW_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,EPA_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,AQS_API_KEY=bolewren34,AQS_EMAIL=ai2communities@gmail.com
```

---

## 🔑 What Changed in API Keys

### **Updated Keys** ✅
1. **AIRNOW_API_KEY**: 
   - **Old**: `87FB7DB4-DDE6-4FDB-B214-3948D35ADE59`
   - **New**: `9C499E45-D997-4DC2-9337-B20B1E2EC659` ✅

2. **EPA_API_KEY**: 
   - **Old**: `87FB7DB4-DDE6-4FDB-B214-3948D35ADE59`
   - **New**: `9C499E45-D997-4DC2-9337-B20B1E2EC659` ✅

3. **AQS_API_KEY**:
   - **Old**: `ochregazelle35`
   - **New**: `bolewren34` ✅

4. **AQS_EMAIL**:
   - **Old**: `sema.`
   - **New**: `ai2communities@gmail.com` ✅

### **Unchanged Keys** (Same as before)
- GOOGLE_CLOUD_PROJECT
- GEMINI_API_KEY
- GOOGLE_API_KEY
- Twitter credentials
- BigQuery configuration

---

## 📝 Environment Variables Breakdown

| Variable | Value | Purpose |
|----------|-------|---------|
| `GOOGLE_CLOUD_PROJECT` | `qwiklabs-gcp-00-4a7d408c735c` | GCP Project ID |
| `BIGQUERY_DATASET` | `CrowdsourceData` | BigQuery dataset name |
| `BIGQUERY_TABLE` | `air_quality_data` | Air quality data table |
| `BIGQUERY_TABLE_REPORTS` | `CrowdSourceData` | Reports table |
| `GEMINI_API_KEY` | `AIzaSy...` | Gemini AI API key |
| `GOOGLE_API_KEY` | `AIzaSy...` | Google API key for ADK |
| `GOOGLE_GENAI_USE_VERTEXAI` | `TRUE` | Enable Vertex AI |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` | Region for services |
| `GCS_VIDEO_BUCKET` | `...-psa-videos` | Video storage bucket |
| `AIRNOW_API_KEY` | `9C499E45...` | **NEW** EPA AirNow API key |
| `EPA_API_KEY` | `9C499E45...` | **NEW** EPA API key |
| `AQS_API_KEY` | `bolewren34` | **NEW** AQS API username |
| `AQS_EMAIL` | `ai2communities@gmail.com` | **NEW** AQS API email |
| `TWITTER_API_KEY` | `j1GPTU3...` | Twitter API key |
| `TWITTER_API_SECRET` | `FEpSd...` | Twitter API secret |
| `TWITTER_ACCESS_TOKEN` | `1982143...` | Twitter access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | `j3M73...` | Twitter token secret |
| `TWITTER_BEARER_TOKEN` | `AAAAA...` | Twitter bearer token |
| `TWITTER_USERNAME` | `AI_mmunity` | Twitter username |
| `FLASK_ENV` | `production` | Flask environment |
| `SECRET_KEY` | `your-secret-key-here` | Flask secret key |

---

## ✅ Post-Deployment Verification

### **1. Check Service Status**
```bash
gcloud run services describe agent4good --region us-central1
```

### **2. Get Service URL**
```bash
gcloud run services describe agent4good --region us-central1 --format='value(status.url)'
```

### **3. Test Endpoints**
```bash
# Health check
curl https://YOUR-SERVICE-URL.run.app/

# Air quality API
curl https://YOUR-SERVICE-URL.run.app/api/air-quality

# Weather API
curl https://YOUR-SERVICE-URL.run.app/api/weather
```

### **4. View Logs**
```bash
gcloud run services logs read agent4good --region us-central1 --limit 50
```

---

## 🔍 Troubleshooting

### **Issue: EPA API Key Not Working**
```bash
# Check if the new key is set correctly
gcloud run services describe agent4good --region us-central1 --format='value(spec.template.spec.containers[0].env)'
```

### **Issue: Service Not Starting**
```bash
# Check recent logs for errors
gcloud run services logs read agent4good --region us-central1 --limit 100

# Common issues:
# - Missing environment variables
# - BigQuery permission errors
# - Memory/CPU limits too low
```

### **Issue: API Rate Limiting**
- The 10-minute cache should prevent this
- Check logs for `[CACHE HIT]` vs `[CACHE MISS]` patterns
- Verify EPA API key is valid: https://docs.airnowapi.org/

---

## 📊 Expected Performance

### **Cache Behavior**
- **First request**: `[CACHE MISS]` → EPA API call
- **Subsequent requests (< 10 min)**: `[CACHE HIT]` → No EPA call
- **After 10 minutes**: Cache expires → Fresh data on next request

### **Resource Usage**
- **Memory**: 2GB (recommended)
- **CPU**: 2 cores (recommended)
- **Timeout**: 300 seconds (5 minutes)
- **Max Instances**: 10 (auto-scales)

### **API Call Reduction**
- **Before caching**: ~100-200 EPA calls per page load
- **After caching**: ~5-10 EPA calls per page load
- **Reduction**: ~90-95% fewer API calls

---

## 🎯 Quick Reference

### **Deploy with New Code**
```bash
gcloud builds submit --tag gcr.io/qwiklabs-gcp-00-4a7d408c735c/agent4good && \
gcloud run deploy agent4good \
  --image gcr.io/qwiklabs-gcp-00-4a7d408c735c/agent4good \
  --region us-central1 \
  --allow-unauthenticated
```

### **Update Environment Variables Only**
```bash
gcloud run services update agent4good --region us-central1 --update-env-vars KEY=VALUE
```

### **View Current Configuration**
```bash
gcloud run services describe agent4good --region us-central1
```

---

## 🚨 Important Notes

1. **API Keys**: Store these securely! Don't commit to git.
2. **Rate Limits**: EPA allows 500 calls/hour. Caching keeps us well below.
3. **BigQuery**: Ensure service account has proper permissions.
4. **Twitter**: Rate limits apply (300 posts/3 hours).
5. **Backup**: `main_backup` branch available for rollback.

---

## 🎉 Deployment Checklist

- [ ] Git status shows `main` branch
- [ ] All changes pushed to `origin/main`
- [ ] Environment variables updated with new API keys
- [ ] Service deployed to Cloud Run
- [ ] Service URL accessible
- [ ] Health check passes
- [ ] API endpoints returning data
- [ ] Logs show proper caching behavior
- [ ] EPA API calls reduced
- [ ] Twitter posting works (if tested)

---

**Ready to Deploy!** 🚀

Use the commands above to get your updated application live on Cloud Run!
