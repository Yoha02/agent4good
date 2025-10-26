# Testing Guide for integrate-to-app-local Branch

## 🚀 Quick Start

### 1. Pull the Branch
```bash
git fetch origin
git checkout integrate-to-app-local
```

### 2. Install Dependencies (if needed)
```bash
pip install -r requirements.txt
```

### 3. Start the App
```bash
python app_local.py
```

### 4. Open Browser
Visit: http://localhost:8080

---

## ✅ Test Checklist

### PSA Video Features (NEW)

#### Test 1: Video Generation
1. In chat, type: **"Create a PSA video about air quality in California"**
2. ✅ Expect: Response says "I'll generate a health alert video... 60 seconds"
3. ✅ Expect: After ~60 seconds, video appears with player
4. ✅ Expect: Message asks "Would you like me to post this to Twitter?"

#### Test 2: Twitter Posting
1. After video appears, type: **"Yes, post to Twitter"**
2. ✅ Expect: Loading message (60-90 seconds)
3. ✅ Expect: Success message with tweet URL
4. ✅ Verify: Only ONE tweet created (duplicate fix)
5. ✅ Check: https://twitter.com/AI_mmunity for the posted video

---

### Existing Features (Regression Testing)

#### Test 3: Infectious Diseases (Real Data)
1. Ask: **"What infectious diseases were reported in California in 2024?"**
2. ✅ Expect: Real CDC data (should show ~1908 cases)
3. ✅ Verify: Says "CDC BEAM Dashboard" (NOT "Demo Mode")

#### Test 4: Historical Air Quality (Real Data)
1. Ask: **"What was the air quality in California in 2021?"**
2. ✅ Expect: Real EPA data with PM2.5 concentration
3. ✅ Verify: Says "EPA Historical Air Quality Dataset"

#### Test 5: Current Air Quality
1. Ask: **"What's the current air quality in San Francisco?"**
2. ✅ Expect: Live AQI data from AirNow API

#### Test 6: Location Services
1. Select different state from dropdown
2. Select different city
3. ✅ Verify: Charts update, location badge shows

#### Test 7: Weather & Pollen
1. Set location to a city with ZIP
2. ✅ Verify: Weather card shows temperature, humidity, wind
3. ✅ Verify: Pollen card shows UPI and pollen types

#### Test 8: Community Reporting
1. Click "Report an Issue" (if available in UI)
2. Fill out form with test data
3. Upload an image
4. ✅ Verify: Submission successful
5. ✅ Verify: AI analysis appears

#### Test 9: Officials Dashboard
1. Navigate to `/officials-dashboard`
2. ✅ Verify: Dashboard loads
3. ✅ Verify: Reports table shows data
4. Test filters, export features

---

## 🔍 What to Look For

### ✅ Good Signs
- Video generates in ~60 seconds
- Only ONE tweet is posted
- Real data appears (not "Demo Mode")
- All charts and maps load
- No console errors
- `/health` endpoint shows all services enabled

### ⚠️ Warning Signs
- "Demo Mode" in responses (means BigQuery failed)
- Multiple tweets for same video
- 404 errors for any API endpoints
- Charts not loading
- Video not appearing after 90 seconds

---

## 🐛 Known Issues

### Non-Critical
1. **Air quality city-specific queries** may ask for more details
   - Workaround: Use state-level queries ("California" not "San Francisco")

2. **Video Manager** requires full restart to initialize
   - If PSA feature shows "disabled", restart Flask

### Fixed in This Branch
- ✅ BigQuery queries now work (replaced ADK toolset)
- ✅ Disease data returns real CDC data
- ✅ Air quality returns real EPA data
- ✅ Duplicate Twitter posting prevented

---

## 📊 Expected Terminal Output

### Successful Video Generation
```
[PSA-VIDEO] Video generation requested for: California
[VIDEO_MANAGER] Task created: abc12345
[VEO3] Calling Veo 3.0 Fast API...
[VEO3] Video generation started!
...
[VEO3] Uploaded to GCS: gs://...
[VIDEO_MANAGER] Task abc12345 updated: complete
```

### Successful Twitter Posting
```
[TWITTER] ===== Twitter Posting Request =====
[TWITTER] Video URL: https://storage.googleapis.com/...
[TWITTER] Downloading video...
[TWITTER] SUCCESS: Downloaded...
[TWITTER] Uploading video...
[TWITTER] SUCCESS: Video uploaded! Media ID: ...
[TWITTER] Posting tweet...
[TWITTER] SUCCESS: Tweet posted!
[TWITTER] URL: https://twitter.com/AI_mmunity/status/...
```

### Real BigQuery Data
```
[DISEASE] Executing BigQuery query...
[DISEASE] Query returned 50 rows from CDC BEAM dataset
```
**NOT:**
```
[DISEASE] Falling back to mock data
```

---

## 🎯 Integration Summary

**Main App:** `app_local.py` (unified app)  
**Branch:** `integrate-to-app-local`  
**Total Endpoints:** 32 (28 original + 4 PSA video)  
**Breaking Changes:** 0  
**New Dependencies:** None (all existing)  

**Key Features:**
- ✅ PSA video generation (Veo 3.1)
- ✅ Twitter integration (OAuth)
- ✅ Real CDC disease data (226K rows)
- ✅ Real EPA air quality data
- ✅ All original team features preserved

---

## 📞 Support

**Issues?** Check:
1. `.env` has all required API keys
2. Flask is running (`python app_local.py`)
3. `/health` endpoint shows all services enabled
4. Browser console for JavaScript errors

**Questions?** See:
- `INTEGRATION_COMPLETE.md` - Implementation details
- `PSA_VIDEO_INTEGRATION_PLAN.md` - Original plan
- Terminal logs for debugging

---

**Happy Testing! 🎉**

