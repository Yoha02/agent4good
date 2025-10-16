# Quick Start - Connect to EPA BigQuery Data

## 🚀 Option 1: Service Account Authentication (Fastest)

This is the easiest way to get started without installing Google Cloud SDK.

### Step 1: Get Service Account Key

1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts?project=qwiklabs-gcp-00-86088b6278cb
2. Click **"+ CREATE SERVICE ACCOUNT"** or select an existing one
3. Grant permissions:
   - **BigQuery Data Viewer**
   - **BigQuery Job User**
4. Click on the service account email
5. Go to **KEYS** tab → **ADD KEY** → **Create new key**
6. Choose **JSON** format and download
7. Save the file as `service-account-key.json` in the `agent4good` folder

### Step 2: Update .env File

Edit the `.env` file and add this line:
```
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
```

Your `.env` file should now look like:
```env
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-86088b6278cb
BIGQUERY_DATASET=BQ_EPA_Air_Data
GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json

# Gemini AI Configuration (Optional)
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your-api-key-here
```

### Step 3: Run the EPA-Connected App

```powershell
# Make sure you're in the agent4good folder
cd "c:\Users\semaa\OneDrive\Documents\Google\Agents4Impact10162025\AIr Quality\agent4good"

# Activate virtual environment
.\venv\Scripts\activate

# Run the EPA version
python app_epa.py
```

### Step 4: Open Your Browser

Visit: http://localhost:8080

---

## 🔧 Option 2: Install Google Cloud SDK (More Control)

If you want full Google Cloud CLI capabilities:

### Step 1: Download and Install

1. Visit: https://cloud.google.com/sdk/docs/install-sdk#windows
2. Download: `GoogleCloudSDKInstaller.exe`
3. Run the installer
4. Follow the installation wizard

### Step 2: Authenticate

```powershell
# Login to Google Cloud
gcloud auth application-default login

# Set your project
gcloud config set project qwiklabs-gcp-00-86088b6278cb

# Verify access
gcloud projects describe qwiklabs-gcp-00-86088b6278cb
```

### Step 3: Run the App

```powershell
# Run the EPA version
python app_epa.py
```

---

## 📊 What to Expect

When you run `app_epa.py`, you'll see:

1. **Dataset Exploration**:
   ```
   📊 Dataset: BQ_EPA_Air_Data
   📋 Available Tables:
      • daily_88101_2025 (123,456 rows)
      • [other tables...]
   ```

2. **Application Startup**:
   ```
   ✅ Connected to EPA BigQuery Dataset
   🌍 Community Health & Wellness Platform
   🚀 Open your browser: http://localhost:8080
   ```

3. **Real EPA Data**: The app will query actual EPA air quality measurements!

---

## 🎯 Quick Test

Once the app is running, test these URLs:

1. **Dataset Info**: http://localhost:8080/api/dataset-info
2. **Air Quality for California**: http://localhost:8080/api/air-quality?state=California&days=7
3. **Main Dashboard**: http://localhost:8080

---

## ⚠️ Troubleshooting

### Issue: "Could not find credentials"

**Solution**: Make sure your `service-account-key.json` file is in the correct location:
```powershell
# Check if file exists
Test-Path .\service-account-key.json
```

### Issue: "Permission denied"

**Solution**: Your service account needs these roles:
- `BigQuery Data Viewer`
- `BigQuery Job User`

Go to: https://console.cloud.google.com/iam-admin/iam?project=qwiklabs-gcp-00-86088b6278cb

### Issue: App shows "Demo Mode"

**Solution**: Check the console output for error messages. Common issues:
- Missing or invalid service account key
- Incorrect project ID or dataset name
- Insufficient permissions

---

## 📝 Next Steps

1. ✅ Get service account key
2. ✅ Update `.env` file
3. ✅ Run `python app_epa.py`
4. ✅ Visit http://localhost:8080
5. 🎉 See real EPA air quality data!

---

## 🔑 Optional: Configure Gemini AI

For the AI Health Advisor feature:

1. Visit: https://makersuite.google.com/app/apikey
2. Create an API key
3. Add to `.env`: `GEMINI_API_KEY=your-key-here`
4. Restart the app

Without this, the app will still work, but AI features will be disabled.

---

**Need Help?** Check the console output for detailed error messages and debugging information!
