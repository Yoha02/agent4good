# Twitter Agent Fix - Local Environment

## 🐛 **Problem**
Twitter agent is defaulting to demo/simulation mode and asking about keys.

## 🔍 **Root Cause**
The `.env` file exists but environment variables are NOT being loaded into your PowerShell session when running the app locally.

The Twitter client checks for these variables:
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`
- `TWITTER_BEARER_TOKEN`

When these are missing, it enters **simulation mode** and uses demo data.

## ✅ **Solution 1: Load .env in PowerShell Before Running App**

### **Step 1: Create a PowerShell script to load .env**
Already exists as `load_env.ps1` (if not, create it):

```powershell
# load_env.ps1
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)\s*$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
        Write-Host "Set: $name"
    }
}
Write-Host "`n✅ Environment variables loaded from .env"
```

### **Step 2: Load environment variables before starting the app**

```powershell
# Load .env file
.\load_env.ps1

# Start the app
python app_local.py
```

---

## ✅ **Solution 2: Use python-dotenv (Already Implemented)**

The `app_local.py` already uses `load_dotenv()` at the top:

```python
from dotenv import load_dotenv
load_dotenv()
```

**BUT** this only loads variables for the Python process, not for tools that check environment variables at import time.

### **Fix: Ensure .env is loaded BEFORE importing twitter_client**

Check `app_local.py` line order:

```python
# This should be at the VERY TOP
from dotenv import load_dotenv
load_dotenv()  # MUST be before other imports

# Then import other modules
from multi_tool_agent_bquery_tools.integrations.twitter_client import get_twitter_client
```

---

## ✅ **Solution 3: Quick Test - Restart Your App**

1. **Stop the current Flask app** (Ctrl+C)
2. **Restart it:**
   ```powershell
   python app_local.py
   ```
3. **Check startup logs** for:
   ```
   [TWITTER] SUCCESS: Client initialized successfully!
   [TWITTER] Ready to post tweets with videos
   ```

If you see:
```
[TWITTER] Running in simulation mode (no credentials)
```

Then the .env is not being loaded properly.

---

## 🧪 **Quick Environment Variable Test**

Run this in PowerShell to manually load and test:

```powershell
# Load .env
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)\s*$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}

# Test if loaded
echo $env:TWITTER_API_KEY
# Should output: j1GPTU3weLMzs3PvIvj4nJmel

# Now start app
python app_local.py
```

---

## 📋 **Verification Checklist**

After restart, check for these log lines:

### ✅ **Success Indicators:**
```
[TWITTER] SUCCESS: Client initialized successfully!
[TWITTER] Ready to post tweets with videos
```

### ❌ **Failure Indicators:**
```
[TWITTER] Running in simulation mode (no credentials)
[TWITTER] [SIMULATION] Tweet posted!
[TWITTER] URL: https://twitter.com/CommunityHealthAlerts/status/...
```

---

## 🚀 **Cloud Run (Production) - No Changes Needed**

On Cloud Run, you're setting environment variables directly via `--set-env-vars`, so this issue doesn't affect production.

The variables are already in your deployment command:
```
TWITTER_API_KEY=j1GPTU3weLMzs3PvIvj4nJmel
TWITTER_API_SECRET=FEpSdSCgsTJTSKByeXA9acbKLy9ACpTkoC84sJDbMPEURiRfnv
...etc
```

---

## 🎯 **Quick Fix Summary**

**Best Solution:**
```powershell
# Stop current app (Ctrl+C)

# Load environment
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)\s*$') {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
    }
}

# Restart app
python app_local.py
```

**Expected Result:**
```
[TWITTER] SUCCESS: Client initialized successfully!
[TWITTER] Ready to post tweets with videos
```

Then test video generation + Twitter posting in the officials dashboard!

