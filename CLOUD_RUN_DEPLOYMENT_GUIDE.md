# Cloud Run Deployment Guide - Latest Code

**Date:** October 26, 2025
**Status:** Ready for Deployment
**Latest Commit:** 126046f3

---

## 🎯 DEPLOYMENT OPTIONS

You have **3 options** for deploying to Cloud Run:

### Option 1: GitHub Actions (Automated) ⭐ RECOMMENDED
### Option 2: Manual Cloud Build
### Option 3: Direct gcloud Deploy

---

## 📋 PRE-DEPLOYMENT CHECKLIST

### 1. Verify Latest Code is Pushed ✅
```bash
cd c:\Users\asggm\Agents4Good\agent4good
git status
git log --oneline -1
```

**Expected:**
- Status: clean working tree
- Latest commit: `126046f3 fix: Resolve ADK agent parent validation error...`

### 2. Check Dockerfile Configuration
**Current Issue:** Dockerfile references `app:app` but we use `app_local.py`

**Fix Needed:**
```dockerfile
# Change line 29 from:
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app

# To:
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app_local:app
```

### 3. Verify GitHub Secrets
Required secrets in your GitHub repo settings:
- `GCP_CREDENTIALS` - Service account JSON
- `GOOGLE_CLOUD_PROJECT` - Your project ID
- `SECRET_KEY` - Flask secret key
- `BIGQUERY_DATASET` - BigQuery dataset name
- `BIGQUERY_TABLE_REPORTS` - Community reports table
- `GOOGLE_API_KEY` - Google API key
- `GEMINI_API_KEY` - Gemini API key
- `EPA_API_KEY` - EPA API key
- `AQS_API_KEY` - AQS API key
- `AQS_EMAIL` - AQS email

---

## 🚀 OPTION 1: GITHUB ACTIONS (RECOMMENDED)

### Step-by-Step:

#### 1. Fix Dockerfile
```bash
# Open Dockerfile and change the CMD line
```

#### 2. Commit and Push
```bash
git add Dockerfile
git commit -m "fix: Update Dockerfile to use app_local.py for Cloud Run"
git push origin main
```

#### 3. Trigger Deployment
The push to `main` will automatically trigger the GitHub Actions workflow!

#### 4. Monitor Deployment
1. Go to: https://github.com/Yoha02/agent4good/actions
2. Click on the latest "Deploy to Production" workflow
3. Watch the progress

#### 5. Get Cloud Run URL
Once deployed, the URL will be:
```
https://agent4good-<hash>.run.app
```

---

## 🚀 OPTION 2: MANUAL CLOUD BUILD

### Step-by-Step:

#### 1. Authenticate with Google Cloud
```bash
gcloud auth login
gcloud config set project qwiklabs-gcp-00-4a7d408c735c
```

#### 2. Enable Required APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

#### 3. Build Docker Image
```bash
cd c:\Users\asggm\Agents4Good\agent4good

# Build and submit to Container Registry
gcloud builds submit --tag gcr.io/qwiklabs-gcp-00-4a7d408c735c/agent4good:latest
```

#### 4. Deploy to Cloud Run
```bash
gcloud run deploy agent4good \
  --image gcr.io/qwiklabs-gcp-00-4a7d408c735c/agent4good:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --port 8080
```

#### 5. Set Environment Variables
```bash
gcloud run services update agent4good \
  --region us-central1 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c" \
  --set-env-vars="BIGQUERY_DATASET=your_dataset" \
  --set-env-vars="GOOGLE_API_KEY=your_key" \
  --set-env-vars="GEMINI_API_KEY=your_key" \
  --set-env-vars="EPA_API_KEY=your_key" \
  --set-env-vars="AQS_API_KEY=your_key" \
  --set-env-vars="AQS_EMAIL=your_email"
```

---

## 🚀 OPTION 3: DIRECT GCLOUD DEPLOY (Fastest)

### Step-by-Step:

#### 1. Create .gcloudignore (if not exists)
```bash
echo "venv/" > .gcloudignore
echo "__pycache__/" >> .gcloudignore
echo "*.pyc" >> .gcloudignore
echo ".git/" >> .gcloudignore
echo ".env" >> .gcloudignore
```

#### 2. Deploy Directly from Source
```bash
cd c:\Users\asggm\Agents4Good\agent4good

gcloud run deploy agent4good \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

This will:
- Build from source automatically
- Create container image
- Deploy to Cloud Run

---

## 🔧 REQUIRED FIXES BEFORE DEPLOYMENT

### 1. Update Dockerfile ⚠️ CRITICAL
```dockerfile
# File: Dockerfile
# Line 29: Change from app:app to app_local:app

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app_local:app
```

### 2. Verify requirements.txt
Check that `requirements.txt` includes:
```
Flask
gunicorn
google-cloud-bigquery
google-cloud-storage
google-generativeai
google-cloud-texttospeech
# ... all other dependencies
```

### 3. Add gunicorn if missing
```bash
pip freeze | grep gunicorn
# If not found:
pip install gunicorn
pip freeze > requirements.txt
```

---

## 📊 DEPLOYMENT CONFIGURATION

### Recommended Cloud Run Settings:
```yaml
Service Name: agent4good
Region: us-central1
Memory: 2Gi (or 4Gi for better performance)
CPU: 2
Timeout: 300 seconds
Max Instances: 10
Min Instances: 0 (or 1 for always-on)
Concurrency: 80
Port: 8080
Allow Unauthenticated: Yes
```

### Environment Variables Needed:
```bash
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c
BIGQUERY_DATASET=<your_dataset>
BIGQUERY_TABLE_REPORTS=community_reports
GOOGLE_API_KEY=<your_key>
GEMINI_API_KEY=<your_key>
EPA_API_KEY=<your_key>
AQS_API_KEY=<your_key>
AQS_EMAIL=<your_email>
GCS_BUCKET=agent4good-report-attachments
PORT=8080
FLASK_ENV=production
```

---

## 🧪 POST-DEPLOYMENT TESTING

### 1. Test Health Endpoint
```bash
curl https://agent4good-<hash>.run.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "adk_agent": "available",
  "psa_video_feature": "available"
}
```

### 2. Test Chat Endpoint
```bash
curl -X POST https://agent4good-<hash>.run.app/api/agent-chat \
  -H "Content-Type: application/json" \
  -d '{"question": "what can you do?", "state": "California"}'
```

### 3. Test Frontend
Open in browser:
```
https://agent4good-<hash>.run.app
```

**Verify:**
- ✅ Page loads
- ✅ Chat works
- ✅ ADK agent responds
- ✅ No JavaScript errors

---

## 🐛 COMMON DEPLOYMENT ISSUES

### Issue 1: "Module not found: app"
**Cause:** Dockerfile references wrong file
**Fix:** Change `app:app` to `app_local:app` in Dockerfile

### Issue 2: "Port already in use"
**Cause:** Cloud Run default port mismatch
**Fix:** Ensure PORT=8080 in environment variables

### Issue 3: "Permission denied"
**Cause:** Service account missing permissions
**Fix:** Grant roles:
```bash
gcloud projects add-iam-policy-binding qwiklabs-gcp-00-4a7d408c735c \
  --member="serviceAccount:your-service-account@project.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Issue 4: "BigQuery connection failed"
**Cause:** Missing credentials
**Fix:** Ensure `GOOGLE_CLOUD_PROJECT` env var is set

### Issue 5: "Out of memory"
**Cause:** Insufficient memory allocation
**Fix:** Increase to 2Gi or 4Gi:
```bash
gcloud run services update agent4good --memory 4Gi --region us-central1
```

---

## 📝 DEPLOYMENT COMMANDS QUICK REFERENCE

### Check Status:
```bash
gcloud run services describe agent4good --region us-central1
```

### View Logs:
```bash
gcloud run services logs read agent4good --region us-central1 --limit 50
```

### Update Service:
```bash
gcloud run services update agent4good --region us-central1 [options]
```

### Delete Service:
```bash
gcloud run services delete agent4good --region us-central1
```

---

## ✅ STEP-BY-STEP RECOMMENDED DEPLOYMENT

### Quick Steps (5 minutes):

1. **Fix Dockerfile:**
   ```bash
   # Change line 29 to use app_local:app
   ```

2. **Commit and Push:**
   ```bash
   git add Dockerfile
   git commit -m "fix: Update Dockerfile for Cloud Run deployment"
   git push origin main
   ```

3. **Wait for GitHub Actions** (or deploy manually)

4. **Get URL and Test:**
   ```bash
   gcloud run services describe agent4good --region us-central1 --format='value(status.url)'
   ```

---

**Ready to deploy? Start with fixing the Dockerfile!**

