# Deploy to Cloud Run - Quick Start

**Status:** ✅ Code Ready for Deployment
**Latest Commit:** 78acf6b5

---

## 🚀 CHOOSE YOUR DEPLOYMENT METHOD

### Option A: GitHub Actions (Automated) ⭐ EASIEST

**The push to main will automatically trigger deployment!**

1. **Check GitHub Actions:**
   - Go to: https://github.com/Yoha02/agent4good/actions
   - Look for "Deploy to Production" workflow
   - It should be running now (triggered by your push)

2. **Monitor Progress:**
   - Click on the running workflow
   - Watch each step complete
   - Wait ~5-10 minutes

3. **Get Your URL:**
   - Once complete, check Cloud Run console
   - Or run: `gcloud run services describe agent4good --region us-central1 --format='value(status.url)'`

**That's it!** ✅

---

### Option B: Manual Deployment (5 minutes)

If GitHub Actions doesn't work or you prefer manual:

#### Step 1: Authenticate
```powershell
gcloud auth login
gcloud config set project qwiklabs-gcp-00-4a7d408c735c
```

#### Step 2: Deploy from Source
```powershell
cd c:\Users\asggm\Agents4Good\agent4good

gcloud run deploy agent4good `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --set-env-vars GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c
```

#### Step 3: Add Environment Variables
```powershell
gcloud run services update agent4good `
  --region us-central1 `
  --update-env-vars GOOGLE_API_KEY=YOUR_KEY `
  --update-env-vars GEMINI_API_KEY=YOUR_KEY `
  --update-env-vars EPA_API_KEY=YOUR_KEY `
  --update-env-vars AQS_API_KEY=YOUR_KEY `
  --update-env-vars AQS_EMAIL=YOUR_EMAIL
```

---

## 🧪 TESTING YOUR DEPLOYMENT

### 1. Get Service URL
```powershell
gcloud run services describe agent4good --region us-central1 --format='value(status.url)'
```

### 2. Test Health Check
```powershell
curl https://YOUR-SERVICE-URL/health
```

### 3. Open in Browser
```
https://YOUR-SERVICE-URL
```

**Test:**
- ✅ Page loads
- ✅ Ask "what can you do?"
- ✅ Check response from ADK agent
- ✅ No errors

---

## 📊 VIEW DEPLOYMENT STATUS

### Cloud Run Console:
https://console.cloud.google.com/run?project=qwiklabs-gcp-00-4a7d408c735c

### GitHub Actions:
https://github.com/Yoha02/agent4good/actions

### View Logs:
```powershell
gcloud run services logs read agent4good --region us-central1 --limit 50
```

---

## 🔧 IF DEPLOYMENT FAILS

### Check GitHub Secrets:
https://github.com/Yoha02/agent4good/settings/secrets/actions

**Required Secrets:**
- GCP_CREDENTIALS
- GOOGLE_CLOUD_PROJECT
- GOOGLE_API_KEY
- GEMINI_API_KEY
- EPA_API_KEY
- AQS_API_KEY
- AQS_EMAIL
- BIGQUERY_DATASET
- BIGQUERY_TABLE_REPORTS
- SECRET_KEY

### Manual Fix:
If automated deployment fails, use **Option B** above for manual deployment.

---

## ✅ POST-DEPLOYMENT CHECKLIST

- [ ] Service deployed successfully
- [ ] Health check returns 200
- [ ] Frontend loads in browser
- [ ] Chat works with ADK agent
- [ ] Air quality queries work
- [ ] Disease queries work
- [ ] PSA video generation works (optional test)
- [ ] No errors in Cloud Run logs

---

**Your deployment is ready! Check GitHub Actions or deploy manually.**

