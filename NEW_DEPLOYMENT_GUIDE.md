# 🚀 Deployment Guide for New GCP Environment

## Prerequisites Checklist

### ✅ **What You Need:**

1. **New Google Cloud Project**
   - Project ID (e.g., `your-new-project-id`)
   - Billing enabled
   - Owner or Editor permissions

2. **Gemini API Key**
   - Get from: https://aistudio.google.com/apikey
   - Free tier available
   - Should start with `AIzaSy...`

3. **Google Cloud SDK**
   - Already installed ✅
   - Authenticated to new project

4. **Code Repository**
   - Branch: `combined_UI_and_agent`
   - All code ready ✅

---

## Step-by-Step Deployment

### **Step 1: Create .env File**

Create a `.env` file in the project root with:

```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-new-project-id
BIGQUERY_DATASET=BQ_EPA_Air_Data

# Gemini API Configuration
GOOGLE_API_KEY=your-new-gemini-api-key
GEMINI_API_KEY=your-new-gemini-api-key
GOOGLE_GENAI_USE_VERTEXAI=FALSE

# Application Configuration
SECRET_KEY=your-random-secret-key-here
PORT=8080
```

**Replace**:
- `your-new-project-id` → Your actual GCP project ID
- `your-new-gemini-api-key` → Your new Gemini API key from AI Studio

---

### **Step 2: Enable Required APIs**

Open **Google Cloud SDK Shell** and run:

```bash
# Set your project
gcloud config set project your-new-project-id

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

**Time**: ~1 minute

---

### **Step 3: Set Up Authentication**

```bash
# Set up application default credentials
gcloud auth application-default login

# Set project environment variable
set GOOGLE_CLOUD_PROJECT=your-new-project-id
```

**Time**: ~2 minutes (browser will open for auth)

---

### **Step 4: (Optional) Set Up BigQuery Dataset**

If you want to use your own EPA data instead of demo data:

#### **Option A: Use Public EPA Dataset** (Recommended)
No setup needed! The app can query:
- Project: `bigquery-public-data`
- Dataset: `epa_historical_air_quality`
- Table: `pm25_frm_daily_summary`

Update `app.py` to use public dataset (I'll show you how below).

#### **Option B: Create Your Own Dataset**
```bash
# Create dataset
bq mk --dataset your-new-project-id:BQ_EPA_Air_Data

# Load data (if you have CSV files)
bq load --source_format=CSV --skip_leading_rows=1 \
  your-new-project-id:BQ_EPA_Air_Data.pm25_frm_daily_summary \
  your-epa-data.csv \
  date_local:DATE,state_name:STRING,county_name:STRING,aqi:INTEGER,...
```

---

### **Step 5: Deploy to Cloud Run**

#### **Method 1: One Command Deploy** (Easiest!)

```bash
cd C:\Users\asggm\Agents4Good\agent4good

gcloud run deploy community-health-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-new-project-id,GOOGLE_API_KEY=your-gemini-key,GOOGLE_GENAI_USE_VERTEXAI=FALSE \
  --memory 2Gi \
  --timeout 300
```

**Time**: ~6-8 minutes

#### **Method 2: Build Then Deploy** (More Control)

```bash
# Build container
gcloud builds submit --tag gcr.io/your-new-project-id/community-health-agent

# Deploy to Cloud Run
gcloud run deploy community-health-agent \
  --image gcr.io/your-new-project-id/community-health-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-new-project-id,GOOGLE_API_KEY=your-gemini-key,GOOGLE_GENAI_USE_VERTEXAI=FALSE \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

---

### **Step 6: Get Your Live URL**

After deployment completes:

```bash
gcloud run services describe community-health-agent \
  --region us-central1 \
  --format='value(status.url)'
```

You'll get a URL like:
```
https://community-health-agent-xxxxx-uc.a.run.app
```

**Open it in your browser!** 🎉

---

## 📋 What Gets Deployed

### **Application Components:**
✅ Flask web application (`app.py`)  
✅ Multi-agent ADK system (`multi_tool_agent_bquery_tools/`)  
✅ Beautiful UI (templates, static files)  
✅ All visualizations (D3.js, Chart.js, Three.js)  
✅ Chat interface with agent integration  

### **Environment Variables Set:**
- `GOOGLE_CLOUD_PROJECT` - Your project ID
- `GOOGLE_API_KEY` - Your Gemini API key
- `GOOGLE_GENAI_USE_VERTEXAI` - Set to FALSE

### **Resources Used:**
- Cloud Run service (2GB memory, 2 CPUs)
- Container Registry (for Docker image)
- Cloud Build (for building container)

---

## 🔧 Configuration Updates Needed

### **If Using Public EPA Dataset:**

Update `app.py` line ~56:

```python
# Change from:
project = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-86088b6278cb')
dataset = os.getenv('BIGQUERY_DATASET', 'BQ_EPA_Air_Data')

# To:
project = 'bigquery-public-data'
dataset = 'epa_historical_air_quality'
```

This lets you query real EPA data without creating your own dataset!

---

## 🧪 Testing Checklist

After deployment, test these URLs:

### **1. Health Check:**
```
https://your-service-url/health
Expected: {"status": "healthy"}
```

### **2. Main Dashboard:**
```
https://your-service-url/
Expected: Beautiful UI loads
```

### **3. Air Quality API:**
```
https://your-service-url/api/air-quality?days=7
Expected: JSON with air quality data
```

### **4. Chat Interface:**
Open the UI, scroll to chat, type:
```
"Hello!"
Expected: Welcome message from multi-agent system
```

---

## 📝 Complete Deployment Checklist

- [ ] Create new GCP project
- [ ] Note down project ID: `_______________`
- [ ] Get new Gemini API key from https://aistudio.google.com/apikey
- [ ] Note down API key: `AIzaSy_______________`
- [ ] Create `.env` file with project ID and API key
- [ ] Enable required APIs (cloudbuild, run, bigquery)
- [ ] Set up authentication (`gcloud auth application-default login`)
- [ ] (Optional) Update app.py to use public BigQuery dataset
- [ ] Run deployment command
- [ ] Test health endpoint
- [ ] Test main UI
- [ ] Test chat interface
- [ ] Share new URL! 🎉

---

## ⚡ Quick Deploy Script

Save this as `deploy_new_env.sh` or run directly:

```bash
#!/bin/bash

# Configuration
PROJECT_ID="your-new-project-id"
API_KEY="your-new-gemini-api-key"
REGION="us-central1"
SERVICE_NAME="community-health-agent"

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
echo "Enabling APIs..."
gcloud services enable cloudbuild.googleapis.com run.googleapis.com bigquery.googleapis.com

# Deploy
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_API_KEY=$API_KEY,GOOGLE_GENAI_USE_VERTEXAI=FALSE \
  --memory 2Gi \
  --timeout 300

# Get URL
echo ""
echo "Deployment complete!"
echo "Your app is live at:"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
```

---

## 🎯 What You Need to Provide

Before deploying, you need:

1. **New GCP Project ID**: `________________`
2. **New Gemini API Key**: `AIzaSy________________`
3. **Region** (recommended): `us-central1`

---

## 💰 Cost Estimate

**Free Tier Includes:**
- 2 million requests/month (Cloud Run)
- 1 TB of queries/month (BigQuery)
- First 10 GB storage free

**Expected Cost**: $0/month (stays in free tier for typical usage)

---

## 🐛 Troubleshooting

### **Build Fails:**
- Check `requirements.txt` is present
- Verify Dockerfile syntax
- Check build logs: `gcloud builds list`

### **Deploy Fails:**
- Ensure APIs are enabled
- Check you have permissions
- Verify environment variables are correct

### **App Returns Errors:**
- Check logs: `gcloud run services logs read community-health-agent --region us-central1`
- Verify API key is valid
- Test locally first: `python app.py`

---

## 📞 Need Help?

I can help you:
1. Create the `.env` file with your credentials
2. Update code to use public BigQuery dataset
3. Run the deployment commands
4. Debug any issues

**Just provide your new Project ID and API key, and I'll help you deploy!** 🚀

---

*Ready to deploy? Let me know your new project details!*

