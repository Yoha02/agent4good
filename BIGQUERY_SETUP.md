# BigQuery EPA Dataset Connection Setup

## Prerequisites

1. **Google Cloud Account** with access to project: `qwiklabs-gcp-00-86088b6278cb`
2. **Python 3.11+** installed
3. **Google Cloud SDK** installed

## Step 1: Authenticate with Google Cloud

### Option A: Application Default Credentials (Recommended for Development)

```powershell
# Login to Google Cloud
gcloud auth application-default login

# Set your project
gcloud config set project qwiklabs-gcp-00-86088b6278cb
```

This will open a browser window for you to authenticate. Once complete, your credentials will be stored locally.

### Option B: Service Account Key (For Production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts?project=qwiklabs-gcp-00-86088b6278cb)
2. Create a service account or use existing one
3. Grant these roles:
   - `BigQuery Data Viewer`
   - `BigQuery Job User`
4. Create and download a JSON key
5. Save it as `service-account-key.json` in the project root
6. Update `.env` file with the path

## Step 2: Verify BigQuery Access

```powershell
# Test query to the EPA dataset
bq query --use_legacy_sql=false `
  "SELECT table_id, row_count `
   FROM qwiklabs-gcp-00-86088b6278cb.BQ_EPA_Air_Data.__TABLES__ `
   LIMIT 10"
```

## Step 3: Configure Gemini AI (Optional)

1. Get API key from: https://makersuite.google.com/app/apikey
2. Update `.env` file:
   ```
   GEMINI_API_KEY=your-actual-api-key
   ```

## Step 4: Run the Application

```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Run with EPA BigQuery connection
python app_epa.py
```

## Troubleshooting

### Issue: "Permission Denied" or "Access Denied"

**Solution**: Make sure you're authenticated and have access to the project:
```powershell
gcloud auth application-default login
gcloud projects list
```

### Issue: "Dataset not found"

**Solution**: Verify the dataset exists:
```powershell
bq ls qwiklabs-gcp-00-86088b6278cb:BQ_EPA_Air_Data
```

### Issue: "Tables not found"

**Solution**: List available tables:
```powershell
bq ls qwiklabs-gcp-00-86088b6278cb:BQ_EPA_Air_Data
```

### Issue: Application runs but shows "Demo Mode"

**Solution**: Check authentication:
```powershell
# Check current auth
gcloud auth list

# Check project
gcloud config get-value project

# Re-authenticate if needed
gcloud auth application-default login
```

## Understanding the EPA Dataset Structure

The application will automatically:
1. Explore the dataset structure on startup
2. Try multiple query patterns to find the correct table/column names
3. Fall back to demo data if connection fails

Common EPA air quality table structures:
- `daily_aqi_by_county` - Daily AQI by county
- `daily_aqi_by_cbsa` - Daily AQI by Core Based Statistical Area
- `hourly_*` - Hourly measurements
- `annual_*` - Annual summaries

## Dataset Information

**Project**: `qwiklabs-gcp-00-86088b6278cb`
**Dataset**: `BQ_EPA_Air_Data`
**Source**: EPA (Environmental Protection Agency) Air Quality System

## API Endpoints

Once running, test these endpoints:

1. **Dataset Info**:
   ```
   http://localhost:8080/api/dataset-info
   ```

2. **Air Quality Data**:
   ```
   http://localhost:8080/api/air-quality?state=California&days=7
   ```

3. **Health Recommendations**:
   ```
   http://localhost:8080/api/health-recommendations?state=Texas
   ```

## Next Steps

1. ✅ Authenticate with Google Cloud
2. ✅ Run `python app_epa.py`
3. ✅ Visit http://localhost:8080
4. ✅ Check the console output for dataset info
5. ✅ Test the application with real EPA data!

---

**Need Help?** The application will show detailed logs about:
- Connection status
- Available tables
- Column names
- Query attempts
