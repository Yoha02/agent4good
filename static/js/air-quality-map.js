// Air Quality Map with Google Photorealistic 3D Tiles using CesiumJS
// WITH Google Air Quality Heatmap Tile Overlay
let cesiumViewer;
let heatmapData = [];
let heatmapEntities = [];
let currentMapState = null;
let use3DMode = false; // Toggle between 2D and 3D
let aqiTileLayer = null; // Air Quality tile overlay

const GOOGLE_API_KEY = 'AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk';

// State center coordinates for better map positioning
const stateCenters = {
    'Alabama': { lat: 32.806671, lng: -86.791130, height: 500000 },
    'Alaska': { lat: 61.370716, lng: -152.404419, height: 2000000 },
    'Arizona': { lat: 33.729759, lng: -111.431221, height: 600000 },
    'Arkansas': { lat: 34.969704, lng: -92.373123, height: 500000 },
    'California': { lat: 36.116203, lng: -119.681564, height: 800000 },
    'Colorado': { lat: 39.059811, lng: -105.311104, height: 600000 },
    'Connecticut': { lat: 41.597782, lng: -72.755371, height: 200000 },
    'Delaware': { lat: 39.318523, lng: -75.507141, height: 150000 },
    'Florida': { lat: 27.766279, lng: -81.686783, height: 700000 },
    'Georgia': { lat: 33.040619, lng: -83.643074, height: 500000 },
    'Hawaii': { lat: 21.094318, lng: -157.498337, height: 400000 },
    'Idaho': { lat: 44.240459, lng: -114.478828, height: 600000 },
    'Illinois': { lat: 40.349457, lng: -88.986137, height: 600000 },
    'Indiana': { lat: 39.849426, lng: -86.258278, height: 400000 },
    'Iowa': { lat: 42.011539, lng: -93.210526, height: 500000 },
    'Kansas': { lat: 38.526600, lng: -96.726486, height: 500000 },
    'Kentucky': { lat: 37.668140, lng: -84.670067, height: 400000 },
    'Louisiana': { lat: 31.169546, lng: -91.867805, height: 500000 },
    'Maine': { lat: 44.693947, lng: -69.381927, height: 400000 },
    'Maryland': { lat: 39.063946, lng: -76.802101, height: 200000 },
    'Massachusetts': { lat: 42.230171, lng: -71.530106, height: 200000 },
    'Michigan': { lat: 43.326618, lng: -84.536095, height: 600000 },
    'Minnesota': { lat: 45.694454, lng: -93.900192, height: 600000 },
    'Mississippi': { lat: 32.741646, lng: -89.678696, height: 500000 },
    'Missouri': { lat: 38.456085, lng: -92.288368, height: 500000 },
    'Montana': { lat: 46.921925, lng: -110.454353, height: 700000 },
    'Nebraska': { lat: 41.125370, lng: -98.268082, height: 500000 },
    'Nevada': { lat: 38.313515, lng: -117.055374, height: 600000 },
    'New Hampshire': { lat: 43.452492, lng: -71.563896, height: 200000 },
    'New Jersey': { lat: 40.298904, lng: -74.521011, height: 200000 },
    'New Mexico': { lat: 34.840515, lng: -106.248482, height: 600000 },
    'New York': { lat: 42.165726, lng: -74.948051, height: 500000 },
    'North Carolina': { lat: 35.630066, lng: -79.806419, height: 500000 },
    'North Dakota': { lat: 47.528912, lng: -99.784012, height: 500000 },
    'Ohio': { lat: 40.388783, lng: -82.764915, height: 400000 },
    'Oklahoma': { lat: 35.565342, lng: -96.928917, height: 500000 },
    'Oregon': { lat: 44.572021, lng: -122.070938, height: 600000 },
    'Pennsylvania': { lat: 40.590752, lng: -77.209755, height: 500000 },
    'Rhode Island': { lat: 41.680893, lng: -71.511780, height: 100000 },
    'South Carolina': { lat: 33.856892, lng: -80.945007, height: 400000 },
    'South Dakota': { lat: 44.299782, lng: -99.438828, height: 500000 },
    'Tennessee': { lat: 35.747845, lng: -86.692345, height: 400000 },
    'Texas': { lat: 31.054487, lng: -97.563461, height: 900000 },
    'Utah': { lat: 40.150032, lng: -111.862434, height: 600000 },
    'Vermont': { lat: 44.045876, lng: -72.710686, height: 200000 },
    'Virginia': { lat: 37.769337, lng: -78.169968, height: 400000 },
    'Washington': { lat: 47.400902, lng: -121.490494, height: 500000 },
    'West Virginia': { lat: 38.491226, lng: -80.954453, height: 400000 },
    'Wisconsin': { lat: 44.268543, lng: -89.616508, height: 500000 },
    'Wyoming': { lat: 42.755966, lng: -107.302490, height: 600000 }
};

// Initialize the map
function initAirQualityMap() {
    console.log('[HEATMAP DEBUG] Starting initAirQualityMap...');
    try {
        console.log('[HEATMAP DEBUG] Creating Cesium Viewer...');
        // Initialize CesiumJS viewer
        Cesium.Ion.defaultAccessToken = 'YOUR_CESIUM_TOKEN'; // Not needed for Google tiles
        
        cesiumViewer = new Cesium.Viewer('airQualityMap', {
            imageryProvider: false,
            baseLayerPicker: false,
            geocoder: false,
            homeButton: true,
            sceneModePicker: true, // Allow switching between 2D/3D
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: true,
            vrButton: false,
            requestRenderMode: true,
            maximumRenderTimeChange: Infinity
        });
        
        console.log('[HEATMAP DEBUG] Cesium Viewer created successfully');
        console.log('[HEATMAP DEBUG] Adding Google 3D Tiles...');
        
        // Add Google's Photorealistic 3D Tiles
        const tileset = cesiumViewer.scene.primitives.add(new Cesium.Cesium3DTileset({
            url: "https://tile.googleapis.com/v1/3dtiles/root.json?key=AIzaSyALQGawG7iVNjJhG8v5w3Z_eyt5oRdMCvk",
            showCreditsOnScreen: true
        }));
        
        console.log('[HEATMAP DEBUG] 3D Tileset added');
        
        // Wait for tileset to be ready before positioning camera
        tileset.readyPromise.then(() => {
            console.log('[HEATMAP DEBUG] Tileset loaded and ready');
            
            // Hide the default globe to show only 3D tiles
            cesiumViewer.scene.globe.show = false;
            console.log('[HEATMAP DEBUG] Globe hidden');
            
            // Add Google Air Quality Heatmap Tiles as overlay
            console.log('[HEATMAP DEBUG] Adding air quality overlay...');
            addAirQualityTileOverlay();
            
            console.log('[HEATMAP DEBUG] Getting user location...');
            // Try to get user's current location
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lng = position.coords.longitude;
                        console.log('[HEATMAP DEBUG] Got user location:', lat, lng);
                        
                        // Fly to user's location - very close to ground
                        cesiumViewer.camera.flyTo({
                            destination: Cesium.Cartesian3.fromDegrees(lng, lat, 300), // 300m height - very close
                            orientation: {
                                heading: Cesium.Math.toRadians(0),
                                pitch: Cesium.Math.toRadians(-30), // 30 degree angle
                                roll: 0.0
                            },
                            duration: 3
                        });
                        
                        // Load data for this location (will use state from global vars if available)
                        loadHeatmapData(null);
                    },
                    (error) => {
                        console.warn('[HEATMAP DEBUG] Geolocation error:', error.message);
                        // Fall back to using global currentZip, currentCity, currentState if available
                        if (typeof currentZip !== 'undefined' && currentZip) {
                            console.log('[HEATMAP DEBUG] Using global location:', currentCity, currentState, currentZip);
                            // Geocode the ZIP to get coordinates
                            geocodeZipCode(currentZip);
                        } else {
                            // Default to Golden Gate Bridge
                            console.log('[HEATMAP DEBUG] Using default location: Golden Gate Bridge');
                            cesiumViewer.camera.flyTo({
                                destination: Cesium.Cartesian3.fromDegrees(-122.4783, 37.8199, 300), // 300m height
                                orientation: {
                                    heading: Cesium.Math.toRadians(0),
                                    pitch: Cesium.Math.toRadians(-30),
                                    roll: 0.0
                                },
                                duration: 3
                            });
                            loadHeatmapData(null);
                        }
                    }
                );
            } else {
                console.warn('[HEATMAP DEBUG] Geolocation not supported');
                // Fall back to Golden Gate Bridge
                cesiumViewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(-122.4783, 37.8199, 300), // 300m height
                    orientation: {
                        heading: Cesium.Math.toRadians(0),
                        pitch: Cesium.Math.toRadians(-30),
                        roll: 0.0
                    },
                    duration: 3
                });
                loadHeatmapData(null);
            }
            
            console.log('[HEATMAP DEBUG] Initialization complete!');
        }).catch((error) => {
            console.error('[HEATMAP DEBUG] Tileset failed to load:', error);
        });
        
    } catch (error) {
        console.error('[HEATMAP] Error initializing Cesium:', error);
        console.error('[HEATMAP DEBUG] Error stack:', error.stack);
        document.getElementById('mapStatus').innerHTML = `
            <i class="fas fa-exclamation-triangle text-red-600 mr-2"></i>
            Error loading 3D map. Falling back to 2D.
        `;
        // Fall back to 2D if 3D fails
        initFallback2DMap();
    }
}

// Fallback to Google Maps if CesiumJS fails
function initFallback2DMap() {
    const mapDiv = document.getElementById('airQualityMap');
    mapDiv.innerHTML = '<div id="fallbackMap" style="width:100%; height:100%;"></div>';
    
    const fallbackMap = new google.maps.Map(document.getElementById('fallbackMap'), {
        center: { lat: 37.8199, lng: -122.4783 }, // Golden Gate Bridge
        zoom: 15, // Very close zoom
        mapTypeId: 'roadmap',
        mapTypeControl: true,
        styles: [
            { elementType: 'geometry', stylers: [{ lightness: 20 }] },
            { featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] },
            { featureType: 'transit', stylers: [{ visibility: 'off' }] }
        ]
    });
    
    // Create heatmap layer
    const heatmapLayer = new google.maps.visualization.HeatmapLayer({
        data: [],
        map: fallbackMap,
        radius: 50,
        opacity: 0.85
    });
    
    // Store for updates
    window.fallbackMap = fallbackMap;
    window.fallbackHeatmap = heatmapLayer;
}

// Helper function to geocode ZIP code to coordinates
function geocodeZipCode(zipCode) {
    console.log('[HEATMAP DEBUG] Geocoding ZIP:', zipCode);
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: zipCode }, (results, status) => {
        if (status === 'OK' && results[0]) {
            const location = results[0].geometry.location;
            const lat = location.lat();
            const lng = location.lng();
            console.log('[HEATMAP DEBUG] ZIP geocoded to:', lat, lng);
            
            // Fly to this location - very close to ground
            cesiumViewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(lng, lat, 300), // 300m height
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-30), // 30 degree angle
                    roll: 0.0
                },
                duration: 3
            });
            
            loadHeatmapData(null);
        } else {
            console.error('[HEATMAP DEBUG] Geocoding failed:', status);
            // Fall back to Golden Gate Bridge
            cesiumViewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(-122.4783, 37.8199, 300),
                orientation: {
                    heading: Cesium.Math.toRadians(0),
                    pitch: Cesium.Math.toRadians(-30),
                    roll: 0.0
                },
                duration: 3
            });
            loadHeatmapData(null);
        }
    });
}

// Fly camera to a specific state
function flyToState(stateName) {
    const stateInfo = stateCenters[stateName];
    if (!stateInfo || !cesiumViewer) {
        console.log('[HEATMAP] Cannot fly to state:', stateName, 'Found:', !!stateInfo, 'Viewer:', !!cesiumViewer);
        if (!stateInfo) {
            console.log('[HEATMAP] Available states:', Object.keys(stateCenters).slice(0, 10).join(', ') + '...');
        }
        return;
    }
    
    console.log('[HEATMAP] Flying camera to:', stateName, stateInfo);
    
    cesiumViewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(
            stateInfo.lng,
            stateInfo.lat,
            stateInfo.height
        ),
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-45), // 45 degree tilt for better view
            roll: 0.0
        },
        duration: 2
    });
}

// Add Google Air Quality Heatmap Tiles overlay
function addAirQualityTileOverlay() {
    if (!cesiumViewer) return;
    
    console.log('[HEATMAP] Adding Google Air Quality tile overlay...');
    
    try {
        // Create imagery provider for Google Air Quality tiles
        // URL pattern: https://airquality.googleapis.com/v1/mapTypes/US_AQI/heatmapTiles/{z}/{x}/{y}?key=API_KEY
        const aqiProvider = new Cesium.UrlTemplateImageryProvider({
            url: `https://airquality.googleapis.com/v1/mapTypes/US_AQI/heatmapTiles/{z}/{x}/{y}?key=${GOOGLE_API_KEY}`,
            maximumLevel: 16,
            minimumLevel: 0,
            credit: 'Air Quality data from Google',
            tilingScheme: new Cesium.WebMercatorTilingScheme(),
            hasAlphaChannel: true
        });
        
        // Add as an imagery layer with transparency
        aqiTileLayer = cesiumViewer.imageryLayers.addImageryProvider(aqiProvider);
        
        // Make the layer EXTREMELY visible - maximum settings
        aqiTileLayer.alpha = 1.0; // 100% opaque
        aqiTileLayer.brightness = 3.0; // VERY bright
        aqiTileLayer.contrast = 3.0; // VERY high contrast
        aqiTileLayer.saturation = 3.0; // VERY vivid colors
        aqiTileLayer.gamma = 2.0; // Much brighter mid-tones
        aqiTileLayer.hue = 0.0; // No hue shift
        
        console.log('[HEATMAP] Air Quality tile overlay added successfully');
        console.log('[HEATMAP] Tile URL pattern:', `https://airquality.googleapis.com/v1/mapTypes/US_AQI/heatmapTiles/{z}/{x}/{y}?key=${GOOGLE_API_KEY}`);
        
        // Test a specific tile URL for San Francisco area
        const testUrl = `https://airquality.googleapis.com/v1/mapTypes/US_AQI/heatmapTiles/5/5/12?key=${GOOGLE_API_KEY}`;
        console.log('[HEATMAP] Test tile URL:', testUrl);
        console.log('[HEATMAP] Click the URL above to test if tiles are loading');
        
        // Listen for errors
        aqiProvider.errorEvent.addEventListener((error) => {
            console.error('[HEATMAP] Tile loading error:', error);
        });
        
        // Listen for tile load success
        aqiProvider.readyPromise.then(() => {
            console.log('[HEATMAP] ✅ Tile provider is ready!');
        }).catch((error) => {
            console.error('[HEATMAP] ❌ Tile provider failed:', error);
        });
        
    } catch (error) {
        console.error('[HEATMAP] Error adding tile overlay:', error);
        document.getElementById('mapStatus').innerHTML = `
            <i class="fas fa-exclamation-circle text-orange-600 mr-2"></i>
            Air quality overlay unavailable - check console
        `;
    }
}

// Fly camera to specific coordinates (for city/ZIP level zoom)
function flyToCoordinates(lat, lng, height = 50000) {
    if (!cesiumViewer) {
        console.log('[HEATMAP] Cannot fly to coordinates - viewer not ready');
        return;
    }
    
    console.log('[HEATMAP] Flying to coordinates:', lat, lng, 'height:', height);
    
    cesiumViewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lng, lat, height),
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-45),
            roll: 0.0
        },
        duration: 2
    });
}

// Make functions globally accessible
window.flyToCoordinates = flyToCoordinates;

// Load heatmap data from API
async function loadHeatmapData(state = null) {
    try {
        console.log('[HEATMAP] ==> loadHeatmapData called with state:', state);
        
        document.getElementById('mapStatus').innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading air quality readings...';
        
        currentMapState = state;
        
        // Fly to state if specified
        if (state) {
            console.log('[HEATMAP] Flying to state:', state);
            flyToState(state);
        }
        
        // Fetch individual readings to show as markers
        let url = '/api/air-quality-map';
        if (state) {
            url += `?state=${encodeURIComponent(state)}`;
        }
        
        const response = await fetch(url);
        const result = await response.json();
        
        if (result.success && result.data) {
            heatmapData = result.data;
            console.log('[HEATMAP] Received', result.data.length, 'data points');
            updateHeatmap(); // Add markers showing readings
            
            document.getElementById('mapStatus').innerHTML = `
                <i class="fas fa-check-circle text-green-600 mr-2"></i>
                Showing ${result.count} air quality readings
            `;
        } else {
            document.getElementById('mapStatus').innerHTML = `
                <i class="fas fa-check-circle text-green-600 mr-2"></i>
                Showing real-time air quality data from Google
            `;
        }
        
    } catch (error) {
        console.error('[HEATMAP] Error:', error);
        document.getElementById('mapStatus').innerHTML = `
            <i class="fas fa-check-circle text-green-600 mr-2"></i>
            Showing air quality tile overlay
        `;
    }
}

// Update heatmap visualization - add markers with AQI readings
function updateHeatmap() {
    console.log('[HEATMAP] updateHeatmap called with', heatmapData.length, 'data points');
    
    if (!cesiumViewer) {
        console.error('[HEATMAP] No cesiumViewer available');
        return;
    }
    
    // Clear existing entities
    heatmapEntities.forEach(entity => {
        cesiumViewer.entities.remove(entity);
    });
    heatmapEntities = [];
    
    console.log('[HEATMAP] Cleared old markers, adding new ones...');
    
    // If using fallback 2D map
    if (window.fallbackHeatmap) {
        const heatmapPoints = heatmapData.map(point => ({
            location: new google.maps.LatLng(point.lat, point.lng),
            weight: point.weight
        }));
        window.fallbackHeatmap.setData(heatmapPoints);
        return;
    }
    
    // Add air quality reading markers on CesiumJS map
    if (heatmapData.length > 0) {
        heatmapData.forEach((point, index) => {
            try {
                const color = getAQIColorCesium(point.aqi);
                
                console.log(`[HEATMAP] Adding marker ${index + 1}: ${point.city}, AQI ${point.aqi}`);
                
                // Create a point (circle) at each location
                const entity = cesiumViewer.entities.add({
                    position: Cesium.Cartesian3.fromDegrees(point.lng, point.lat, 1000), // 1km above ground for visibility
                    point: {
                        pixelSize: 25, // Large visible point
                        color: color,
                        outlineColor: Cesium.Color.WHITE,
                        outlineWidth: 3,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY, // Always visible
                        heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
                    },
                    label: {
                        text: point.aqi.toString(),
                        font: 'bold 18px Arial',
                        fillColor: Cesium.Color.WHITE,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 4,
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -30),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY,
                        heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
                    },
                    description: `
                        <div style="padding: 15px; min-width: 250px;">
                            <h3 style="margin: 0 0 10px 0; color: #1a3a52; font-size: 18px;">${point.city}, ${point.state}</h3>
                            <p style="margin: 8px 0;"><strong style="font-size: 14px;">AQI:</strong> <span style="color: ${getAQIColorHex(point.aqi)}; font-weight: bold; font-size: 24px;">${point.aqi}</span></p>
                            <p style="margin: 8px 0; font-size: 14px;"><strong>Category:</strong> ${getAQICategory(point.aqi)}</p>
                            <p style="margin: 8px 0; font-size: 12px; color: #666;">ZIP: ${point.zipcode}</p>
                        </div>
                    `
                });
                
                heatmapEntities.push(entity);
            } catch (error) {
                console.error('[HEATMAP] Error adding marker for', point.city, error);
            }
        });
        
        console.log('[HEATMAP] ✅ Successfully added', heatmapEntities.length, 'reading markers');
    } else {
        console.warn('[HEATMAP] No data points to display');
    }
}

// Toggle heatmap visualization type
function toggleHeatmapType(type) {
    const aqiBtn = document.getElementById('btnAQI');
    const intensityBtn = document.getElementById('btnIntensity');
    
    if (type === 'aqi') {
        // Show AQI-based heatmap - EXTREMELY bright
        if (aqiTileLayer) {
            aqiTileLayer.alpha = 1.0;
            aqiTileLayer.brightness = 3.0;
            aqiTileLayer.contrast = 3.0;
            aqiTileLayer.saturation = 3.0;
            aqiTileLayer.gamma = 2.0;
        }
        if (window.fallbackHeatmap) {
            window.fallbackHeatmap.setOptions({ 
                radius: 50, 
                opacity: 1.0,
                maxIntensity: 200,
                dissipating: true
            });
        }
        aqiBtn.className = 'px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors font-medium text-sm';
        intensityBtn.className = 'px-4 py-2 bg-gray-200 text-navy-700 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm';
    } else if (type === 'intensity') {
        // Show intensity-based heatmap - MAXIMUM visibility (nuclear bright!)
        if (aqiTileLayer) {
            aqiTileLayer.alpha = 1.0;
            aqiTileLayer.brightness = 5.0; // MAXIMUM brightness
            aqiTileLayer.contrast = 5.0; // MAXIMUM contrast
            aqiTileLayer.saturation = 5.0; // MAXIMUM saturation
            aqiTileLayer.gamma = 3.0; // MAXIMUM gamma
        }
        if (window.fallbackHeatmap) {
            window.fallbackHeatmap.setOptions({ 
                radius: 70, 
                opacity: 0.9,
                maxIntensity: 150,
                dissipating: false
            });
        }
        aqiBtn.className = 'px-4 py-2 bg-gray-200 text-navy-700 rounded-lg hover:bg-gray-300 transition-colors font-medium text-sm';
        intensityBtn.className = 'px-4 py-2 bg-navy-600 text-white rounded-lg hover:bg-navy-700 transition-colors font-medium text-sm';
    }
}

// Reset map view
function resetMapView() {
    flyToState('California');
}

// Get AQI color (hex string for HTML)
function getAQIColorHex(aqi) {
    if (aqi <= 50) return '#00E400';      // Green
    if (aqi <= 100) return '#FFFF00';     // Yellow
    if (aqi <= 150) return '#FF7E00';     // Orange
    if (aqi <= 200) return '#FF0000';     // Red
    if (aqi <= 300) return '#8F3F97';     // Purple
    return '#7E0023';                      // Maroon
}

// Get AQI color (Cesium.Color object)
function getAQIColorCesium(aqi) {
    if (aqi <= 50) return Cesium.Color.fromCssColorString('#00E400');
    if (aqi <= 100) return Cesium.Color.fromCssColorString('#FFFF00');
    if (aqi <= 150) return Cesium.Color.fromCssColorString('#FF7E00');
    if (aqi <= 200) return Cesium.Color.fromCssColorString('#FF0000');
    if (aqi <= 300) return Cesium.Color.fromCssColorString('#8F3F97');
    return Cesium.Color.fromCssColorString('#7E0023');
}

// Get AQI category
function getAQICategory(aqi) {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Moderate';
    if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
    if (aqi <= 200) return 'Unhealthy';
    if (aqi <= 300) return 'Very Unhealthy';
    return 'Hazardous';
}

// Listen for state changes from location filter
window.addEventListener('locationChanged', (event) => {
    const state = event.detail.state;
    currentMapState = state;
    loadHeatmapData(state);
});

// Make loadHeatmapData globally accessible for app.js
window.loadHeatmapData = loadHeatmapData;

// Initialize map when libraries are loaded
window.addEventListener('load', () => {
    console.log('[HEATMAP DEBUG] Window loaded');
    console.log('[HEATMAP DEBUG] Cesium available?', typeof Cesium !== 'undefined');
    console.log('[HEATMAP DEBUG] Google Maps available?', typeof google !== 'undefined' && google.maps);
    
    // Wait for CesiumJS to be ready
    if (typeof Cesium !== 'undefined') {
        console.log('[HEATMAP DEBUG] Cesium found, initializing map...');
        initAirQualityMap();
    } else {
        console.warn('[HEATMAP DEBUG] Cesium not found immediately, retrying in 1s...');
        // Retry after a short delay
        setTimeout(() => {
            console.log('[HEATMAP DEBUG] Retry - Cesium available?', typeof Cesium !== 'undefined');
            if (typeof Cesium !== 'undefined') {
                console.log('[HEATMAP DEBUG] Cesium found on retry, initializing map...');
                initAirQualityMap();
            } else {
                console.warn('[HEATMAP] CesiumJS not loaded, attempting fallback to Google Maps');
                if (typeof google !== 'undefined' && google.maps) {
                    console.log('[HEATMAP DEBUG] Using Google Maps fallback');
                    initFallback2DMap();
                } else {
                    console.error('[HEATMAP DEBUG] Neither Cesium nor Google Maps available!');
                }
            }
        }, 1000);
    }
});
