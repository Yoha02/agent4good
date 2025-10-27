# 🧪 EPA Live Data Cache Test Plan

**Purpose**: Verify that changing locations triggers fresh EPA API calls and returns real live data

---

## 📋 Current Cache Configuration

```python
CACHE_DURATION = 1800  # 30 minutes in seconds
```

### Cached Endpoints:
1. ✅ `/api/air-quality` - Main EPA AirNow data
2. ✅ `/api/air-quality-detailed` - EPA AQS detailed pollutant data
3. ✅ `/api/weather` - Google Weather API
4. ✅ `/api/air-quality-map` - Heatmap data (limit 10 to prevent rate limiting)
5. ✅ `/api/pollen` - Google Pollen API

### How Caching Works:
- **Cache Key**: Built from endpoint + request parameters (state, city, ZIP, days, etc.)
- **Cache Hit**: Returns cached data if less than 30 minutes old
- **Cache Miss**: Calls EPA API and caches the result

---

## 🧪 Test Procedure

### Test 1: Initial Load (Cache Miss)
**Expected**: Fresh EPA API call

1. **Open the app**: `http://localhost:8080`
2. **Default location**: San Francisco, CA (ZIP 94102)
3. **Check Terminal Logs** for:
   ```
   [CACHE MISS] Cached new data for air-quality
   [CACHE MISS] Cached new data for weather
   [CACHE MISS] Cached new data for pollen
   ```
4. **Check Console** for:
   ```
   [APP] Initializing pollutant charts on page load
   Fetching air quality data with params: days=7&zipCode=94102
   API Response: {success: true, data: [...]}
   Data received: X records
   ```

### Test 2: Same Location (Cache Hit)
**Expected**: Cached data returned

1. **Hard refresh** (`Ctrl + F5`)
2. **Check Terminal Logs** for:
   ```
   [CACHE HIT] Returning cached data for air-quality
   [CACHE HIT] Returning cached data for weather
   [CACHE HIT] Returning cached data for pollen
   ```
3. **Result**: No EPA API calls, instant response

### Test 3: Change Location (New Cache Miss)
**Expected**: Fresh EPA API call for new location

1. **Use location search** in the app
2. **Select a different city**, for example:
   - Los Angeles, CA (ZIP 90001)
   - New York, NY (ZIP 10001)
   - Chicago, IL (ZIP 60601)
3. **Check Terminal Logs** for:
   ```
   [CACHE MISS] Cached new data for air-quality
   ```
4. **Check Console** for:
   ```
   Fetching air quality data with params: days=7&zipCode=90001
   API Response: {success: true, data: [...]}
   ```
5. **Verify AQI changes** - Different cities should have different AQI values

### Test 4: Return to First Location (Cache Hit)
**Expected**: Original cached data still valid (if < 30 minutes)

1. **Select San Francisco again**
2. **Check Terminal Logs**:
   - If **< 30 min**: `[CACHE HIT] Returning cached data for air-quality`
   - If **> 30 min**: `[CACHE MISS] Cached new data for air-quality`

---

## 🔍 What to Look For in Terminal

### ✅ **Good - Cache Working Correctly:**
```bash
[CACHE MISS] Cached new data for air-quality
# ... EPA API call happens ...
200 OK from EPA

# 10 seconds later, same location:
[CACHE HIT] Returning cached data for air-quality
# ... no EPA call ...

# Different location:
[CACHE MISS] Cached new data for air-quality
# ... new EPA API call ...
200 OK from EPA
```

### ❌ **Bad - Cache Not Working:**
```bash
# Every request shows CACHE MISS even for same location:
[CACHE MISS] Cached new data for air-quality
[CACHE MISS] Cached new data for air-quality
[CACHE MISS] Cached new data for air-quality
```
This would indicate cache key generation is broken.

---

## 📊 Expected Data Differences by Location

| City | ZIP | Expected AQI Range |
|------|-----|-------------------|
| **San Francisco, CA** | 94102 | 15-50 (typically Good) |
| **Los Angeles, CA** | 90001 | 30-80 (typically Moderate) |
| **Phoenix, AZ** | 85001 | 40-100 (typically Moderate-USG) |
| **New York, NY** | 10001 | 20-60 (typically Good-Moderate) |

If you see the **same AQI value** across different cities, the cache key might not be including the location parameter correctly.

---

## 🎯 Success Criteria

### ✅ **Pass**:
1. First load shows `[CACHE MISS]` in terminal
2. Immediate refresh shows `[CACHE HIT]` in terminal
3. Changing location shows `[CACHE MISS]` with new location parameters
4. Different locations return **different AQI values**
5. Console shows actual EPA API responses with real data arrays
6. Terminal shows **NO** `Status 429 (Rate Limited)` errors

### ❌ **Fail**:
1. Every request shows `[CACHE MISS]` (cache not persisting)
2. All locations return same data (cache key not using location)
3. Terminal shows `429 Rate Limited` errors (cache not preventing API spam)
4. No EPA API calls even on first load (data completely stale)

---

## 🔧 Manual Cache Clear (If Needed)

If you want to force fresh data without waiting 30 minutes:

### Option 1: Restart Flask
```bash
# Stop the server (Ctrl+C)
# Restart:
python app_local.py
```
This clears the `API_CACHE` dictionary (in-memory).

### Option 2: Wait 30 Minutes
Cache automatically expires after 30 minutes.

### Option 3: Modify Code Temporarily
```python
# In app_local.py, change:
CACHE_DURATION = 60  # 1 minute for testing
```

---

## 📝 Test Results Template

Please fill this out and share:

```
=== EPA CACHE TEST RESULTS ===

Test 1 - Initial Load (San Francisco):
Terminal logs: [CACHE HIT/MISS]: __________
AQI Value: __________
Console showed EPA response: [YES/NO]

Test 2 - Immediate Refresh (San Francisco):
Terminal logs: [CACHE HIT/MISS]: __________
AQI Value: __________ (should match Test 1)

Test 3 - Change Location (Los Angeles):
Terminal logs: [CACHE HIT/MISS]: __________
AQI Value: __________ (should be different from Test 1)
Console showed EPA response: [YES/NO]

Test 4 - Return to San Francisco:
Terminal logs: [CACHE HIT/MISS]: __________
AQI Value: __________ (should match Test 1)

Rate Limiting Errors: [YES/NO]
Data appears live/real: [YES/NO]
```

---

## 🎯 What This Proves

If all tests pass:
- ✅ **EPA API is being called** (not mock data)
- ✅ **Cache is working** (preventing rate limits)
- ✅ **Location changes trigger fresh calls** (dynamic data)
- ✅ **Data is real-time** (different cities = different values)

**Ready to test! Change your location and share the terminal logs!** 🚀

