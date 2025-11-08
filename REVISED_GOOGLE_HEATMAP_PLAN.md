# 🗺️ REVISED: Google Air Quality Heatmap Integration Plan

**Date**: November 8, 2025  
**Goal**: Replace backend EPA API with Google's official Air Quality heatmap tiles  
**Status**: 📋 **READY FOR IMPLEMENTATION** (with user clarifications)

---

## ✅ **User Clarifications Applied**

### **1. UI Buttons Already Exist** ✅
- **Location**: `templates/index.html` lines 613-614
- **Buttons**: "AQI" and "Intensity" already in place
- **Function**: `toggleHeatmapType('aqi')` / `toggleHeatmapType('intensity')`
- **Action**: Just update the existing function logic, NO new UI needed

### **2. Validate Before Removing APIs** ✅
- **API**: `/api/air-quality-map` in `app_local.py` (line 2500)
- **Used by**: `static/js/air-quality-map.js` (line 410)
- **Also called from**: `static/js/app.js` (4 locations via `loadHeatmapData()`)
- **Decision**: Keep backend endpoint, but make it optional/fallback only

---

## 🔍 **Dependency Analysis**

### **What Uses `/api/air-quality-map`?**

#### **Primary Caller: `air-quality-map.js`**
```javascript
// Line 410 in static/js/air-quality-map.js
let url = '/api/air-quality-map?limit=20';
```

#### **Secondary Callers: `app.js` (via `loadHeatmapData()`)**
```javascript
// Line 345: When location changes
if (typeof loadHeatmapData === 'function') {
    loadHeatmapData(state);
}

// Line 461: After geocode/address lookup
if (typeof loadHeatmapData === 'function') {
    loadHeatmapData(state);
}

// Line 855: When state filter changes
if (typeof loadHeatmapData === 'function') {
    loadHeatmapData(currentState);
}

// Line 894: On page load (default California)
if (typeof loadHeatmapData === 'function') {
    loadHeatmapData('California');
}
```

### **Current `toggleHeatmapType()` Function**

**Location**: `static/js/air-quality-map.js` lines 537-580

**Current Behavior**:
- **AQI mode**: Adjusts tile layer brightness/contrast/saturation
- **Intensity mode**: MAXIMUM brightness/contrast/saturation (5.0)
- **Problem**: Still using the same tile layer, just changing visual properties

**What We Need**:
- **AQI mode**: Load `US_AQI` heatmap tiles (standard EPA colors)
- **Intensity mode**: Load `UAQI_INDIGO_PERSIAN` heatmap tiles (high contrast)

---

## 🎯 **Revised Implementation Strategy**

### **Phase 1: Keep Backend as Fallback** ✅
- ❌ **DO NOT remove** `/api/air-quality-map` endpoint
- ✅ **Keep it** as a fallback for marker overlays
- ✅ Backend provides individual data points for tooltips/info
- ✅ Google tiles provide visual heatmap overlay

**Why?**
- `app.js` calls `loadHeatmapData()` in 4 places for location updates
- Backend provides detailed readings (AQI values, city names)
- Google tiles provide visual overlay only (no data values)
- **Best approach**: Use both (tiles for visual, backend for data markers)

---

### **Phase 2: Map UI Buttons to Google Heatmap Types** 🎨

**Current Function** (lines 537-580):
```javascript
function toggleHeatmapType(type) {
    // Current: Changes brightness/contrast only
    if (type === 'aqi') {
        aqiTileLayer.brightness = 3.0;
    } else if (type === 'intensity') {
        aqiTileLayer.brightness = 5.0;
    }
}
```

**Updated Function**:
```javascript
let currentHeatmapType = 'US_AQI'; // Global variable

function toggleHeatmapType(type) {
    const aqiBtn = document.getElementById('btnAQI');
    const intensityBtn = document.getElementById('btnIntensity');
    
    if (type === 'aqi') {
        // Switch to standard US AQI heatmap
        currentHeatmapType = 'US_AQI';
        switchGoogleHeatmapTiles('US_AQI');
        
        // Update button styles
        aqiBtn.className = 'px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors font-medium text-sm';
        intensityBtn.className = 'px-4 py-2 bg-gray-200 text-navy-700 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm';
    } else if (type === 'intensity') {
        // Switch to high-contrast INDIGO_PERSIAN heatmap
        currentHeatmapType = 'UAQI_INDIGO_PERSIAN';
        switchGoogleHeatmapTiles('UAQI_INDIGO_PERSIAN');
        
        // Update button styles
        aqiBtn.className = 'px-4 py-2 bg-gray-200 text-navy-700 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm';
        intensityBtn.className = 'px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors font-medium text-sm';
    }
}

function switchGoogleHeatmapTiles(mapType) {
    console.log(`[HEATMAP] Switching to Google ${mapType} tiles`);
    
    // Remove old imagery layer
    if (aqiTileLayer) {
        cesiumViewer.imageryLayers.remove(aqiTileLayer);
    }
    
    // Create new provider with selected map type
    const aqiProvider = new Cesium.UrlTemplateImageryProvider({
        url: `https://airquality.googleapis.com/v1/mapTypes/${mapType}/heatmapTiles/{z}/{x}/{y}?key=${GOOGLE_API_KEY}`,
        maximumLevel: 16,
        minimumLevel: 0,
        tilingScheme: new Cesium.WebMercatorTilingScheme(),
        hasAlphaChannel: true,
        credit: new Cesium.Credit('Google Air Quality API', false)
    });
    
    // Add new imagery layer
    aqiTileLayer = cesiumViewer.imageryLayers.addImageryProvider(aqiProvider);
    aqiTileLayer.alpha = 0.8; // 80% opacity for visibility
    aqiTileLayer.show = true;
    
    console.log(`[HEATMAP] ✓ Loaded ${mapType} tiles`);
}
```

**Key Changes:**
1. ✅ Uses existing buttons (no new UI)
2. ✅ Switches between Google heatmap types (not just brightness)
3. ✅ `US_AQI` for standard EPA colors
4. ✅ `UAQI_INDIGO_PERSIAN` for high-contrast colors
5. ✅ Maintains existing button styling logic

---

### **Phase 3: Simplify Backend API (Keep as Fallback)** ✅

#### **Option 1: Keep Endpoint, Add Warning** (RECOMMENDED)
```python
@app.route('/api/air-quality-map', methods=['GET'])
def get_air_quality_map():
    """
    API endpoint for air quality marker overlays.
    Note: Primary visualization now uses Google Air Quality heatmap tiles.
    This endpoint provides supplemental data points for tooltips/info windows.
    """
    try:
        # Reduce default limit to minimize EPA API calls
        limit = min(int(request.args.get('limit', 10)), 20)  # Max 20 instead of 100
        
        # ... rest of existing logic ...
        
        return jsonify({
            'success': True,
            'data': heatmap_data,
            'count': len(heatmap_data),
            'source': 'EPA AirNow API',
            'note': 'Google heatmap tiles provide primary visualization'
        })
    except Exception as e:
        # Return empty data instead of error (frontend can use tiles only)
        return jsonify({
            'success': False,
            'data': [],
            'count': 0,
            'error': str(e)
        })
```

**Benefits:**
- ✅ Keeps existing functionality
- ✅ Reduces EPA API load (limit 20 max)
- ✅ Graceful degradation (returns empty on error)
- ✅ `app.js` calls continue to work
- ✅ No breaking changes

#### **Option 2: Remove Endpoint Entirely** (NOT RECOMMENDED)
- ❌ Would break 4 calls in `app.js`
- ❌ Would require refactoring `loadHeatmapData()` logic
- ❌ Would lose detailed data for tooltips
- ❌ More work, less benefit

**Decision: Use Option 1** ✅

---

## 📝 **Exact Code Changes**

### **File 1: `static/js/air-quality-map.js`**

#### **Change 1: Add Global Variable (after line 91)**
```javascript
// After: const GOOGLE_API_KEY = 'AIzaSyChngX3bEfvIg8V9WW0TFGXkgb0W4o3HGI';

// Track current heatmap type
let currentHeatmapType = 'US_AQI'; // Default to standard US AQI
```

#### **Change 2: Remove 3D Tiles (lines 93-130)**
```javascript
// REMOVE ENTIRE BLOCK:
// Lines 93-130: Google 3D Tileset initialization and readyPromise

// REPLACE WITH:
console.log('[HEATMAP DEBUG] Initializing map for air quality visualization');

// Configure globe for heatmap display
cesiumViewer.scene.globe.show = true;
cesiumViewer.scene.globe.showGroundAtmosphere = true;

// Keep base imagery layer but make it subtle
const baseLayer = cesiumViewer.imageryLayers.get(0);
if (baseLayer) {
    baseLayer.alpha = 0.5; // Semi-transparent for context
}

console.log('[HEATMAP DEBUG] Adding air quality overlay...');

// Add default Google Air Quality Heatmap (US_AQI)
addAirQualityTileOverlay();

// Try to get user's location
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (position) => {
            console.log('[HEATMAP DEBUG] User location found:', position.coords);
            
            // Fly to user location
            cesiumViewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(
                    position.coords.longitude,
                    position.coords.latitude,
                    1000000 // 1000km altitude
                ),
                duration: 2
            });
            
            // Load data for user's area (optional, for markers)
            loadHeatmapData(null);
        },
        (error) => {
            console.log('[HEATMAP DEBUG] Geolocation not available, using default view');
            // Default to US view
            flyToState('California');
        }
    );
} else {
    console.log('[HEATMAP DEBUG] Geolocation not supported');
    flyToState('California');
}

console.log('[HEATMAP DEBUG] Initialization complete!');

// Update status message
document.getElementById('mapStatus').innerHTML = `
    <i class="fas fa-check-circle text-green-600 mr-2"></i>
    Real-time air quality heatmap from Google
`;
```

#### **Change 3: Add New Function (after line 393)**
```javascript
// NEW FUNCTION: Switch between Google heatmap types
function switchGoogleHeatmapTiles(mapType) {
    console.log(`[HEATMAP] Switching to Google ${mapType} tiles`);
    
    // Remove old imagery layer if it exists
    if (aqiTileLayer) {
        cesiumViewer.imageryLayers.remove(aqiTileLayer);
        console.log(`[HEATMAP] Removed old tile layer`);
    }
    
    // Create new provider with selected map type
    const aqiProvider = new Cesium.UrlTemplateImageryProvider({
        url: `https://airquality.googleapis.com/v1/mapTypes/${mapType}/heatmapTiles/{z}/{x}/{y}?key=${GOOGLE_API_KEY}`,
        maximumLevel: 16,
        minimumLevel: 0,
        tilingScheme: new Cesium.WebMercatorTilingScheme(),
        hasAlphaChannel: true,
        credit: new Cesium.Credit('Google Air Quality API', false)
    });
    
    // Add new imagery layer
    aqiTileLayer = cesiumViewer.imageryLayers.addImageryProvider(aqiProvider);
    aqiTileLayer.alpha = 0.8; // 80% opacity for good visibility
    aqiTileLayer.show = true;
    
    console.log(`[HEATMAP] ✓ Loaded ${mapType} tiles (opacity: 0.8)`);
    
    // Update status
    const typeLabel = mapType === 'US_AQI' ? 'Standard AQI' : 'High Contrast';
    document.getElementById('mapStatus').innerHTML = `
        <i class="fas fa-check-circle text-green-600 mr-2"></i>
        Showing ${typeLabel} air quality heatmap
    `;
}
```

#### **Change 4: Update `toggleHeatmapType()` (lines 537-580)**
```javascript
// REPLACE ENTIRE FUNCTION:
function toggleHeatmapType(type) {
    const aqiBtn = document.getElementById('btnAQI');
    const intensityBtn = document.getElementById('btnIntensity');
    
    if (type === 'aqi') {
        // Switch to standard US AQI heatmap (EPA color scale)
        console.log('[HEATMAP] Switching to US_AQI (standard EPA colors)');
        currentHeatmapType = 'US_AQI';
        switchGoogleHeatmapTiles('US_AQI');
        
        // Update button styles (active state)
        aqiBtn.className = 'px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors font-medium text-sm';
        intensityBtn.className = 'px-4 py-2 bg-gray-200 text-navy-700 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm';
        
    } else if (type === 'intensity') {
        // Switch to high-contrast INDIGO_PERSIAN heatmap (maximum visibility)
        console.log('[HEATMAP] Switching to UAQI_INDIGO_PERSIAN (high contrast)');
        currentHeatmapType = 'UAQI_INDIGO_PERSIAN';
        switchGoogleHeatmapTiles('UAQI_INDIGO_PERSIAN');
        
        // Update button styles (active state)
        aqiBtn.className = 'px-4 py-2 bg-gray-200 text-navy-700 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm';
        intensityBtn.className = 'px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors font-medium text-sm';
    }
}
```

#### **Change 5: Update `addAirQualityTileOverlay()` (lines 371-393)**
```javascript
// UPDATE to use currentHeatmapType variable:
function addAirQualityTileOverlay() {
    console.log('[HEATMAP DEBUG] Creating Google Air Quality tile provider...');
    
    // Use the current heatmap type (defaults to US_AQI)
    const aqiProvider = new Cesium.UrlTemplateImageryProvider({
        url: `https://airquality.googleapis.com/v1/mapTypes/${currentHeatmapType}/heatmapTiles/{z}/{x}/{y}?key=${GOOGLE_API_KEY}`,
        maximumLevel: 16,
        minimumLevel: 0,
        tilingScheme: new Cesium.WebMercatorTilingScheme(),
        hasAlphaChannel: true,
        credit: new Cesium.Credit('Google Air Quality API', false)
    });
    
    console.log('[HEATMAP DEBUG] Adding air quality imagery layer...');
    
    // Add the imagery layer
    aqiTileLayer = cesiumViewer.imageryLayers.addImageryProvider(aqiProvider);
    aqiTileLayer.alpha = 0.8; // 80% opacity
    aqiTileLayer.show = true;
    
    console.log('[HEATMAP DEBUG] ✓ Air quality layer added and visible');
}
```

---

### **File 2: `app_local.py`**

#### **Change 1: Reduce Default Limit (line 2508)**
```python
# BEFORE:
limit = int(request.args.get('limit', 100))

# AFTER:
# Reduce default limit to minimize EPA API calls (tiles provide main visualization)
limit = min(int(request.args.get('limit', 10)), 20)  # Default 10, max 20
```

#### **Change 2: Update Docstring and Success Response (lines 2502-2503)**
```python
# UPDATE:
@app.route('/api/air-quality-map', methods=['GET'])
def get_air_quality_map():
    """
    API endpoint for supplemental air quality marker overlays.
    
    NOTE: Primary visualization now uses Google Air Quality heatmap tiles directly.
    This endpoint provides data points for optional marker overlays and tooltips.
    
    Reduced limits to minimize EPA API load:
    - Default: 10 locations
    - Maximum: 20 locations
    """
```

#### **Change 3: Update Success Response (add note field)**
```python
# Around line 2620, UPDATE return statement:
return jsonify({
    'success': True,
    'data': heatmap_data,
    'count': len(heatmap_data),
    'source': 'EPA AirNow API',
    'cached': False,
    'note': 'Google Air Quality heatmap tiles provide primary visualization'
})
```

---

## 🧪 **Testing Plan**

### **Test 1: Default Load (US_AQI)**
1. Load page `http://localhost:5000`
2. Scroll to "Air Quality Heatmap" section
3. **Expected**: 
   - ✅ Map loads with satellite imagery
   - ✅ Colored heatmap overlay visible (green/yellow/orange/red)
   - ✅ "AQI" button is active (navy blue)
   - ✅ Status shows "Real-time air quality heatmap from Google"
4. **Console Check**:
   - `[HEATMAP DEBUG] Initialization complete!`
   - `[HEATMAP] ✓ Loaded US_AQI tiles`
5. **Network Tab**:
   - Requests to `airquality.googleapis.com/v1/mapTypes/US_AQI/heatmapTiles/...`
   - Status 200 OK

### **Test 2: Toggle to Intensity (UAQI_INDIGO_PERSIAN)**
1. Click "Intensity" button
2. **Expected**:
   - ✅ Heatmap changes to high-contrast colors (indigo/purple/persian)
   - ✅ "Intensity" button becomes active (navy blue)
   - ✅ "AQI" button becomes inactive (gray)
   - ✅ Status updates to "Showing High Contrast air quality heatmap"
3. **Console Check**:
   - `[HEATMAP] Switching to UAQI_INDIGO_PERSIAN (high contrast)`
   - `[HEATMAP] Removed old tile layer`
   - `[HEATMAP] ✓ Loaded UAQI_INDIGO_PERSIAN tiles`
4. **Network Tab**:
   - New requests to `.../mapTypes/UAQI_INDIGO_PERSIAN/heatmapTiles/...`

### **Test 3: Toggle Back to AQI (US_AQI)**
1. Click "AQI" button
2. **Expected**:
   - ✅ Heatmap returns to standard EPA colors
   - ✅ Smooth transition (no flicker)
   - ✅ Button states update correctly
3. **Console Check**:
   - `[HEATMAP] Switching to US_AQI (standard EPA colors)`

### **Test 4: Pan/Zoom Map**
1. Pan to different location (e.g., New York)
2. Zoom in (street level)
3. **Expected**:
   - ✅ New tiles load for visible area
   - ✅ Heatmap stays visible at all zoom levels (0-16)
   - ✅ Selected heatmap type persists during navigation
4. **Network Tab**:
   - New tile requests for new coordinates

### **Test 5: Backend API Still Works**
1. Open browser console
2. Run: `loadHeatmapData('California')`
3. **Expected**:
   - ✅ Backend API call to `/api/air-quality-map?limit=10&state=California`
   - ✅ Returns up to 10 data points
   - ✅ Optional markers appear on map (if marker code is kept)
   - ✅ No errors if backend returns empty data

### **Test 6: State Filter in `app.js`**
1. Change location filter (if UI has state selector)
2. **Expected**:
   - ✅ `loadHeatmapData(state)` is called from `app.js`
   - ✅ Backend API is queried for that state
   - ✅ Google heatmap tiles remain visible (not affected)

---

## ✅ **Success Criteria**

### **Visual**:
- ✅ Heatmap overlay is clearly visible over satellite imagery
- ✅ "AQI" button shows standard EPA colors (green/yellow/orange/red)
- ✅ "Intensity" button shows high-contrast colors (indigo/purple/persian)
- ✅ Smooth transitions when toggling between modes
- ✅ No black/gray areas (unless no data for that region)

### **Functional**:
- ✅ Buttons toggle correctly (active state styling)
- ✅ Tiles load for all zoom levels (0-16)
- ✅ Pan/zoom triggers new tile requests
- ✅ Backend API `/api/air-quality-map` still works (reduced limit)
- ✅ `app.js` calls to `loadHeatmapData()` don't break

### **Performance**:
- ✅ Tiles load quickly from Google CDN
- ✅ No backend processing delay
- ✅ Reduced EPA API calls (max 20 instead of 100)
- ✅ Browser caches tiles (fewer re-requests)

### **Console**:
- ✅ No JavaScript errors
- ✅ Clear logging for heatmap type switches
- ✅ Backend API gracefully handles errors (returns empty data)

---

## 🚀 **Implementation Steps**

### **Step 1: Backup** ✅
```bash
git add static/js/air-quality-map.js app_local.py
git commit -m "BACKUP: Before Google Air Quality heatmap integration"
```

### **Step 2: Update `air-quality-map.js`** 🔧
- Add `currentHeatmapType` global variable
- Remove 3D tiles initialization
- Add `switchGoogleHeatmapTiles()` function
- Update `toggleHeatmapType()` function
- Update `addAirQualityTileOverlay()` function

### **Step 3: Update `app_local.py`** 🔧
- Reduce default/max limit to 10/20
- Update docstring
- Add note field to response

### **Step 4: Test All Features** 🧪
- Run all 6 tests from Testing Plan
- Verify visual, functional, performance criteria
- Check console for errors

### **Step 5: Commit** 🚀
```bash
git add static/js/air-quality-map.js app_local.py
git commit -m "FEATURE: Google Air Quality heatmap with AQI/Intensity toggle

- AQI button: Standard US_AQI color scale
- Intensity button: High-contrast UAQI_INDIGO_PERSIAN
- Removed 3D tiles for better heatmap visibility
- Backend API kept as fallback for data markers (reduced limits)
- Complete coverage with real-time Google data"
```

---

## 🎯 **Final Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                          │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ AQI Button   │  │ Intensity Btn│                        │
│  │ (US_AQI)     │  │ (INDIGO)     │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
│         │                  │                                 │
│         └──────────┬───────┘                                │
│                    │                                         │
│         toggleHeatmapType(type)                             │
│                    │                                         │
│         ┌──────────┴──────────┐                            │
│         │                     │                             │
│         ▼                     ▼                             │
│  switchGoogleHeatmapTiles('US_AQI')                        │
│  switchGoogleHeatmapTiles('UAQI_INDIGO_PERSIAN')          │
│                    │                                         │
│                    ▼                                         │
│  ┌─────────────────────────────────────────────┐           │
│  │   CesiumJS Viewer                           │           │
│  │   ┌─────────────────────────────────────┐   │           │
│  │   │ Base Layer (satellite imagery)      │   │ (bottom)  │
│  │   └─────────────────────────────────────┘   │           │
│  │   ┌─────────────────────────────────────┐   │           │
│  │   │ Google Air Quality Heatmap Tiles    │   │ (overlay) │
│  │   │ (US_AQI or UAQI_INDIGO_PERSIAN)     │   │           │
│  │   └─────────────────────────────────────┘   │           │
│  │   ┌─────────────────────────────────────┐   │           │
│  │   │ Optional: Data Markers (from backend)│   │ (top)     │
│  │   └─────────────────────────────────────┘   │           │
│  └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
                       ▲                    ▲
                       │                    │
        Google Air Quality API    Backend API (fallback)
        (real-time heatmap tiles)  (data points/markers)
              │                            │
              │                            │
              ▼                            ▼
     airquality.googleapis.com    /api/air-quality-map
     (complete coverage)           (10-20 sample points)
```

---

## 📊 **Comparison: Before vs After**

| Aspect | **Before (Current)** | **After (Google Heatmap)** |
|--------|---------------------|---------------------------|
| **Data Source** | Backend EPA API | Google Air Quality API |
| **Coverage** | 10-20 sampled cities | Complete area coverage |
| **Visualization** | Markers only | Continuous heatmap overlay |
| **EPA API Load** | 10-100 calls per request | 10-20 calls (optional markers) |
| **Performance** | Backend processing delay | Direct CDN tiles (fast) |
| **Real-time** | Depends on cache | Always current |
| **Fallback** | Dummy data | Empty data (tiles still work) |
| **AQI Button** | Brightness adjustment | Standard US_AQI tiles |
| **Intensity Button** | Max brightness | High-contrast INDIGO tiles |
| **Backend Dependency** | Critical | Optional (markers only) |
| **Rate Limiting Risk** | High | Low (tiles cached) |

---

## 🎉 **Expected Outcome**

**Users will see:**
1. ✅ **Full air quality heatmap** covering entire visible area (not just sampled points)
2. ✅ **Real-time data** from Google (updated continuously)
3. ✅ **Two distinct visualization modes**:
   - "AQI": Standard EPA color scale (familiar to users)
   - "Intensity": High-contrast colors (better visibility)
4. ✅ **Smooth tile loading** as they pan/zoom (cached by browser)
5. ✅ **No "Loading..." or "No data" errors** (tiles always available)
6. ✅ **Optional data markers** from backend (if available)
7. ✅ **Professional, polished visualization** matching Google Maps quality

**This is a significant upgrade!** 🚀

---

## ✅ **READY TO IMPLEMENT**

All user concerns addressed:
- ✅ Using existing UI buttons (no new UI)
- ✅ Validated backend API usage (keeping as fallback)
- ✅ Not removing any APIs needed by other parts

**Proceed with implementation?** 🎯

