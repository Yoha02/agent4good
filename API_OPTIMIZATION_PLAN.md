# API Optimization Plan - EPA Key Exhaustion Fix

## Problem
The landing page makes too many EPA API calls, exhausting the API key quickly.

## Current Issues
1. **Multiple JS files** loading simultaneously (`app.js`, `air-quality-map.js`, `pollutant-charts.js`, `respiratory-chart.js`)
2. **No caching** - Each page load makes fresh API calls
3. **No rate limiting** on the frontend
4. **Pollutant dashboard** not loading data (secondary issue)

## Solutions

### Immediate Fix (High Priority)
1. **Implement API Response Caching** (Backend)
   - Cache EPA API responses for 15-30 minutes
   - Use Python's `cachetools` or Flask-Caching
   - Reduce redundant API calls

2. **Lazy Load Charts** (Frontend)
   - Don't load pollutant charts until user scrolls to section
   - Use Intersection Observer API
   - Saves ~6-8 API calls per page load

3. **Debounce Location Changes**
   - Wait 500ms before making API calls on location change
   - Prevents rapid-fire requests

### Medium Priority
4. **Rate Limiting Frontend**
   - Maximum 1 API call per endpoint per 5 seconds
   - Queue requests and batch them

5. **Use Mock/Sample Data for Demo**
   - Show sample data on initial load
   - Load real data only when user interacts

### Long Term
6. **Switch to EPA API v2** (if available)
   - Higher rate limits
   - Better caching support

7. **Implement Redis Caching**
   - Cache responses across sessions
   - Share cache between users for same location

## Implementation Order

### Step 1: Backend Caching (Highest Impact)
Add to `app_local.py`:
```python
from flask_caching import Cache
from functools import lru_cache
import time

# Configure cache
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 1800})  # 30 min

@cache.cached(timeout=1800, query_string=True)
@app.route('/api/air-quality-detailed')
def get_air_quality_detailed():
    # Existing code...
```

### Step 2: Lazy Load Pollutant Charts
Modify `pollutant-charts.js` to only initialize when section is visible.

### Step 3: Add Request Throttling
Implement a simple throttle mechanism in the frontend.

## Estimated Impact
- **Current**: ~15-20 API calls per page load
- **After Step 1**: ~15-20 API calls first load, then 0 for 30 minutes
- **After Step 2**: ~8-10 API calls per page load
- **After Step 3**: ~8-10 API calls per page load (with better control)

**Total Savings**: ~60-70% reduction in API calls

## Quick Win - Disable Auto-Load
Comment out auto-initialization in JavaScript files until user clicks "View Data" button.

---

**Priority**: CRITICAL
**Estimated Time**: 
- Step 1: 15 minutes
- Step 2: 30 minutes
- Step 3: 20 minutes

**Total**: ~1 hour to implement all fixes

