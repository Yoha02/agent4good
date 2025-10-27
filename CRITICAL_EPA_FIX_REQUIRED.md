# 🚨 CRITICAL: EPA Rate Limit Issue - Root Cause Found

## Problem Summary
**EPA API still getting rate limited (Status 429) despite caching!**

## Root Cause Identified ✅

### The Culprit: Air Quality Heatmap
The `/api/air-quality-map` endpoint is being called and it:
1. Loads data for 100+ locations (default limit: 100)
2. For EACH location, makes an EPA API call
3. This happens EVERY time the map loads
4. **Result**: 100+ EPA API calls in rapid succession

### Evidence from Logs:
```
[HEATMAP API] Request - State: None, Limit: 100
[INFO] Found 1240 cities in CA
[INFO] Found 1611 cities in NY
[INFO] Found 1471 cities in TX
...
EPA API Error: Status 429 (Rate Limited)
```

## Why Caching Didn't Help
- **Backend caching works** for same requests
- **BUT**: Map loads 100 DIFFERENT ZIP codes
- Each ZIP code = unique request = cache miss
- 100 unique requests = 100 EPA API calls = rate limit

## Solutions (In Order of Priority)

### Solution 1: DISABLE Auto-Load Map (IMMEDIATE)
**Impact**: Eliminates 100+ EPA calls on page load
**Downside**: Map won't show data until user clicks "Load Map"

```javascript
// In air-quality-map.js
// Comment out auto-initialization
// loadHeatmapData(null);  // DISABLED

// Add manual trigger
document.getElementById('loadMapBtn').addEventListener('click', () => {
    loadHeatmapData(null);
});
```

### Solution 2: DRASTICALLY Reduce Map Limit (QUICK FIX)
**Impact**: Reduces from 100 to 10-20 locations
**Downside**: Less comprehensive map

```javascript
// Change from:
limit = int(request.args.get('limit', 100))
// To:
limit = int(request.args.get('limit', 10))  #  Only 10 locations
```

### Solution 3: Cache at EPA Service Level (MEDIUM TERM)
Cache EPA API responses in the `epa_service.py` file itself.

### Solution 4: Use Pre-Aggregated Data (LONG TERM)
- Store air quality data in BigQuery
- Update every 30 minutes via cron job
- Serve from BigQuery instead of EPA API

## Recommended Action Plan

### IMMEDIATE (Do Now):
1. **Reduce map limit to 10** locations
2. **Disable auto-load** for map
3. **Add manual "Load Map" button**

###  Code Changes Needed:

#### File 1: `app_local.py`
```python
# Line ~2507
limit = int(request.args.get('limit', 10))  # Changed from 100 to 10
```

#### File 2: `static/js/air-quality-map.js`
```javascript
// Comment out auto-load calls
// loadHeatmapData(null);  // DISABLED - user must click button
```

#### File 3: Add button to `templates/index.html`
```html
<button id="loadMapBtn" class="btn btn-primary">
    <i class="fas fa-map"></i> Load Air Quality Map
</button>
```

## Expected Impact

### Before Fix:
- Page load: **100+ EPA API calls**
- Result: **Rate limited in < 1 minute**

### After Fix (Limit=10, Manual Load):
- Page load: **~10 EPA API calls** (first time)
- Manual load: **0 calls** (cached) or **~10 calls** (new location)
- Result: **90% reduction, no more rate limits!**

---

**Priority**: 🔴 **CRITICAL - IMMEDIATE ACTION REQUIRED**
**Estimated Time**: 10 minutes
**Impact**: Solves 90% of EPA rate limit issues

