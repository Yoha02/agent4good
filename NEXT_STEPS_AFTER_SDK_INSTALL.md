# 🎯 Next Steps After Google Cloud SDK Installation

## ✅ What Just Happened

The Google Cloud SDK installer has been launched. You should see an installation wizard window.

---

## 📋 Step-by-Step: Complete the Installation

### During Installation Wizard:

1. **Welcome Screen**
   - Click **"Next"**

2. **Choose Installation Location**
   - Keep default: `C:\Users\asggm\AppData\Local\Google\Cloud SDK`
   - Click **"Next"**

3. **Select Components** ⚠️ IMPORTANT
   - ✅ Check **"Install bundled Python"** (if not already installed)
   - ✅ Check **"Google Cloud SDK Core Libraries"** (should be checked)
   - ✅ Check **"gcloud CLI"**
   - ✅ Check **"bq"** (BigQuery command-line tool)
   - ✅ Check **"gsutil"** (Cloud Storage tool)
   - Click **"Install"**

4. **Installation Progress**
   - Wait for installation to complete (2-5 minutes)

5. **Completing Setup** ⭐ VERY IMPORTANT
   - ✅ **CHECK** "Start Google Cloud SDK Shell"
   - ✅ **CHECK** "Run 'gcloud init'"
   - Click **"Finish"**

---

## 🚀 After Installation Completes

### A Cloud SDK Shell window will open automatically. Follow these steps:

### Step 1: Initialize gcloud
```bash
# You'll be prompted with:
# "You must log in to continue. Would you like to log in (Y/n)?"

# Type: Y

# Your browser will open for authentication
# 1. Log in with your Google account
# 2. Click "Allow" to grant permissions
# 3. You'll see "You are now authenticated with gcloud"
```

### Step 2: Select or Create a Project
```bash
# You'll be prompted:
# "Pick cloud project to use:"

# Options:
# - Select existing project from the list (use arrow keys and Enter)
# - Or create a new one
# - Or enter a project ID manually

# For qwiklabs project, enter:
qwiklabs-gcp-00-86088b6278cb
```

### Step 3: Set Default Region (Optional)
```bash
# You'll be prompted:
# "Do you want to configure a default Compute Region and Zone? (Y/n)"

# Type: n (we don't need this for BigQuery)
```

---

## 🔐 Set Up Application Default Credentials

**CRITICAL STEP** - This is what allows the agent to work:

```bash
gcloud auth application-default login
```

This will:
1. Open your browser again
2. Ask you to select your Google account
3. Request additional permissions
4. Save credentials to:
   `C:\Users\asggm\AppData\Roaming\gcloud\application_default_credentials.json`

---

## ⚙️ Set Environment Variable

In the Cloud SDK Shell or PowerShell:

```powershell
# Set for current session
$env:GOOGLE_CLOUD_PROJECT = "qwiklabs-gcp-00-86088b6278cb"

# Or set permanently (run PowerShell as Administrator):
[System.Environment]::SetEnvironmentVariable('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-86088b6278cb', 'User')
```

---

## ✅ Verify Everything Works

Run these commands in Cloud SDK Shell or PowerShell:

### 1. Check gcloud version
```bash
gcloud --version
```
**Expected output:**
```
Google Cloud SDK 4XX.X.X
bq 2.X.XX
...
```

### 2. Verify authentication
```bash
gcloud auth list
```
**Expected output:**
```
              Credentialed Accounts
ACTIVE  ACCOUNT
*       your-email@gmail.com
```

### 3. Check project
```bash
gcloud config get-value project
```
**Expected output:**
```
qwiklabs-gcp-00-86088b6278cb
```

### 4. Test BigQuery access
```bash
bq ls
```
**Expected output:** List of datasets in your project

### 5. Test authentication file
```bash
gcloud auth application-default print-access-token
```
**Expected output:** A long access token (starts with "ya29...")

---

## 🎉 Run the Full Agent!

If all tests pass, you're ready to run the agent with real EPA data:

### Option 1: From Cloud SDK Shell
```bash
cd C:\Users\asggm\Agents4Good\agent4good
python interactive_demo.py
```

### Option 2: From Regular PowerShell (NEW WINDOW)

**Important**: Open a **NEW** PowerShell window so it picks up the updated PATH

```powershell
# Navigate to project
cd C:\Users\asggm\Agents4Good\agent4good

# Set project (if not set permanently)
$env:GOOGLE_CLOUD_PROJECT = "qwiklabs-gcp-00-86088b6278cb"

# Run the agent
python interactive_demo.py
```

---

## 🐛 Troubleshooting

### Problem: "gcloud: command not found" in regular PowerShell

**Solution 1**: Open a **NEW** PowerShell window
- The PATH is only updated when you open a new terminal

**Solution 2**: Manually add to PATH for current session
```powershell
$env:Path += ";C:\Users\asggm\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin"
```

**Solution 3**: Use Cloud SDK Shell
- Search for "Google Cloud SDK Shell" in Start Menu

---

### Problem: "Could not find default credentials"

**Solution**: Run this again:
```bash
gcloud auth application-default login
```

---

### Problem: "Permission denied" when accessing BigQuery

**Solution**: Make sure your Google account has access to the project:
```bash
# Check current project
gcloud config get-value project

# List projects you have access to
gcloud projects list

# Switch to correct project
gcloud config set project YOUR_PROJECT_ID
```

---

### Problem: Agent import fails with authentication error

**Solution**: Make sure both authentications are done:
```bash
# Regular gcloud authentication
gcloud auth login

# Application Default Credentials (THIS IS THE ONE FOR THE AGENT)
gcloud auth application-default login
```

---

## 📊 Quick Reference Commands

```bash
# Authentication
gcloud auth login                          # Login to gcloud
gcloud auth application-default login      # Login for applications (AGENT NEEDS THIS)
gcloud auth list                           # List authenticated accounts

# Project Management
gcloud config set project PROJECT_ID       # Set active project
gcloud config get-value project            # Show active project
gcloud projects list                       # List all your projects

# BigQuery
bq ls                                      # List datasets
bq ls DATASET_ID                           # List tables in dataset
bq show PROJECT:DATASET.TABLE              # Show table info

# General
gcloud --version                           # Show version
gcloud config list                         # Show configuration
gcloud help                                # Get help
```

---

## 🎯 Success Checklist

Before running the agent, verify:

- [ ] ✅ Google Cloud SDK installed
- [ ] ✅ `gcloud --version` works
- [ ] ✅ `gcloud auth list` shows your account
- [ ] ✅ `gcloud auth application-default login` completed
- [ ] ✅ `gcloud config get-value project` shows correct project
- [ ] ✅ `bq ls` works (tests BigQuery access)
- [ ] ✅ `$env:GOOGLE_CLOUD_PROJECT` is set
- [ ] ✅ Opened a NEW PowerShell window (to get updated PATH)

**If all checked**, run: `python interactive_demo.py`

---

## 🆘 Still Having Issues?

### Quick Test Script

Save this as `test_gcloud_setup.ps1` and run it:

```powershell
Write-Host "Testing Google Cloud SDK Setup..." -ForegroundColor Cyan
Write-Host ""

# Test 1: gcloud command
Write-Host "[1/5] Testing gcloud command..." -NoNewline
try {
    $version = gcloud --version 2>&1 | Select-Object -First 1
    Write-Host " OK" -ForegroundColor Green
    Write-Host "      Version: $version" -ForegroundColor Gray
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "      Error: gcloud not found in PATH" -ForegroundColor Red
    Write-Host "      Solution: Open a NEW PowerShell window" -ForegroundColor Yellow
}

# Test 2: Authentication
Write-Host "[2/5] Testing authentication..." -NoNewline
try {
    $account = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
    Write-Host " OK" -ForegroundColor Green
    Write-Host "      Account: $account" -ForegroundColor Gray
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "      Solution: Run 'gcloud auth login'" -ForegroundColor Yellow
}

# Test 3: Project
Write-Host "[3/5] Testing project configuration..." -NoNewline
try {
    $project = gcloud config get-value project 2>&1
    Write-Host " OK" -ForegroundColor Green
    Write-Host "      Project: $project" -ForegroundColor Gray
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "      Solution: Run 'gcloud config set project YOUR_PROJECT_ID'" -ForegroundColor Yellow
}

# Test 4: Application Default Credentials
Write-Host "[4/5] Testing application default credentials..." -NoNewline
try {
    $token = gcloud auth application-default print-access-token 2>&1
    if ($token -like "ya29*") {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        Write-Host "      Solution: Run 'gcloud auth application-default login'" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "      Solution: Run 'gcloud auth application-default login'" -ForegroundColor Yellow
}

# Test 5: Environment Variable
Write-Host "[5/5] Testing GOOGLE_CLOUD_PROJECT env var..." -NoNewline
if ($env:GOOGLE_CLOUD_PROJECT) {
    Write-Host " OK" -ForegroundColor Green
    Write-Host "      Value: $env:GOOGLE_CLOUD_PROJECT" -ForegroundColor Gray
} else {
    Write-Host " NOT SET" -ForegroundColor Yellow
    Write-Host "      Solution: Run '`$env:GOOGLE_CLOUD_PROJECT = `"your-project-id`"'" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup test complete!" -ForegroundColor Cyan
```

---

## 📞 Need More Help?

- **Google Cloud SDK Docs**: https://cloud.google.com/sdk/docs
- **Authentication Guide**: https://cloud.google.com/docs/authentication/provide-credentials-adc
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs

---

**You're almost there! Follow the steps above and you'll be running the full agent in no time! 🚀**

---

*Last Updated: October 16, 2025*

