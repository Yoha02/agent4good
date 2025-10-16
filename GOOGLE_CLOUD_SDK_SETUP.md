# Google Cloud SDK Installation Guide for Windows

## 📥 Step 1: Download the Installer

**Two Options:**

### Option A: Direct Download (Recommended)
Download directly: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe

### Option B: From Documentation Page
Visit: https://cloud.google.com/sdk/docs/install-sdk#windows
Click "Download the Google Cloud SDK installer"

---

## 🔧 Step 2: Run the Installer

1. **Run** `GoogleCloudSDKInstaller.exe`
2. Click **"Yes"** if prompted by User Account Control
3. Follow the installation wizard:
   - ✅ Accept the license agreement
   - ✅ Choose installation location (default is fine: `C:\Users\YourName\AppData\Local\Google\Cloud SDK`)
   - ✅ Select components to install (keep defaults)
   - ✅ **IMPORTANT**: Check "Start Cloud SDK Shell" and "Run 'gcloud init'"

---

## ⚙️ Step 3: Initialize Google Cloud SDK

After installation, a command prompt will open automatically.

### Run these commands:

```powershell
# Initialize gcloud
gcloud init

# Follow the prompts:
# 1. Log in with your Google account (browser will open)
# 2. Select your Google Cloud project (or create a new one)
# 3. Set default compute region (optional)
```

---

## 🔐 Step 4: Set Up Application Default Credentials

This is required for our agent to work:

```powershell
# Set up authentication
gcloud auth application-default login
```

This will:
1. Open your browser
2. Ask you to log in with your Google account
3. Grant permissions to Google Cloud SDK
4. Save credentials locally

---

## 🎯 Step 5: Set Your Project ID

```powershell
# Set your project ID (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID

# Or if you're using the qwiklabs project:
gcloud config set project qwiklabs-gcp-00-86088b6278cb
```

---

## ✅ Step 6: Verify Installation

Test that everything is working:

```powershell
# Check gcloud version
gcloud --version

# List your projects
gcloud projects list

# Test BigQuery access
bq ls

# Verify authentication
gcloud auth application-default print-access-token
```

If all commands work without errors, you're ready!

---

## 🚀 Step 7: Set Environment Variable for the Agent

In the same PowerShell window or add to your system:

```powershell
# Set project ID for the agent
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"

# Or for qwiklabs:
$env:GOOGLE_CLOUD_PROJECT = "qwiklabs-gcp-00-86088b6278cb"
```

### To make it permanent:
```powershell
# Add to user environment variables (PowerShell as Admin)
[System.Environment]::SetEnvironmentVariable('GOOGLE_CLOUD_PROJECT', 'your-project-id', 'User')
```

---

## 🧪 Step 8: Test the Full Agent

Now you can run the full agent with real EPA data:

```powershell
# Navigate to your project directory
cd C:\Users\asggm\Agents4Good\agent4good

# Run the interactive demo
python interactive_demo.py
```

---

## 🔧 Troubleshooting

### Issue: "gcloud: command not found"
**Solution**: Restart PowerShell or your terminal to reload the PATH

### Issue: "Could not find default credentials"
**Solution**: Run `gcloud auth application-default login` again

### Issue: "Permission denied" when querying BigQuery
**Solution**: Make sure your Google account has access to the project and BigQuery

### Issue: Installation hangs
**Solution**: 
1. Close the installer
2. Delete: `C:\Users\YourName\AppData\Local\Google\Cloud SDK`
3. Run installer again

---

## 📋 Quick Setup Script

After SDK is installed, run this in PowerShell:

```powershell
# Quick setup script
gcloud auth application-default login
gcloud config set project qwiklabs-gcp-00-86088b6278cb
$env:GOOGLE_CLOUD_PROJECT = "qwiklabs-gcp-00-86088b6278cb"

# Test it works
gcloud projects describe qwiklabs-gcp-00-86088b6278cb

# Run the agent
cd C:\Users\asggm\Agents4Good\agent4good
python interactive_demo.py
```

---

## 🎯 What You'll Be Able to Do After Setup

✅ Query real EPA air quality data from BigQuery  
✅ Access historical data from 2010-2021  
✅ Use all Google Cloud services  
✅ Run the full multi-agent system  
✅ Deploy to Google Cloud Run  

---

## 📦 What Gets Installed

- **gcloud CLI** - Main command-line tool
- **bq** - BigQuery command-line tool  
- **gsutil** - Cloud Storage tool
- **Python SDK components**
- **Auth tools**

Installation size: ~500 MB

---

## 🔗 Useful Links

- **Installation Docs**: https://cloud.google.com/sdk/docs/install-sdk#windows
- **Quickstart Guide**: https://cloud.google.com/sdk/docs/quickstart
- **Authentication Guide**: https://cloud.google.com/docs/authentication/provide-credentials-adc
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs

---

## 💡 Alternative: Use Service Account (For Production)

If you prefer not to use your personal Google account:

1. **Create a Service Account** in Google Cloud Console
2. **Download the JSON key**
3. **Set environment variable**:
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS = "C:\path\to\service-account-key.json"
   ```

---

## 🎓 Learning Resources

After setup, try these:
- `gcloud help` - Get help
- `gcloud init` - Reconfigure settings
- `gcloud auth list` - List authenticated accounts
- `gcloud config list` - Show configuration

---

## ⏱️ Estimated Time

- **Download**: 2-5 minutes
- **Installation**: 5-10 minutes
- **Authentication**: 2-3 minutes
- **Testing**: 2-3 minutes

**Total**: ~15-20 minutes

---

## 🎉 Next Steps After Installation

1. ✅ Verify with: `gcloud --version`
2. ✅ Authenticate: `gcloud auth application-default login`
3. ✅ Set project: `gcloud config set project YOUR_PROJECT_ID`
4. ✅ Test agent: `python interactive_demo.py`
5. ✅ Enjoy real EPA data! 🌟

---

**Ready to install? Follow the steps above and let me know if you need help with any step!**

---

*Last Updated: October 16, 2025*

