# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Prerequisites

1. **Install Python 3.11+**
   - Download from: https://www.python.org/downloads/

2. **Install Google Cloud SDK**
   - Download from: https://cloud.google.com/sdk/docs/install
   - After installation, run: `gcloud init`

### Step 2: Set Up Google Cloud

1. **Create a new project** (or use existing):
   ```powershell
   gcloud projects create YOUR-PROJECT-ID
   gcloud config set project YOUR-PROJECT-ID
   ```

2. **Enable billing** for your project in the Cloud Console

3. **Get Gemini API Key**:
   - Go to: https://makersuite.google.com/app/apikey
   - Create and copy your API key

### Step 3: Set Up BigQuery

Run the provided script:
```powershell
.\setup_bigquery.ps1
```

Or manually:
```powershell
# Create dataset
bq mk --dataset YOUR-PROJECT-ID:air_quality_dataset

# Create table
bq mk --table YOUR-PROJECT-ID:air_quality_dataset.air_quality_data ^
  date:DATE,state_name:STRING,county_name:STRING,aqi:INTEGER,parameter_name:STRING,site_name:STRING

# Load data
bq load --source_format=CSV --skip_leading_rows=1 ^
  air_quality_dataset.air_quality_data ^
  ..\daily_88101_2025\daily_88101_2025.csv
```

### Step 4: Configure Environment

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` with your values:
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   BIGQUERY_DATASET=air_quality_dataset
   BIGQUERY_TABLE=air_quality_data
   GEMINI_API_KEY=your-gemini-api-key
   SECRET_KEY=your-random-secret-key
   ```

### Step 5: Test Locally

1. **Create virtual environment**:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Set up service account** (for local testing):
   ```powershell
   gcloud auth application-default login
   ```

4. **Run the app**:
   ```powershell
   python app.py
   ```

5. **Open browser**: http://localhost:8080

### Step 6: Deploy to Cloud Run

Use the deployment script:
```powershell
.\deploy.ps1
```

Or manually:
```powershell
# Build container
gcloud builds submit --tag gcr.io/YOUR-PROJECT-ID/air-quality-advisor

# Deploy
gcloud run deploy air-quality-advisor ^
  --image gcr.io/YOUR-PROJECT-ID/air-quality-advisor ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR-PROJECT-ID,BIGQUERY_DATASET=air_quality_dataset,BIGQUERY_TABLE=air_quality_data,GEMINI_API_KEY=YOUR-KEY"
```

## 📊 Features to Test

Once deployed, test these features:

1. **Dashboard**:
   - View real-time AQI statistics
   - Filter by state
   - See 7-day trends

2. **AI Health Advisor**:
   - Ask: "What are the health risks of high AQI?"
   - Ask: "Should I exercise outdoors today?"
   - Ask: "What precautions should I take?"

3. **Data Explorer**:
   - Browse detailed air quality records
   - Sort and filter data

## 🔧 Troubleshooting

### Issue: "Permission denied" when accessing BigQuery

**Solution**: Make sure you've authenticated:
```powershell
gcloud auth application-default login
```

### Issue: "Module not found" errors

**Solution**: Activate virtual environment and reinstall:
```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: Gemini API errors

**Solution**: 
1. Verify API key is correct in `.env`
2. Check quota at: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas

### Issue: Cloud Run deployment fails

**Solution**: Check logs:
```powershell
gcloud run services logs read air-quality-advisor --limit=50
```

## 📱 API Endpoints

Test these endpoints directly:

1. **Health Check**:
   ```
   GET /health
   ```

2. **Air Quality Data**:
   ```
   GET /api/air-quality?state=California&days=7
   ```

3. **Health Recommendations**:
   ```
   GET /api/health-recommendations?state=California
   ```

4. **AI Analysis**:
   ```
   POST /api/analyze
   Body: {"question": "What are health impacts?", "days": 7}
   ```

## 🎉 Next Steps

1. Customize the UI colors in `static/css/style.css`
2. Add more states to the dropdown in `templates/index.html`
3. Configure custom domain for your Cloud Run service
4. Set up Cloud Monitoring for alerts
5. Add authentication if needed

## 💡 Tips

- Use Cloud Shell for easier setup (no local installation needed)
- Monitor costs in Cloud Console
- Set up budget alerts
- Use Cloud Run's auto-scaling features
- Enable Cloud CDN for faster static file delivery

## 📞 Need Help?

- Check the main README.md
- Review Cloud Run documentation: https://cloud.google.com/run/docs
- Check BigQuery docs: https://cloud.google.com/bigquery/docs
- Gemini AI docs: https://ai.google.dev/docs

---

**Happy Coding! 🚀**
