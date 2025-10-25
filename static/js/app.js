// Global variables
let aqiChart = null;
let currentState = '';
let currentCity = '';
let currentZip = '';
let currentDays = 7;
let lastVideoData = null; // Store video data for Twitter posting
let locationData = {}; // Cache location data
let autocomplete = null; // Google Places Autocomplete
let geocoder = null; // Google Geocoder

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    initializeGoogleAutocomplete();
});

// Initialize Google Places Autocomplete
function initializeGoogleAutocomplete() {
    // Wait for Google Maps API to load
    if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
        setTimeout(initializeGoogleAutocomplete, 100);
        return;
    }
    
    const input = document.getElementById('locationSearch');
    if (!input) {
        console.error('[Google API] locationSearch input not found');
        return;
    }
    
    // Initialize autocomplete for US cities, regions, and postal codes
    autocomplete = new google.maps.places.Autocomplete(input, {
        types: ['(regions)'],  // Includes cities, states, counties, and postal codes
        componentRestrictions: { country: 'us' }
    });
    
    // CRITICAL: Prevent autocomplete from interfering with typing
    // Limit fields to reduce API costs and prevent focus issues
    autocomplete.setFields(['address_components', 'geometry', 'name', 'formatted_address']);
    
    // Prevent autocomplete from selecting on Enter (let user keep typing)
    google.maps.event.addDomListener(input, 'keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            e.stopPropagation();
            // If dropdown is showing, don't submit
            const pacContainer = document.querySelector('.pac-container');
            if (pacContainer && pacContainer.offsetParent !== null) {
                return false;
            }
        }
    });
    
    // Initialize geocoder for reverse geocoding
    geocoder = new google.maps.Geocoder();
    
    // Listen for place selection
    autocomplete.addListener('place_changed', onPlaceSelected);
    
    console.log('[Google API] Autocomplete initialized with full location support');
}

// Handle place selection from autocomplete
function onPlaceSelected() {
    const place = autocomplete.getPlace();
    
    if (!place.geometry) {
        alert('No details available for: ' + place.name);
        return;
    }
    
    console.log('[Google API] Place selected:', place);
    
    // Extract location details from place
    let city = '';
    let state = '';
    let county = '';
    let zipCode = '';
    
    // Parse address components
    if (place.address_components) {
        for (const component of place.address_components) {
            const types = component.types;
            
            if (types.includes('locality')) {
                city = component.long_name;
            }
            if (types.includes('administrative_area_level_2')) {
                county = component.long_name;
            }
            if (types.includes('administrative_area_level_1')) {
                state = component.long_name;
            }
            if (types.includes('postal_code')) {
                zipCode = component.short_name;
            }
        }
    }
    
    console.log(`[Location Search] City: ${city}, County: ${county}, State: ${state}, ZIP: ${zipCode}`);
    
    // Update current location
    currentState = state;
    currentCity = city;
    currentZip = zipCode;
    
    // Update dropdowns if applicable
    if (state) {
        document.getElementById('stateSelect').value = state || '';
    }
    
    // Load data
    loadAirQualityData();
    loadHealthRecommendations();
    loadWeatherData();  // NEW: Load weather
    loadPollenData();   // NEW: Load pollen
    
    // Show success message
    const locationText = [city, county, state, zipCode].filter(Boolean).join(', ');
    updateAPIStatus('success', 'Location Set', locationText);
}

// Auto-location using browser geolocation
function getAutoLocation() {
    const btn = document.getElementById('autoLocationBtn');
    
    if (!navigator.geolocation) {
        alert('Geolocation is not supported by your browser');
        return;
    }
    
    // Check if Google is available
    if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
        alert('Google Maps is still loading. Please wait a moment and try again.');
        return;
    }
    
    // Update button state
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i><span>Locating...</span>';
    btn.disabled = true;
    
    updateAPIStatus('loading', 'Getting Location', 'Using device location...');
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            console.log(`[Auto-location] Coordinates: ${lat}, ${lon}`);
            
            // Ensure geocoder is initialized
            if (!geocoder) {
                geocoder = new google.maps.Geocoder();
            }
            
            geocoder.geocode(
                { location: { lat, lng: lon } },
                (results, status) => {
                    if (status === 'OK' && results[0]) {
                        console.log('[Geocoding] Result:', results[0]);
                        
                        // Extract city, state, ZIP
                        let city = '';
                        let state = '';
                        let zipCode = '';
                        
                        for (const component of results[0].address_components) {
                            const types = component.types;
                            
                            if (types.includes('locality')) {
                                city = component.long_name;
                            }
                            if (types.includes('administrative_area_level_1')) {
                                state = component.long_name;
                            }
                            if (types.includes('postal_code')) {
                                zipCode = component.short_name;
                            }
                        }
                        
                        console.log(`[Auto-location] Detected: ${city}, ${state} ${zipCode}`);
                        
                        if (zipCode) {
                            currentZip = zipCode;
                            currentState = state;
                            currentCity = city;
                            
                            // Update search box
                            document.getElementById('locationSearch').value = `${city}, ${state} ${zipCode}`;
                            
                            // Update dropdowns
                            const stateSelect = document.getElementById('stateSelect');
                            if (stateSelect) {
                                stateSelect.value = state || '';
                            }
                            
                            // Load ALL data
                            loadAirQualityData();
                            loadHealthRecommendations();
                            loadWeatherData();
                            loadPollenData();
                            
                            updateAPIStatus('success', 'Location Detected', `${city}, ${state} (${zipCode})`);
                        } else {
                            alert('Could not determine ZIP code from your location. Please search manually.');
                            updateAPIStatus('error', 'Location Error', 'ZIP code not found');
                        }
                    } else {
                        console.error('[Geocoding] Failed:', status);
                        alert('Could not determine your location. Error: ' + status);
                        updateAPIStatus('error', 'Geocoding Failed', status);
                    }
                    
                    // Reset button
                    btn.innerHTML = '<i class="fas fa-location-arrow"></i><span>Use My Location</span>';
                    btn.disabled = false;
                }
            );
        },
        (error) => {
            console.error('[Auto-location] Error:', error);
            
            let errorMsg = 'Unknown error';
            switch(error.code) {
                case error.PERMISSION_DENIED:
                    errorMsg = 'Location permission denied. Please enable location access in your browser settings.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMsg = 'Location information unavailable. Please check your device settings.';
                    break;
                case error.TIMEOUT:
                    errorMsg = 'Location request timed out. Please try again.';
                    break;
            }
            
            alert(errorMsg);
            updateAPIStatus('error', 'Location Error', errorMsg);
            
            // Reset button
            btn.innerHTML = '<i class="fas fa-location-arrow"></i><span>Use My Location</span>';
            btn.disabled = false;
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Initialize the application
function initializeApp() {
    // Set default to California
    currentState = 'California';
    updateAPIStatus('loading', 'Initializing...', 'Loading default location data');
    
    // Load cities for California on startup
    onStateChange();
    
    loadAirQualityData();
    loadHealthRecommendations();
}

// Handle state selection change
async function onStateChange() {
    const stateSelect = document.getElementById('stateSelect');
    const citySelect = document.getElementById('citySelect');
    const countyZipSelect = document.getElementById('countyZipSelect');
    
    const selectedState = stateSelect.value;
    
    // Reset dependent dropdowns
    citySelect.innerHTML = '<option value="">Select City</option>';
    countyZipSelect.innerHTML = '<option value="">County/ZIP Code</option>';
    citySelect.disabled = true;
    countyZipSelect.disabled = true;
    
    if (!selectedState) {
        return;
    }
    
    currentState = selectedState;
    currentCity = '';
    currentZip = '';
    
    try {
        // Fetch cities for selected state
        const response = await fetch(`/api/locations?type=cities&state=${encodeURIComponent(selectedState)}`);
        const data = await response.json();
        
        console.log('Cities API response:', data);
        
        if (data.success && data.data) {
            // Store state code
            locationData.stateCode = data.state_code;
            locationData.cities = data.data;
            
            // Populate city dropdown
            data.data.forEach(city => {
                const option = document.createElement('option');
                option.value = city.name;
                option.textContent = `${city.name} (${city.zipcodes_count} ZIPs)`;
                citySelect.appendChild(option);
            });
            
            citySelect.disabled = false;
            
            console.log(`Loaded ${data.data.length} cities for ${selectedState} (${data.state_code})`);
        } else {
            console.error('Failed to load cities:', data);
            alert(`Error loading cities: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error loading cities:', error);
        alert(`Network error loading cities: ${error.message}`);
    }
}

// Handle city selection change
async function onCityChange() {
    const citySelect = document.getElementById('citySelect');
    const countyZipSelect = document.getElementById('countyZipSelect');
    
    const selectedCity = citySelect.value;
    
    // Reset county/ZIP dropdown
    countyZipSelect.innerHTML = '<option value="">County/ZIP Code</option>';
    countyZipSelect.disabled = true;
    
    if (!selectedCity) {
        currentCity = '';
        currentZip = '';
        return;
    }
    
    currentCity = selectedCity;
    currentZip = '';
    
    try {
        // Fetch ZIP codes and counties for selected city
        const response = await fetch(`/api/locations?type=zipcodes&state=${encodeURIComponent(currentState)}&city=${encodeURIComponent(selectedCity)}`);
        const data = await response.json();
        
        console.log('ZIP/County API response:', data);
        
        if (data.success) {
            locationData.zipcodes = data.zipcodes || [];
            locationData.counties = data.counties || [];
            
            console.log(`Received ${locationData.zipcodes.length} ZIPs and ${locationData.counties.length} counties`);
            
            // Add counties as optgroup
            if (locationData.counties.length > 0) {
                const countyGroup = document.createElement('optgroup');
                countyGroup.label = 'Counties';
                locationData.counties.forEach(county => {
                    const option = document.createElement('option');
                    option.value = `county:${county.name}`;
                    option.textContent = `${county.name} County`;
                    countyGroup.appendChild(option);
                });
                countyZipSelect.appendChild(countyGroup);
            }
            
            // Add ZIP codes as optgroup
            if (locationData.zipcodes.length > 0) {
                const zipGroup = document.createElement('optgroup');
                zipGroup.label = 'ZIP Codes';
                locationData.zipcodes.forEach(zip => {
                    const option = document.createElement('option');
                    option.value = `zip:${zip.zipcode}`;
                    option.textContent = `${zip.zipcode} - ${zip.city}`;
                    zipGroup.appendChild(option);
                });
                countyZipSelect.appendChild(zipGroup);
            }
            
            countyZipSelect.disabled = false;
            
            console.log(`Loaded ${locationData.zipcodes.length} ZIP codes and ${locationData.counties.length} counties for ${selectedCity}`);
        } else {
            console.error('Failed to load ZIP/counties:', data);
            alert(`Error loading ZIP codes: ${data.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error loading ZIP codes/counties:', error);
        alert(`Network error loading ZIP codes: ${error.message}`);
    }
}

// Setup event listeners
function setupEventListeners() {
    // Enter key for AI chat
    const questionInput = document.getElementById('questionInput');
    if (questionInput) {
        questionInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                askAI();
            }
        });
    }
}

// Apply location filter
function applyLocationFilter() {
    const stateSelect = document.getElementById('stateSelect');
    const citySelect = document.getElementById('citySelect');
    const countyZipSelect = document.getElementById('countyZipSelect');
    
    if (!stateSelect.value) {
        alert('Please select a state');
        return;
    }
    
    currentState = stateSelect.value;
    currentCity = citySelect.value || '';
    
    // Parse county/ZIP selection
    const countyZipValue = countyZipSelect.value;
    if (countyZipValue) {
        if (countyZipValue.startsWith('zip:')) {
            currentZip = countyZipValue.replace('zip:', '');
        } else {
            currentZip = ''; // County selected, backend will handle
        }
    } else {
        currentZip = '';
    }
    
    // Build location display text
    let locationText = currentState;
    if (currentCity) {
        locationText = `${currentCity}, ${locationData.stateCode || currentState}`;
    }
    if (currentZip) {
        locationText += ` (${currentZip})`;
    }
    
    updateLocationDisplay(locationText);
    
    console.log('Applying filter - State:', currentState, 'City:', currentCity, 'ZIP:', currentZip);
    loadAirQualityData();
    loadHealthRecommendations();
}

// Clear location filter
function clearLocationFilter() {
    const stateSelect = document.getElementById('stateSelect');
    const citySelect = document.getElementById('citySelect');
    const countyZipSelect = document.getElementById('countyZipSelect');
    
    stateSelect.value = 'California';
    citySelect.innerHTML = '<option value="">Select City</option>';
    countyZipSelect.innerHTML = '<option value="">County/ZIP Code</option>';
    citySelect.disabled = true;
    countyZipSelect.disabled = true;
    
    currentState = 'California';
    currentCity = '';
    currentZip = '';
    
    // Reload cities for California
    onStateChange();
    
    updateLocationDisplay('California');
    loadAirQualityData();
    loadHealthRecommendations();
}

// Update location display text
function updateLocationDisplay(location) {
    const locationText = document.getElementById('currentLocationText');
    if (locationText) {
        locationText.textContent = location;
    }
}

// Update API status indicator
function updateAPIStatus(status, message, details = '') {
    const statusIndicator = document.getElementById('statusIndicator');
    const statusText = document.getElementById('statusText');
    const statusInfo = document.getElementById('statusInfo');
    const apiStatus = document.getElementById('apiStatus');
    
    if (!statusIndicator || !statusText) return;
    
    const timestamp = new Date().toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
    
    // RAG colors: Red/Amber/Green
    const statusConfig = {
        loading: {
            color: '#fbbf24', // Amber
            bg: '#fef3c7',
            border: '#fbbf24',
            text: 'Loading...',
            icon: 'fa-spinner fa-spin'
        },
        success: {
            color: '#10b981', // Green
            bg: '#d1fae5',
            border: '#10b981',
            text: 'Connected',
            icon: 'fa-check-circle'
        },
        error: {
            color: '#ef4444', // Red
            bg: '#fee2e2',
            border: '#ef4444',
            text: 'Error',
            icon: 'fa-exclamation-circle'
        },
        warning: {
            color: '#f97316', // Amber/Orange
            bg: '#ffedd5',
            border: '#f97316',
            text: 'Warning',
            icon: 'fa-exclamation-triangle'
        }
    };
    
    const config = statusConfig[status] || statusConfig.error;
    
    // Update indicator dot
    statusIndicator.style.backgroundColor = config.color;
    statusIndicator.className = statusIndicator.className.replace(/fa-\S+/g, '');
    
    // Update text
    statusText.textContent = config.text;
    statusText.style.color = config.color;
    
    // Update container
    apiStatus.style.backgroundColor = config.bg;
    apiStatus.style.borderColor = config.border;
    
    // Update info icon with tooltip
    if (statusInfo) {
        statusInfo.className = `fas ${config.icon} cursor-help`;
        statusInfo.style.color = config.color;
        
        const tooltipText = details 
            ? `${message}\n${details}\nLast updated: ${timestamp}`
            : `${message}\nLast updated: ${timestamp}`;
        
        statusInfo.title = tooltipText;
        
        // Add hover effect for more info
        statusInfo.onmouseover = function() {
            const tooltip = document.createElement('div');
            tooltip.id = 'apiStatusTooltip';
            tooltip.className = 'absolute z-50 bg-gray-900 text-white text-xs rounded-lg py-2 px-3 shadow-lg max-w-xs';
            tooltip.style.right = '0';
            tooltip.style.top = '100%';
            tooltip.style.marginTop = '8px';
            tooltip.innerHTML = tooltipText.replace(/\n/g, '<br>');
            
            apiStatus.style.position = 'relative';
            
            // Remove existing tooltip
            const existing = document.getElementById('apiStatusTooltip');
            if (existing) existing.remove();
            
            apiStatus.appendChild(tooltip);
        };
        
        statusInfo.onmouseout = function() {
            const tooltip = document.getElementById('apiStatusTooltip');
            if (tooltip) tooltip.remove();
        };
    }
}

// Load air quality data
async function loadAirQualityData() {
    showLoading();
    updateAPIStatus('loading', 'Fetching EPA data...', `Requesting data for: ${currentZip || currentState || 'Default location'}`);
    
    try {
        const params = new URLSearchParams({
            days: currentDays
        });
        
        if (currentZip) {
            params.append('zipCode', currentZip);
            console.log('Using ZIP code:', currentZip);
        } else if (currentState) {
            params.append('state', currentState);
            console.log('Using state:', currentState);
        }

        console.log('Fetching air quality data with params:', params.toString());
        const startTime = Date.now();
        const response = await fetch(`/api/air-quality?${params}`);
        const data = await response.json();
        const responseTime = Date.now() - startTime;
        
        console.log('API Response:', data);

        if (data.success) {
            console.log('Data received:', data.data ? data.data.length : 0, 'records');
            
            const recordCount = data.data ? data.data.length : 0;
            updateAPIStatus(
                'success', 
                'EPA API data loaded successfully', 
                `${recordCount} records retrieved in ${responseTime}ms`
            );
            
            // Update current AQI display
            if (data.data && data.data.length > 0) {
                const latestData = data.data[data.data.length - 1];
                updateCurrentAQI(latestData.aqi, latestData.location || (currentZip || currentState));
            }
            
            updateStatistics(data.statistics);
            updateDataTable(data.data);
            updateChart(data.data);
        } else {
            console.error('Failed to load air quality data:', data.error);
            updateAPIStatus('error', 'Failed to load EPA data', data.error || 'Unknown error');
            showError(data.error || 'Failed to load data');
        }
    } catch (error) {
        console.error('Error loading air quality data:', error);
        updateAPIStatus('error', 'Network error', error.message || 'Could not connect to EPA API');
        showError('Network error - please try again');
    } finally {
        hideLoading();
    }
}

// Update current AQI display
function updateCurrentAQI(aqi, location) {
    const currentAqiEl = document.getElementById('currentAqi');
    const aqiLevelEl = document.getElementById('aqiLevel');
    
    if (currentAqiEl) {
        currentAqiEl.textContent = aqi || '--';
    }
    
    if (aqiLevelEl && aqi) {
        const level = getAQILevel(aqi);
        aqiLevelEl.textContent = level.text;
        aqiLevelEl.style.color = level.color;
    }
}

// Get AQI level details
function getAQILevel(aqi) {
    if (aqi <= 50) return { text: 'Good', color: '#10b981' };
    if (aqi <= 100) return { text: 'Moderate', color: '#fbbf24' };
    if (aqi <= 150) return { text: 'Unhealthy for Sensitive Groups', color: '#f97316' };
    if (aqi <= 200) return { text: 'Unhealthy', color: '#ef4444' };
    if (aqi <= 300) return { text: 'Very Unhealthy', color: '#a855f7' };
    return { text: 'Hazardous', color: '#7f1d1d' };
}

// Show error message
function showError(message) {
    const currentAqiEl = document.getElementById('currentAqi');
    const aqiLevelEl = document.getElementById('aqiLevel');
    
    if (currentAqiEl) {
        currentAqiEl.textContent = '--';
    }
    if (aqiLevelEl) {
        aqiLevelEl.textContent = message;
        aqiLevelEl.style.color = '#ef4444';
    }
}

// Update statistics cards with animation
function updateStatistics(stats) {
    const totalRecordsEl = document.getElementById('totalRecords');
    const uniqueLocationsEl = document.getElementById('uniqueLocations');
    const avgAqiEl = document.getElementById('avgAqi');
    
    if (totalRecordsEl && window.animateNumber) {
        animateNumber(totalRecordsEl, 0, stats.total_records || 0, 1500);
    } else if (totalRecordsEl) {
        totalRecordsEl.textContent = formatNumber(stats.total_records || 0);
    }
    
    if (uniqueLocationsEl && window.animateNumber) {
        animateNumber(uniqueLocationsEl, 0, stats.unique_locations || 0, 1500);
    } else if (uniqueLocationsEl) {
        uniqueLocationsEl.textContent = formatNumber(stats.unique_locations || 0);
    }
    
    if (avgAqiEl && window.animateNumber) {
        animateNumber(avgAqiEl, 0, Math.round(stats.avg_aqi || 0), 1500);
    } else if (avgAqiEl) {
        avgAqiEl.textContent = formatNumber(stats.avg_aqi || 0, 1);
    }
}

// Load health recommendations
async function loadHealthRecommendations() {
    try {
        const params = new URLSearchParams();
        if (currentState) {
            params.append('state', currentState);
        }

        const response = await fetch(`/api/health-recommendations?${params}`);
        const data = await response.json();

        if (data.success) {
            updateAQIDisplay(data);
        }
    } catch (error) {
        console.error('Error loading health recommendations:', error);
    }
}


// Update AQI display
function updateAQIDisplay(data) {
    const aqiValue = document.getElementById('currentAqi');
    const aqiLevel = document.getElementById('aqiLevel');
    const recommendation = document.getElementById('recommendation');

    if (aqiValue) {
        if (window.animateNumber) {
            animateNumber(aqiValue, 0, Math.round(data.aqi), 1500);
        } else {
            aqiValue.textContent = Math.round(data.aqi);
        }
    }
    if (aqiLevel) aqiLevel.textContent = data.level;
    if (recommendation) recommendation.textContent = data.recommendation;
}

// Update data table with Tailwind styling
function updateDataTable(data) {
    const tableBody = document.getElementById('dataTableBody');
    if (!tableBody) return;

    if (!data || data.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                    <i class="fas fa-inbox text-3xl mb-2"></i>
                    <p>No data available</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = data.slice(0, 50).map(row => `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-sm text-gray-700">${formatDate(row.date)}</td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.state_name || '-'}</td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.county_name || '-'}</td>
            <td class="px-6 py-4">
                <span class="px-3 py-1 text-sm font-bold rounded-full ${getAQIBadgeClass(row.aqi)}">
                    ${row.aqi || '-'}
                </span>
            </td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.parameter_name || '-'}</td>
            <td class="px-6 py-4 text-sm text-gray-700">${row.site_name || '-'}</td>
        </tr>
    `).join('');
}

// Get AQI badge color class
function getAQIBadgeClass(aqi) {
    if (aqi <= 50) return 'bg-emerald-100 text-emerald-700';
    if (aqi <= 100) return 'bg-yellow-100 text-yellow-700';
    if (aqi <= 150) return 'bg-orange-100 text-orange-700';
    if (aqi <= 200) return 'bg-red-100 text-red-700';
    if (aqi <= 300) return 'bg-purple-100 text-purple-700';
    return 'bg-rose-100 text-rose-700';
}


// Update chart with modern styling
function updateChart(data) {
    if (!data || data.length === 0) {
        console.log('No data available for chart');
        return;
    }

    // Aggregate data by date
    const dateAqiMap = {};
    data.forEach(row => {
        const date = row.date; // Use full date for proper sorting
        if (!dateAqiMap[date]) {
            dateAqiMap[date] = [];
        }
        dateAqiMap[date].push(row.aqi);
    });

    // Calculate average AQI per date and sort by date
    const chartData = Object.keys(dateAqiMap)
        .sort((a, b) => new Date(a) - new Date(b)) // Sort by actual date
        .slice(-currentDays) // Take last N days
        .map(date => ({
            date: date,
            dateFormatted: formatDate(date),
            aqi: average(dateAqiMap[date])
        }));

    console.log('Chart data:', chartData);

    const ctx = document.getElementById('aqiChart');
    if (!ctx) {
        console.error('Chart canvas not found');
        return;
    }

    // Destroy existing chart
    if (aqiChart) {
        aqiChart.destroy();
    }

    // Function to get color based on AQI value
    const getAQIColor = (aqi) => {
        if (aqi <= 50) return '#00E400'; // Good - Green
        if (aqi <= 100) return '#FFFF00'; // Moderate - Yellow
        if (aqi <= 150) return '#FF7E00'; // Unhealthy for Sensitive - Orange
        if (aqi <= 200) return '#FF0000'; // Unhealthy - Red
        if (aqi <= 300) return '#8F3F97'; // Very Unhealthy - Purple
        return '#7E0023'; // Hazardous - Maroon
    };

    // Function to get AQI level text
    const getAQILevel = (aqi) => {
        if (aqi <= 50) return 'Good';
        if (aqi <= 100) return 'Moderate';
        if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
        if (aqi <= 200) return 'Unhealthy';
        if (aqi <= 300) return 'Very Unhealthy';
        return 'Hazardous';
    };

    // Create color array for each point
    const pointColors = chartData.map(d => getAQIColor(d.aqi));
    const borderColors = chartData.map(d => getAQIColor(d.aqi));

    // Create gradient background
    const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    // Calculate max for Y axis
    const maxAqi = Math.max(...chartData.map(d => d.aqi), 100);
    const yAxisMax = Math.ceil(maxAqi / 50) * 50 + 50;

    // Create new chart with zoom and better styling
    aqiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.map(d => d.dateFormatted),
            datasets: [{
                label: 'Average AQI',
                data: chartData.map(d => d.aqi),
                borderColor: '#10b981',
                backgroundColor: gradient,
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 8,
                pointHoverRadius: 12,
                pointBackgroundColor: pointColors,
                pointBorderColor: '#fff',
                pointBorderWidth: 3,
                pointHoverBackgroundColor: pointColors,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 4,
                segment: {
                    borderColor: (ctx) => {
                        const value = ctx.p1.parsed.y;
                        return getAQIColor(value);
                    }
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 16,
                            weight: 'bold',
                            family: "'Inter', sans-serif"
                        },
                        color: '#1a3a52',
                        usePointStyle: true,
                        padding: 20,
                        boxWidth: 15,
                        boxHeight: 15
                    }
                },
                title: {
                    display: true,
                    text: `Air Quality Trend (${currentDays} Days)`,
                    font: {
                        size: 22,
                        weight: 'bold',
                        family: "'Space Grotesk', sans-serif"
                    },
                    color: '#1a3a52',
                    padding: {
                        top: 15,
                        bottom: 25
                    }
                },
                tooltip: {
                    enabled: true,
                    backgroundColor: 'rgba(26, 58, 82, 0.95)',
                    padding: 20,
                    titleFont: {
                        size: 18,
                        weight: 'bold',
                        family: "'Inter', sans-serif"
                    },
                    bodyFont: {
                        size: 16,
                        family: "'Inter', sans-serif"
                    },
                    borderColor: '#10b981',
                    borderWidth: 3,
                    cornerRadius: 15,
                    displayColors: true,
                    callbacks: {
                        title: function(context) {
                            return context[0].label;
                        },
                        label: function(context) {
                            const aqi = Math.round(context.parsed.y);
                            const level = getAQILevel(aqi);
                            return [
                                `AQI: ${aqi}`,
                                `Level: ${level}`
                            ];
                        },
                        labelColor: function(context) {
                            return {
                                borderColor: getAQIColor(context.parsed.y),
                                backgroundColor: getAQIColor(context.parsed.y),
                                borderWidth: 2,
                                borderRadius: 5
                            };
                        }
                    }
                },
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x',
                        modifierKey: 'ctrl'
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.1
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: yAxisMax,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.08)',
                        drawBorder: false,
                        lineWidth: 1
                    },
                    ticks: {
                        font: {
                            size: 14,
                            family: "'Inter', sans-serif",
                            weight: '600'
                        },
                        color: '#374151',
                        stepSize: 25,
                        padding: 12,
                        callback: function(value) {
                            return value;
                        }
                    },
                    title: {
                        display: true,
                        text: 'Air Quality Index (AQI)',
                        font: {
                            size: 16,
                            weight: 'bold',
                            family: "'Inter', sans-serif"
                        },
                        color: '#1a3a52',
                        padding: {
                            top: 5,
                            bottom: 15
                        }
                    },
                    border: {
                        display: true,
                        color: '#d1d5db',
                        width: 2
                    }
                },
                x: {
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.04)',
                        drawBorder: false
                    },
                    ticks: {
                        font: {
                            size: 13,
                            family: "'Inter', sans-serif",
                            weight: '600'
                        },
                        color: '#374151',
                        maxRotation: 45,
                        minRotation: 0,
                        padding: 10
                    },
                    title: {
                        display: true,
                        text: 'Date',
                        font: {
                            size: 16,
                            weight: 'bold',
                            family: "'Inter', sans-serif"
                        },
                        color: '#1a3a52',
                        padding: {
                            top: 15,
                            bottom: 5
                        }
                    },
                    border: {
                        display: true,
                        color: '#d1d5db',
                        width: 2
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });

    console.log('Chart created successfully');
}

// Ask AI function
async function askAI() {
    const questionInput = document.getElementById('questionInput');
    const chatMessages = document.getElementById('chatMessages');
    
    if (!questionInput || !chatMessages) return;
    
    const question = questionInput.value.trim();
    if (!question) return;

    // Check if user is approving Twitter post
    if (lastVideoData && isTwitterApproval(question)) {
        await postToTwitter(lastVideoData);
        questionInput.value = '';
        return;
    }

    // Add user message
    addMessage(question, 'user');
    questionInput.value = '';

    // Show loading
    const loadingMsg = addMessage('Thinking...', 'bot');
    
    try {
        // Try ADK agent first
        const response = await fetch('/api/agent-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                state: currentState,
                days: currentDays
            })
        });

        const data = await response.json();

        // Remove loading message
        loadingMsg.remove();

        if (data.success) {
            // Add agent badge if available
            const agentBadge = data.agent ? `<div class="text-xs text-gray-500 mt-1">via ${data.agent}</div>` : '';
            addMessage(data.response + agentBadge, 'bot');
            
            // If video generation started, begin polling
            if (data.task_id) {
                pollForVideoCompletion(data.task_id);
            }
        } else {
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        loadingMsg.remove();
        addMessage('Sorry, I could not connect to the AI service.', 'bot');
        console.error('Error asking AI:', error);
    }
}

// Check if user message is Twitter approval
function isTwitterApproval(message) {
    const lowerMsg = message.toLowerCase().trim();
    const approvalPhrases = ['yes', 'yeah', 'sure', 'ok', 'okay', 'post it', 'post to twitter', 'tweet it', 'share it'];
    return approvalPhrases.some(phrase => lowerMsg === phrase || lowerMsg.includes(phrase));
}

// Post video to Twitter
async function postToTwitter(videoData) {
    const questionInput = document.getElementById('questionInput');
    
    // Add user's approval message
    addMessage('Yes, post to Twitter', 'user');
    
    // Show posting message
    const loadingMsg = addMessage('Posting to Twitter... (This may take 60-90 seconds: downloading video, uploading to Twitter, processing)', 'bot');
    
    try {
        // Create abort controller for timeout (2 minutes)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes
        
        const response = await fetch('/api/post-to-twitter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                video_url: videoData.video_url,
                message: videoData.action_line,
                hashtags: ['HealthAlert', 'PublicHealth', 'CommunityHealth', 'AirQuality']
            }),
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const result = await response.json();
        
        // Remove loading message
        loadingMsg.remove();
        
        if (result.success) {
            const successMessage = `✓ Posted to Twitter successfully!\n\nView your post: ${result.tweet_url}\n\n${result.message}`;
            addMessage(successMessage, 'bot');
            
            // Clear video data after posting
            lastVideoData = null;
        } else {
            addMessage(`Sorry, I couldn't post to Twitter: ${result.error}`, 'bot');
        }
        
    } catch (error) {
        loadingMsg.remove();
        if (error.name === 'AbortError') {
            addMessage('Twitter posting timed out. The video may still have been posted. Please check your Twitter feed at https://twitter.com/AI_mmunity', 'bot');
        } else {
            addMessage('Sorry, there was an error posting to Twitter. Please try again.', 'bot');
        }
        console.error('Twitter posting error:', error);
    }
    
    // Clear input
    if (questionInput) {
        questionInput.value = '';
    }
}

// Poll for video generation completion
const activeVideoPolls = new Set();

async function pollForVideoCompletion(taskId) {
    // Prevent duplicate polling
    if (activeVideoPolls.has(taskId)) return;
    activeVideoPolls.add(taskId);
    
    console.log(`[VIDEO] Starting poll for task: ${taskId}`);
    
    const maxAttempts = 30; // 30 * 5 sec = 2.5 minutes
    
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
        
        try {
            const response = await fetch(`/api/check-video-task/${taskId}`);
            const status = await response.json();
            
            console.log(`[VIDEO] Poll ${i + 1}: ${status.status} - ${status.progress || 0}%`);
            
            if (status.status === 'complete') {
                // Store video data for potential Twitter posting
                lastVideoData = {
                    video_url: status.video_url,
                    action_line: status.action_line,
                    task_id: taskId
                };
                
                // Video is ready! Add new message with video
                const videoMessage = `✓ Your PSA video is ready!

[VIDEO:${status.video_url}]

Action: "${status.action_line}"

Would you like me to post this to Twitter?`;
                
                addMessage(videoMessage, 'bot');
                activeVideoPolls.delete(taskId);
                console.log(`[VIDEO] Task ${taskId} complete!`);
                console.log('[VIDEO] Video data stored for Twitter posting');
                return;
            } else if (status.status === 'error') {
                // Generation failed
                addMessage(`Sorry, video generation encountered an error: ${status.error}`, 'bot');
                activeVideoPolls.delete(taskId);
                console.error(`[VIDEO] Task ${taskId} failed:`, status.error);
                return;
            }
            // Continue polling if still processing
        } catch (error) {
            console.error('[VIDEO] Polling error:', error);
            // Continue polling despite errors
        }
    }
    
    // Timeout
    activeVideoPolls.delete(taskId);
    addMessage('Video generation timed out. Please try again.', 'bot');
    console.error(`[VIDEO] Task ${taskId} timeout`);
}


// Add message to chat with Tailwind styling
function addMessage(text, type) {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return null;

    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-3 ${type === 'user' ? 'justify-end' : ''}`;
    
    // Parse video markers for bot messages
    let messageContent = text;
    let videoHtml = '';
    
    if (type === 'bot' && text.includes('[VIDEO:')) {
        const videoMatch = text.match(/\[VIDEO:(.*?)\]/);
        if (videoMatch) {
            const videoUrl = videoMatch[1];
            
            // Remove video marker from text
            messageContent = text.replace(/\[VIDEO:.*?\]/, '').trim();
            
            // Create video player
            videoHtml = `
                <div class="my-3">
                    <video 
                        controls 
                        class="w-full rounded-lg shadow-lg" 
                        style="max-width: 300px; max-height: 533px;"
                        preload="metadata"
                    >
                        <source src="${videoUrl}" type="video/mp4">
                        Your browser doesn't support video playback.
                    </video>
                </div>
            `;
        }
    }
    
    if (type === 'bot') {
        messageDiv.innerHTML = `
            <div class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-white"></i>
            </div>
            <div class="bg-white rounded-2xl rounded-tl-none p-4 shadow-md max-w-2xl">
                ${videoHtml}
                <p class="text-gray-700 leading-relaxed whitespace-pre-line">${messageContent}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="bg-navy-700 text-white rounded-2xl rounded-tr-none p-4 shadow-md max-w-lg">
                <p class="leading-relaxed">${text}</p>
            </div>
            <div class="w-10 h-10 bg-navy-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-white"></i>
            </div>
        `;
    }

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Animate the message if anime.js is available
    if (window.animateMessage) {
        animateMessage(messageDiv);
    }

    return messageDiv;
}

// Change days function
function changeDays(days) {
    currentDays = days;
    
    // Update button styles
    document.querySelectorAll('[id^="btn"]').forEach(btn => {
        btn.classList.remove('bg-navy-600', 'text-white');
        btn.classList.add('bg-gray-200', 'text-navy-700');
    });
    
    const activeBtn = document.getElementById(`btn${days}d`);
    if (activeBtn) {
        activeBtn.classList.remove('bg-gray-200', 'text-navy-700');
        activeBtn.classList.add('bg-navy-600', 'text-white');
    }
    
    loadAirQualityData();
}

// Reset chart zoom
function resetChartZoom() {
    if (aqiChart) {
        aqiChart.resetZoom();
    }
}

// Utility functions
function formatNumber(num, decimals = 0) {
    if (typeof num !== 'number') return '-';
    return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function average(arr) {
    if (!arr || arr.length === 0) return 0;
    return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function adjustColor(color, amount) {
    // Simple color adjustment for gradient
    return color;
}

function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }
}

function smoothScrollToSections() {
    // Handled by animations.js
}

// Load weather data
async function loadWeatherData() {
    if (!currentZip && !currentCity) {
        console.log('[Weather] No location set - ZIP:', currentZip, 'City:', currentCity);
        return;
    }
    
    console.log('[Weather] Loading data for ZIP:', currentZip, 'City:', currentCity, 'State:', currentState);
    
    try {
        const params = new URLSearchParams();
        if (currentZip) params.append('zipCode', currentZip);
        else if (currentCity && currentState) {
            params.append('city', currentCity);
            params.append('state', currentState);
        }
        
        const url = `/api/weather?${params.toString()}`;
        console.log('[Weather] Fetching from:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('[Weather] Response:', data);
        
        if (data.success && data.data) {
            updateWeatherDisplay(data.data);
        } else {
            console.error('[Weather] Failed to load:', data.error);
        }
    } catch (error) {
        console.error('[Weather] Error loading data:', error);
    }
}

// Load pollen data
async function loadPollenData() {
    if (!currentZip && !currentCity) {
        console.log('[Pollen] No location set - ZIP:', currentZip, 'City:', currentCity);
        return;
    }
    
    console.log('[Pollen] Loading data for ZIP:', currentZip, 'City:', currentCity, 'State:', currentState);
    
    try {
        const params = new URLSearchParams();
        if (currentZip) params.append('zipCode', currentZip);
        else if (currentCity && currentState) {
            params.append('city', currentCity);
            params.append('state', currentState);
        }
        
        const url = `/api/pollen?${params.toString()}`;
        console.log('[Pollen] Fetching from:', url);
        
        const response = await fetch(url);
        const data = await response.json();
        
        console.log('[Pollen] Response:', data);
        
        if (data.success && data.data) {
            updatePollenDisplay(data.data);
        } else {
            console.error('[Pollen] Failed to load:', data.error);
        }
    } catch (error) {
        console.error('[Pollen] Error loading data:', error);
    }
}

// Update weather display
function updateWeatherDisplay(weather) {
    if (!weather || !weather.current) {
        console.log('[Weather] No data to display');
        return;
    }
    
    const current = weather.current;
    console.log('[Weather] Current data:', current);
    
    // Temperature
    const temp = Math.round(current.temperature || 0);
    const unit = current.temperature_unit || 'F';
    document.getElementById('temperature').textContent = `${temp}°${unit}`;
    document.getElementById('feelsLike').textContent = `Feels like ${Math.round(current.feels_like || 0)}°${unit}`;
    
    // Humidity
    document.getElementById('humidity').textContent = `${Math.round(current.humidity || 0)}%`;
    
    // Wind - use wind_direction (cardinal) directly, use wind_degrees for getWindDirection if needed
    document.getElementById('windSpeed').textContent = `${Math.round(current.wind_speed || 0)} mph`;
    document.getElementById('windDirection').textContent = `Direction: ${current.wind_direction || getWindDirection(current.wind_degrees || 0) || '--'}`;
    
    // UV Index
    const uvIndex = current.uv_index || 0;
    document.getElementById('uvIndex').textContent = uvIndex || '--';
    document.getElementById('uvLevel').textContent = getUVLevel(uvIndex);
    
    // Conditions
    document.getElementById('weatherConditions').textContent = current.conditions || 'Unknown';
    document.getElementById('weatherIcon').textContent = getWeatherIcon(current.conditions || '');
    
    console.log('[Weather] Display updated successfully');
}

// Update pollen display
function updatePollenDisplay(pollen) {
    if (!pollen || !pollen.current) {
        console.log('[Pollen] No data to display');
        return;
    }
    
    const current = pollen.current;
    console.log('[Pollen] Current data:', current);
    
    // UPI
    const upi = current.upi !== undefined ? current.upi : '--';
    document.getElementById('pollenUPI').textContent = upi;
    document.getElementById('pollenLevel').textContent = current.level || 'Unknown';
    
    // Individual indices - handle 0 as valid value
    const treeIndex = current.tree_index !== undefined ? current.tree_index : '--';
    const grassIndex = current.grass_index !== undefined ? current.grass_index : '--';
    const weedIndex = current.weed_index !== undefined ? current.weed_index : '--';
    
    document.getElementById('treeIndex').textContent = treeIndex;
    document.getElementById('grassIndex').textContent = grassIndex;
    document.getElementById('weedIndex').textContent = weedIndex;
    
    // Recommendations
    document.getElementById('pollenRecommendations').textContent = current.health_recommendations || 'No recommendations available';
    
    // Primary plants
    if (current.primary_plants && current.primary_plants.length > 0) {
        document.getElementById('primaryPlants').textContent = `Primary allergens: ${current.primary_plants.join(', ')}`;
    } else {
        document.getElementById('primaryPlants').textContent = 'Primary allergens: None detected';
    }
    
    // Update icon based on level
    document.getElementById('pollenIcon').textContent = getPollenIcon(upi);
    
    console.log('[Pollen] Display updated successfully');
}

// Helper functions
function getWindDirection(degrees) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(degrees / 45) % 8;
    return directions[index] || '--';
}

function getUVLevel(uv) {
    if (uv <= 2) return 'Low';
    if (uv <= 5) return 'Moderate';
    if (uv <= 7) return 'High';
    if (uv <= 10) return 'Very High';
    return 'Extreme';
}

function getWeatherIcon(conditions) {
    const conditionsLower = (conditions || '').toLowerCase();
    if (conditionsLower.includes('clear') || conditionsLower.includes('sunny')) return '☀️';
    if (conditionsLower.includes('cloud')) return '☁️';
    if (conditionsLower.includes('rain')) return '🌧️';
    if (conditionsLower.includes('storm')) return '⛈️';
    if (conditionsLower.includes('snow')) return '❄️';
    if (conditionsLower.includes('fog')) return '🌫️';
    return '🌤️';
}

function getPollenIcon(upi) {
    if (upi <= 1) return '🌱';
    if (upi == 2) return '🌸';
    if (upi == 3) return '🌺';
    if (upi == 4) return '🌼';
    return '🌻';
}
