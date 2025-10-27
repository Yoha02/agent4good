# Data Loading Debug Checklist

## Issue
UI elements (pollutant charts, weather, pollen) are not loading data.

## Possible Causes

### 1. JavaScript Not Initialized
- Dashboard initialization function not being called
- Missing `DOMContentLoaded` event listener
- Script loading order issue

### 2. Missing Location Data
- Dashboard requires location (ZIP code or city/state)
- No default location set
- Location detection not working

### 3. API Endpoints Failing
- Backend returning errors
- CORS issues
- Network errors

### 4. Frontend JavaScript Errors
- Console errors preventing execution
- Missing dependencies
- Syntax errors in updated files

## Debug Steps

### Step 1: Check Browser Console
Open browser DevTools (F12) and check:
- [ ] Any JavaScript errors?
- [ ] Network tab - are API calls being made?
- [ ] If API calls fail, what's the status code?

### Step 2: Check Backend Logs
Look for in terminal:
- [ ] Are API endpoints being hit?
- [ ] Any cache messages (`[CACHE HIT]` or `[CACHE MISS]`)?
- [ ] Any error messages?

### Step 3: Test Individual Endpoint
Try calling API directly:
```bash
curl "http://localhost:8080/api/air-quality-detailed?zipCode=94102&days=7"
```

### Step 4: Check JavaScript Initialization
Look in `pollutant-charts.js`:
- [ ] Is `initializePollutantDashboard()` defined?
- [ ] Is it being called somewhere?
- [ ] Does it need location parameters?

## Quick Fixes to Try

### Fix 1: Ensure Dashboard Initializes on Page Load
Add to `index.html` (or `app.js`):
```javascript
document.addEventListener('DOMContentLoaded', function() {
    console.log('[DEBUG] Page loaded, initializing dashboard');
    
    // Check if pollutant dashboard exists
    const dashboard = document.getElementById('pollutant-dashboard');
    if (dashboard && typeof initializePollutantDashboard === 'function') {
        console.log('[DEBUG] Calling initializePollutantDashboard');
        initializePollutantDashboard();
    }
});
```

### Fix 2: Add Default Location
If dashboard needs location:
```javascript
// Use a default location if none selected
const defaultLocation = {
    zipCode: '94102',  // San Francisco
    city: 'San Francisco',
    state: 'California'
};
initializePollutantDashboard(defaultLocation.zipCode, defaultLocation.city, defaultLocation.state);
```

### Fix 3: Add Error Logging
Add to `pollutant-charts.js` `fetchPollutantData()`:
```javascript
.catch(error => {
    console.error('[POLLUTANT CHARTS] Fetch error:', error);
    console.error('[POLLUTANT CHARTS] URL was:', url);
});
```

## Next Steps

1. **Collect Info**: Check browser console and backend logs
2. **Identify Issue**: Which of the above causes matches?
3. **Apply Fix**: Implement appropriate solution
4. **Test**: Verify data loads

---

**Status**: Investigating
**Priority**: HIGH (blocks UI functionality)

