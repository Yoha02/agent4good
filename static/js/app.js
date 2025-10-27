// Global variables
let aqiChart = null;
let currentState = '';
let currentCity = '';
let currentZip = '';
let lastVideoData = null; // Store video data for Twitter posting

// Voice control variables
let recognition = null;
let isListening = false;
let speechEnabled = false;
let currentUtterance = null;
let selectedVoice = 'en-US-Neural2-F'; // Google Cloud TTS voice (Female Neural2)
let currentAudio = null;

// Initialize speech recognition
function initializeSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = function() {
            isListening = true;
            updateMicrophoneButton();
            console.log('[VOICE] Speech recognition started');
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            console.log('[VOICE] Recognized:', transcript);
            document.getElementById('questionInput').value = transcript;
            // Automatically ask the question
            setTimeout(() => askAI(), 500);
        };

        recognition.onerror = function(event) {
            console.error('[VOICE] Speech recognition error:', event.error);
            isListening = false;
            updateMicrophoneButton();
            if (event.error === 'not-allowed') {
                alert('Microphone access denied. Please enable microphone permissions.');
            }
        };

        recognition.onend = function() {
            isListening = false;
            updateMicrophoneButton();
            console.log('[VOICE] Speech recognition ended');
        };

        return true;
    } else {
        console.warn('[VOICE] Speech recognition not supported');
        return false;
    }
}

// Toggle voice input
function toggleVoiceInput() {
    if (!recognition) {
        if (!initializeSpeechRecognition()) {
            alert('Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.');
            return;
        }
    }

    if (isListening) {
        recognition.stop();
    } else {
        recognition.start();
    }
}

// Update microphone button state
function updateMicrophoneButton() {
    const micButton = document.getElementById('micButton');
    if (micButton) {
        if (isListening) {
            micButton.classList.add('bg-red-500', 'hover:bg-red-600');
            micButton.classList.remove('bg-gray-500', 'hover:bg-gray-600');
            micButton.innerHTML = '<i class="fas fa-microphone-slash"></i>';
        } else {
            micButton.classList.add('bg-gray-500', 'hover:bg-gray-600');
            micButton.classList.remove('bg-red-500', 'hover:bg-red-600');
            micButton.innerHTML = '<i class="fas fa-microphone"></i>';
        }
    }
}

// Toggle speech output
function toggleSpeechOutput() {
    speechEnabled = !speechEnabled;
    
    // Stop any current speech
    if (!speechEnabled && currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    
    // Update button state
    const speakerButton = document.getElementById('speakerButton');
    if (speakerButton) {
        if (speechEnabled) {
            speakerButton.classList.add('bg-emerald-500', 'hover:bg-emerald-600');
            speakerButton.classList.remove('bg-gray-500', 'hover:bg-gray-600');
            speakerButton.innerHTML = '<i class="fas fa-volume-up"></i>';
        } else {
            speakerButton.classList.add('bg-gray-500', 'hover:bg-gray-600');
            speakerButton.classList.remove('bg-emerald-500', 'hover:bg-emerald-600');
            speakerButton.innerHTML = '<i class="fas fa-volume-mute"></i>';
        }
    }
    
    console.log('[VOICE] Speech output:', speechEnabled ? 'enabled (Google Cloud TTS)' : 'disabled');
}

// Change voice selection
function changeVoice(voiceName) {
    selectedVoice = voiceName;
    console.log('[VOICE] Voice changed to:', voiceName);
}

// Preview the selected voice
async function previewVoice() {
    const previewText = "Hello! I'm your AI health advisor. This is how I sound with the selected voice.";
    
    // Temporarily enable speech for preview if disabled
    const wasEnabled = speechEnabled;
    speechEnabled = true;
    
    await speakText(previewText);
    
    // Restore original state
    speechEnabled = wasEnabled;
}

// Speak text using Google Cloud Text-to-Speech
async function speakText(text) {
    if (!speechEnabled) return;
    
    // Stop any ongoing speech
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    
    // Remove HTML tags for clean text
    const cleanText = text.replace(/<[^>]*>/g, '').replace(/via.*$/, '').trim();
    
    if (!cleanText) return;
    
    try {
        console.log('[VOICE] Requesting Google TTS for:', cleanText.substring(0, 50) + '...');
        
        // Call backend API for Google TTS
        const response = await fetch('/api/text-to-speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: cleanText,
                voice: selectedVoice
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.audio) {
            // Convert base64 to audio blob
            const audioBlob = base64ToBlob(data.audio, 'audio/mp3');
            const audioUrl = URL.createObjectURL(audioBlob);
            
            // Create and play audio
            currentAudio = new Audio(audioUrl);
            currentAudio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
            };
            
            currentAudio.onerror = (error) => {
                console.error('[VOICE] Audio playback error:', error);
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
            };
            
            await currentAudio.play();
            console.log('[VOICE] Playing Google TTS audio with voice:', data.voice);
        } else {
            console.error('[VOICE] TTS failed:', data.error);
        }
    } catch (error) {
        console.error('[VOICE] Text-to-Speech error:', error);
    }
}

// Helper function to convert base64 to blob
function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
}
let currentDays = 7;
let locationData = {}; // Cache location data
let autocomplete = null; // Google Places Autocomplete
let geocoder = null; // Google Geocoder

// Add getters/setters to track location changes
let _currentState = '';
let _currentCity = '';
let _currentZip = '';

Object.defineProperty(window, 'currentState', {
    get() { return _currentState; },
    set(value) {
        console.log(`🔄 [LOCATION CHANGE] currentState: "${_currentState}" → "${value}"`);
        _currentState = value;
    }
});

Object.defineProperty(window, 'currentCity', {
    get() { return _currentCity; },
    set(value) {
        console.log(`🔄 [LOCATION CHANGE] currentCity: "${_currentCity}" → "${value}"`);
        _currentCity = value;
    }
});

Object.defineProperty(window, 'currentZip', {
    get() { return _currentZip; },
    set(value) {
        console.log(`🔄 [LOCATION CHANGE] currentZip: "${_currentZip}" → "${value}"`);
        _currentZip = value;
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 [INIT] DOMContentLoaded event fired');
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
    
    // Initialize autocomplete for US locations including landmarks, cities, regions, and postal codes
    autocomplete = new google.maps.places.Autocomplete(input, {
        // Remove type restriction to allow all place types including landmarks
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
    
    // Store location data in browser storage for chat agent
    const locationData = {
        city: city,
        state: state,
        county: county,
        zipCode: zipCode,
        formattedAddress: place.formatted_address,
        coordinates: {
            lat: place.geometry.location.lat(),
            lng: place.geometry.location.lng()
        },
        timestamp: new Date().toISOString()
    };
    
    // Store in localStorage for persistence
    localStorage.setItem('currentLocationData', JSON.stringify(locationData));
    console.log('[Location Search] Location data stored for chat agent:', locationData);
    
    // Update dropdowns if applicable
    if (state) {
        document.getElementById('stateSelect').value = state || '';
    }
    
    // Load ALL data for this location
    loadAllDataForLocation();
    
    // Update heatmap and zoom to location
    if (typeof loadHeatmapData === 'function') {
        loadHeatmapData(state);
    }
    // Zoom to the specific searched location
    if (place.geometry && place.geometry.location && typeof flyToCoordinates === 'function') {
        const lat = place.geometry.location.lat();
        const lng = place.geometry.location.lng();
        console.log('[Location Search] Flying to coordinates:', lat, lng);
        flyToCoordinates(lat, lng, 300); // Always use 300m height for close ground view
    }
    
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
                            
                            // Store location data in browser storage for chat agent
                            const locationData = {
                                city: city,
                                state: state,
                                county: '', // Auto-location doesn't provide county
                                zipCode: zipCode,
                                formattedAddress: results[0].formatted_address,
                                coordinates: {
                                    lat: position.coords.latitude,
                                    lng: position.coords.longitude
                                },
                                timestamp: new Date().toISOString(),
                                source: 'auto-location'
                            };
                            
                            // Store in localStorage for persistence
                            localStorage.setItem('currentLocationData', JSON.stringify(locationData));
                            console.log('[Auto-location] Location data stored for chat agent:', locationData);
                            
                            // Update search box with full formatted address
                            document.getElementById('locationSearch').value = results[0].formatted_address;
                            
                            // Update dropdowns
    const stateSelect = document.getElementById('stateSelect');
    if (stateSelect) {
                                stateSelect.value = state || '';
                            }
                            
                            // Load ALL data for this location
            loadAllDataForLocation();
                            
                            // Update heatmap - fly to specific location instead of just state
                            if (typeof loadHeatmapData === 'function') {
                                loadHeatmapData(state);
                            }
                            // Zoom to specific coordinates - close ground view
                            if (typeof flyToCoordinates === 'function') {
                                flyToCoordinates(position.coords.latitude, position.coords.longitude, 300); // 300m height for close view
                            }
                            
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
    // Set default date range (2024 to 2025)
    setDefaultDateRange();
    
    // Update date range display
    updateDateRangeDisplay();
    
    updateAPIStatus('loading', 'Initializing...', 'Detecting your location...');
    
    const defaultZip = '94102';
    const defaultCity = 'San Francisco';
    const defaultState = 'California';
    
    const restoredFromStorage = loadStoredLocationData();
    
    if (!currentState && !currentCity && !currentZip) {
        console.log('[APP] Using default location for initial data load:', defaultCity);
        currentZip = defaultZip;
        currentCity = defaultCity;
        currentState = defaultState;
        
        const searchInput = document.getElementById('locationSearch');
        if (searchInput) {
            searchInput.value = `${defaultCity}, ${defaultState} ${defaultZip}`;
        }
    } else {
        console.log('[APP] Initial location resolved:', {
            currentCity,
            currentState,
            currentZip
        });
    }
    
    const stateSelect = document.getElementById('stateSelect');
    if (stateSelect && currentState) {
        stateSelect.value = currentState;
    }
    
    loadAllDataForLocation();
    
    if (!restoredFromStorage) {
        console.log('[APP] No stored location detected, attempting auto-location...');
        autoDetectAndLoadLocation();
    }
}

// Auto-detect location and load all data
function autoDetectAndLoadLocation() {
    const defaultZip = '94102';
    const defaultCity = 'San Francisco';
    const defaultState = 'California';
    
    const applyDefaultLocation = (statusDetails) => {
        currentZip = defaultZip;
        currentCity = defaultCity;
        currentState = defaultState;
        
        const searchInput = document.getElementById('locationSearch');
        if (searchInput) {
            searchInput.value = `${defaultCity}, ${defaultState} ${defaultZip}`;
        }
        
        const stateSelect = document.getElementById('stateSelect');
        if (stateSelect) {
            stateSelect.value = defaultState;
        }
        
        loadAllDataForLocation();
        updateAPIStatus('warning', 'Using Default', statusDetails || `${defaultCity}, ${defaultState}`);
    };
    
    if (!navigator.geolocation) {
        console.warn('[APP] Geolocation not supported - defaulting to California');
        applyDefaultLocation(`${defaultCity}, ${defaultState} (geolocation not supported)`);
        return;
    }
    
    if (typeof google === 'undefined' || typeof google.maps === 'undefined') {
        console.warn('[APP] Google Maps not loaded yet - defaulting to California');
        applyDefaultLocation(`${defaultCity}, ${defaultState} (maps not ready)`);
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;
            
            console.log(`[APP Auto-location] Coordinates: ${lat}, ${lon}`);
            
            if (!geocoder) {
                geocoder = new google.maps.Geocoder();
            }
            
            geocoder.geocode(
                { location: { lat, lng: lon } },
                (results, status) => {
                    if (status === 'OK' && results[0]) {
                        console.log('[APP Auto-location] Geocoded result:', results[0]);
                        
                        let city = '';
                        let state = '';
                        let zipCode = '';
                        let county = '';
                        
                        for (const component of results[0].address_components) {
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
                        
                        console.log(`[APP Auto-location] Detected: ${city}, ${state} ${zipCode}`);
                        
                        if (state) {
                            currentZip = zipCode;
                            currentState = state;
                            currentCity = city;
                            
                            const locationData = {
                                city: city,
                                state: state,
                                county: county,
                                zipCode: zipCode,
                                formattedAddress: results[0].formatted_address,
                                coordinates: {
                                    lat: position.coords.latitude,
                                    lng: position.coords.longitude
                                },
                                timestamp: new Date().toISOString(),
                                source: 'auto-detection'
                            };
                            
                            localStorage.setItem('currentLocationData', JSON.stringify(locationData));
                            console.log('[APP Auto-location] Location data stored:', locationData);
                            
                            const searchInput = document.getElementById('locationSearch');
                            if (searchInput) {
                                searchInput.value = `${city}, ${state}${zipCode ? ' ' + zipCode : ''}`;
                            }
                            
                            const stateSelect = document.getElementById('stateSelect');
                            if (stateSelect) {
                                stateSelect.value = state || '';
                            }
                            
                            loadAllDataForLocation();
                            
                            if (typeof loadHeatmapData === 'function') {
                                loadHeatmapData(state);
                            }
                            if (typeof flyToCoordinates === 'function') {
                                flyToCoordinates(position.coords.latitude, position.coords.longitude, 50000);
                            }
                            
                            const locationPieces = [city, state].filter(Boolean);
                            const details = locationPieces.length ? locationPieces.join(', ') : state || 'Location detected';
                            const zipDetails = zipCode ? ` (${zipCode})` : '';
                            updateAPIStatus('success', 'Location Detected', `${details}${zipDetails}`);
                        } else {
                            console.warn('[APP Auto-location] Could not determine state - defaulting to California');
                            applyDefaultLocation(`${defaultCity}, ${defaultState} (state not detected)`);
                        }
                    } else {
                        console.error('[APP Auto-location] Geocoding failed:', status);
                        applyDefaultLocation(`${defaultCity}, ${defaultState} (geocoding failed)`);
                    }
                }
            );
        },
        (error) => {
            console.error('[APP Auto-location] Error:', error);
            applyDefaultLocation(`${defaultCity}, ${defaultState} (location denied)`);
        },
        {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 0
        }
    );
}

// Load all data for the current location
function loadAllDataForLocation() {
    console.log('');
    console.log('═══════════════════════════════════════════════════════');
    console.log('[DATA LOAD DEBUG] Starting loadAllDataForLocation()');
    console.log('[DATA LOAD DEBUG] Current State:', currentState);
    console.log('[DATA LOAD DEBUG] Current City:', currentCity);
    console.log('[DATA LOAD DEBUG] Current ZIP:', currentZip);
    console.log('═══════════════════════════════════════════════════════');
    console.log('');
    
    // Update location indicators on all components
    console.log('[1/7] Updating location indicators...');
    updateLocationIndicators();
    
    // Load air quality data and health recommendations
    console.log('[2/7] Loading air quality data...');
    loadAirQualityData();
    
    console.log('[3/7] Loading health recommendations...');
    loadHealthRecommendations();
    
    // Load weather and pollen data
    console.log('[4/7] Loading weather data...');
    loadWeatherData();
    
    console.log('[5/7] Loading pollen data...');
    loadPollenData();
    
    console.log('[6/7] Loading summary cards...');
    loadSummaryCards();
    
    console.log('[7/7] Updating disease cards (async)...');
    setTimeout(() => {
        if (typeof window.updateDiseaseCards === 'function') {
            window.updateDiseaseCards(currentDays || 7);
        } else {
            console.warn('[DATA LOAD DEBUG] updateDiseaseCards function not available yet');
        }
    }, 1000);
    
    console.log('');
    console.log('[DATA LOAD DEBUG] All load functions called');
    console.log('═══════════════════════════════════════════════════════');
    console.log('');
}

// Update location indicators on all components
function updateLocationIndicators() {
    const locationText = currentCity && currentState 
        ? `${currentCity}, ${currentState}${currentZip ? ' ' + currentZip : ''}`
        : currentState || 'No location';
    
    console.log('[Location Indicators] ===== UPDATING INDICATORS =====');
    console.log('[Location Indicators] Current location:', { currentCity, currentState, currentZip });
    console.log('[Location Indicators] Display text:', locationText);
    
    // Update each component's location indicator
    const indicators = [
        'aqiLocationIndicator',
        'trendLocationIndicator',
        'weatherLocationIndicator',
        'pollenLocationIndicator',
        'dataExplorerLocationIndicator'
    ];
    
    indicators.forEach(id => {
        const element = document.getElementById(id);
        console.log(`[Location Indicators] Looking for element: ${id}`, element ? 'FOUND' : 'NOT FOUND');
        if (element) {
            const span = element.querySelector('span');
            console.log(`[Location Indicators] Looking for span inside ${id}:`, span ? 'FOUND' : 'NOT FOUND');
            if (span) {
                span.textContent = locationText;
                console.log(`[Location Indicators] ✓ Updated ${id} to: ${locationText}`);
            } else {
                console.error(`[Location Indicators] ✗ No span found in ${id}`);
            }
        } else {
            console.error(`[Location Indicators] ✗ Element ${id} not found in DOM`);
        }
    });
    
    console.log('[Location Indicators] ===== DONE =====');
}

// Set default date range (2024 to 2025)
function setDefaultDateRange() {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        // Set default dates to 2024-2025
        startDateInput.value = '2024-01-01';
        endDateInput.value = '2025-12-31';
        
        console.log('[APP] Default date range set: 2024-01-01 to 2025-12-31');
    }
}

// Load stored location data from localStorage
function loadStoredLocationData() {
    const storedLocationData = localStorage.getItem('currentLocationData');
    let restored = false;
    
    if (storedLocationData) {
        try {
            const locationData = JSON.parse(storedLocationData);
            
            // Check if location data is recent (within 24 hours)
            const dataAge = Date.now() - new Date(locationData.timestamp).getTime();
            const maxAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
            
            if (dataAge < maxAge) {
                // Restore location data
                currentState = locationData.state || '';
                currentCity = locationData.city || '';
                currentZip = locationData.zipCode || '';
                restored = true;
                
                // Update search box if it exists
                const searchInput = document.getElementById('locationSearch');
                if (searchInput && locationData.formattedAddress) {
                    searchInput.value = locationData.formattedAddress;
                }
                
                console.log('[APP] Restored location data:', locationData);
                updateAPIStatus('success', 'Location Restored', `${locationData.city || ''}, ${locationData.state || ''}`);
            } else {
                console.log('[APP] Stored location data is too old, clearing');
                localStorage.removeItem('currentLocationData');
            }
        } catch (e) {
            console.warn('[APP] Failed to parse stored location data:', e);
            localStorage.removeItem('currentLocationData');
        }
    }
    
    return restored;
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
    
    // Date picker change listeners
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput) {
        startDateInput.addEventListener('change', function() {
            console.log('[Date Picker] Start date changed:', this.value);
            updateDateRangeDisplay();
            // Refresh charts if we have a location
            if (currentZip || (currentCity && currentState)) {
                console.log('[Date Picker] Refreshing charts with new date range');
                initializePollutantCharts(currentZip, currentCity, currentState);
            }
        });
    }
    
    if (endDateInput) {
        endDateInput.addEventListener('change', function() {
            console.log('[Date Picker] End date changed:', this.value);
            updateDateRangeDisplay();
            // Refresh charts if we have a location
            if (currentZip || (currentCity && currentState)) {
                console.log('[Date Picker] Refreshing charts with new date range');
                initializePollutantCharts(currentZip, currentCity, currentState);
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
    
    // Update chat location context indicator
    updateChatLocationContext(locationText);
    
    console.log('Applying filter - State:', currentState, 'City:', currentCity, 'ZIP:', currentZip);
    
    // Load ALL data for the new location
    loadAllDataForLocation();
    
    // Update heatmap - zoom to state level
    if (typeof loadHeatmapData === 'function') {
        loadHeatmapData(currentState);
    }
    // If we have city data, try to get coordinates and zoom closer
    if (currentCity && currentState && typeof geocoder !== 'undefined') {
        const address = currentCity + ', ' + currentState;
        geocoder.geocode({ address: address }, (results, status) => {
            if (status === 'OK' && results[0] && typeof flyToCoordinates === 'function') {
                const location = results[0].geometry.location;
                flyToCoordinates(location.lat(), location.lng(), currentZip ? 50000 : 200000);
            }
        });
    }
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
    
    // Load ALL data for California
    loadAllDataForLocation();
    
    // Update heatmap if it exists
    if (typeof loadHeatmapData === 'function') {
        loadHeatmapData('California');
    }
}

// Update location display text
function updateLocationDisplay(location) {
    const locationText = document.getElementById('currentLocationText');
    if (locationText) {
        locationText.textContent = location;
    }
    
    // Update date range display
    updateDateRangeDisplay();
}

// Update date range display
function updateDateRangeDisplay() {
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const dateRangeText = document.getElementById('dateRangeText');
    
    if (startDateInput && endDateInput && dateRangeText) {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        
        if (startDate && endDate) {
            // Format dates for display
            const startFormatted = new Date(startDate).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short' 
            });
            const endFormatted = new Date(endDate).toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short' 
            });
            
            dateRangeText.textContent = `(${startFormatted} - ${endFormatted})`;
        } else {
            dateRangeText.textContent = '';
        }
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
    console.log('┌─────────────────────────────────────────────────────┐');
    console.log('│ [AIR QUALITY] Starting loadAirQualityData()        │');
    console.log('├─────────────────────────────────────────────────────┤');
    console.log('│ Location Variables:                                 │');
    console.log('│  - State:', currentState || '(empty)');
    console.log('│  - City:', currentCity || '(empty)');
    console.log('│  - ZIP:', currentZip || '(empty)');
    console.log('└─────────────────────────────────────────────────────┘');
    
    showLoading();
    updateAPIStatus('loading', 'Fetching EPA data...', `Requesting data for: ${currentZip || currentState || 'Default location'}`);
    
    try {
        const params = new URLSearchParams({
            days: currentDays
        });
        
        // Add date range parameters
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (startDateInput && startDateInput.value) {
            params.append('start_date', startDateInput.value);
            console.log('Using start date:', startDateInput.value);
        }
        
        if (endDateInput && endDateInput.value) {
            params.append('end_date', endDateInput.value);
            console.log('Using end date:', endDateInput.value);
        }
        
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
                
                // Update summary AQI card
                const summaryAQIEl = document.getElementById('summaryAQI');
                if (summaryAQIEl && latestData.aqi) {
                    summaryAQIEl.textContent = Math.round(latestData.aqi);
                }
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
        
        // Add date range parameters
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (startDateInput && startDateInput.value) {
            params.append('start_date', startDateInput.value);
        }
        
        if (endDateInput && endDateInput.value) {
            params.append('end_date', endDateInput.value);
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

// Update chat location context indicator
function updateChatLocationContext(locationText) {
    const contextDiv = document.getElementById('chatLocationContext');
    const contextTextSpan = document.getElementById('chatLocationText');
    
    if (contextDiv && contextTextSpan) {
        if (locationText && locationText !== 'California') {
            contextTextSpan.textContent = locationText;
            contextDiv.classList.remove('hidden');
        } else {
            contextDiv.classList.add('hidden');
        }
    }
}

// ========================================
// AGENT WORKFLOW VISUALIZATION
// ========================================

let workflowPanelVisible = false;
let useStreaming = true; // Set to true to enable workflow visualization
let workflowView = 'list'; // 'list' or 'graph'

// D3.js graph state
let graphNodes = [];
let graphLinks = [];
let lastNodeInFlow = null; // Track the last node in the workflow sequence
let simulation = null;
let svg = null;
let g = null;

// Toggle between list and graph view
function setWorkflowView(view) {
    workflowView = view;
    const listContainer = document.getElementById('agentFlowContainer');
    const graphContainer = document.getElementById('agentGraphContainer');
    const listBtn = document.getElementById('viewListBtn');
    const graphBtn = document.getElementById('viewGraphBtn');
    
    if (view === 'list') {
        listContainer.classList.remove('hidden');
        graphContainer.classList.add('hidden');
        listBtn.classList.add('bg-emerald-500', 'text-white');
        listBtn.classList.remove('bg-gray-200', 'text-gray-700');
        graphBtn.classList.remove('bg-emerald-500', 'text-white');
        graphBtn.classList.add('bg-gray-200', 'text-gray-700');
    } else {
        listContainer.classList.add('hidden');
        graphContainer.classList.remove('hidden');
        graphBtn.classList.add('bg-emerald-500', 'text-white');
        graphBtn.classList.remove('bg-gray-200', 'text-gray-700');
        listBtn.classList.remove('bg-emerald-500', 'text-white');
        listBtn.classList.add('bg-gray-200', 'text-gray-700');
        
        // Initialize or update graph
        if (!simulation) {
            initializeGraph();
        }
    }
}

// Initialize D3.js force-directed graph
function initializeGraph() {
    const container = document.getElementById('agentGraphContainer');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    svg = d3.select('#agentGraphSvg');
    svg.selectAll('*').remove(); // Clear previous content
    
    // Create zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.5, 3])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Create main group
    g = svg.append('g');
    
    // Add arrow markers for links
    const defs = svg.append('defs');
    
    // Regular arrow
    defs.append('marker')
        .attr('id', 'arrowhead')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .append('path')
        .attr('d', 'M 0,-5 L 10,0 L 0,5')
        .attr('fill', '#10b981');
    
    // Self-loop arrow (different color)
    defs.append('marker')
        .attr('id', 'arrowhead-self')
        .attr('viewBox', '-0 -5 10 10')
        .attr('refX', 25)
        .attr('refY', 0)
        .attr('orient', 'auto')
        .attr('markerWidth', 8)
        .attr('markerHeight', 8)
        .append('path')
        .attr('d', 'M 0,-5 L 10,0 L 0,5')
        .attr('fill', '#f59e0b');
    
    // Create force simulation
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));
    
    updateGraph();
}

// Add node to graph (with deduplication)
function addGraphNode(stepData) {
    let nodeType = 'default';
    let label = 'Processing';
    let color = '#6b7280';
    let nodeKey = 'processing'; // Unique key for deduplication
    
    if (stepData.type === 'start') {
        nodeType = 'start';
        label = 'Start';
        color = '#3b82f6';
        nodeKey = 'start';
    } else if (stepData.type === 'agent_active') {
        nodeType = 'agent';
        label = stepData.agent ? formatAgentName(stepData.agent) : 'Agent';
        color = '#10b981';
        nodeKey = `agent_${stepData.agent || 'unknown'}`;
    } else if (stepData.type === 'tool_call') {
        nodeType = 'tool';
        label = stepData.tool ? formatToolName(stepData.tool) : 'Tool';
        color = '#a855f7';
        nodeKey = `tool_${stepData.tool || 'unknown'}`;
    } else if (stepData.type === 'thinking') {
        // Skip "thinking" nodes - they just update the active state of the last agent
        if (graphNodes.length > 0) {
            const lastNode = graphNodes[graphNodes.length - 1];
            if (lastNode.type === 'agent') {
                lastNode.active = true;
                updateGraph();
            }
        }
        return;
    } else if (stepData.type === 'final_response') {
        nodeType = 'complete';
        label = 'Complete';
        color = '#22c55e';
        nodeKey = 'complete';
    }
    
    // Check if node already exists
    let existingNode = graphNodes.find(n => n.key === nodeKey);
    
    if (existingNode) {
        // Node exists - just update its active state and add a link
        existingNode.active = stepData.type === 'agent_active' || stepData.type === 'thinking';
        existingNode.callCount = (existingNode.callCount || 1) + 1;
        
        // Add link from last node in flow to this existing node
        if (lastNodeInFlow && lastNodeInFlow.id !== existingNode.id) {
            // Check if link already exists to avoid duplicates
            const linkExists = graphLinks.some(
                l => (l.source.id || l.source) === lastNodeInFlow.id && 
                     (l.target.id || l.target) === existingNode.id
            );
            
            if (!linkExists) {
                graphLinks.push({
                    source: lastNodeInFlow.id,
                    target: existingNode.id
                });
            }
        }
        
        // Update last node in flow
        lastNodeInFlow = existingNode;
    } else {
        // Create new node
        const nodeId = `node_${graphNodes.length}`;
        const newNode = {
            id: nodeId,
            key: nodeKey,
            type: nodeType,
            label: label,
            color: color,
            active: stepData.type === 'agent_active' || stepData.type === 'thinking',
            timestamp: stepData.timestamp,
            callCount: 1
        };
        
        graphNodes.push(newNode);
        
        // Add link from last node in flow
        if (lastNodeInFlow) {
            graphLinks.push({
                source: lastNodeInFlow.id,
                target: nodeId
            });
        }
        
        // Update last node in flow
        lastNodeInFlow = newNode;
    }
    
    updateGraph();
}

// Update D3.js graph
function updateGraph() {
    if (!simulation || !g) return;
    
    // Update links (separate self-loops from regular links)
    const regularLinks = graphLinks.filter(l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        return sourceId !== targetId;
    });
    
    const selfLoops = graphLinks.filter(l => {
        const sourceId = l.source.id || l.source;
        const targetId = l.target.id || l.target;
        return sourceId === targetId;
    });
    
    // Render regular links as lines
    const link = g.selectAll('.link')
        .data(regularLinks, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
    
    link.exit().remove();
    
    const linkEnter = link.enter()
        .append('line')
        .attr('class', 'link')
        .attr('stroke', '#10b981')
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.6)
        .attr('marker-end', 'url(#arrowhead)');
    
    const linkMerge = linkEnter.merge(link);
    
    // Render self-loops as curved paths
    const selfLoop = g.selectAll('.self-loop')
        .data(selfLoops, d => `${d.source.id || d.source}-${d.target.id || d.target}`);
    
    selfLoop.exit().remove();
    
    const selfLoopEnter = selfLoop.enter()
        .append('path')
        .attr('class', 'self-loop')
        .attr('fill', 'none')
        .attr('stroke', '#f59e0b')
        .attr('stroke-width', 2)
        .attr('stroke-opacity', 0.8)
        .attr('marker-end', 'url(#arrowhead-self)');
    
    const selfLoopMerge = selfLoopEnter.merge(selfLoop);
    
    // Update nodes
    const node = g.selectAll('.node')
        .data(graphNodes, d => d.id);
    
    node.exit().remove();
    
    const nodeEnter = node.enter()
        .append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));
    
    // Add circle
    nodeEnter.append('circle')
        .attr('r', 0)
        .attr('fill', d => d.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 3)
        .transition()
        .duration(500)
        .attr('r', 25);
    
    // Add pulsing circle for active nodes
    nodeEnter.filter(d => d.active)
        .append('circle')
        .attr('class', 'pulse')
        .attr('r', 25)
        .attr('fill', 'none')
        .attr('stroke', d => d.color)
        .attr('stroke-width', 2)
        .attr('opacity', 0.8)
        .call(pulse);
    
    // Add label
    nodeEnter.append('text')
        .attr('dy', 45)
        .attr('text-anchor', 'middle')
        .attr('fill', '#1f2937')
        .attr('font-size', '11px')
        .attr('font-weight', '600')
        .text(d => d.label);
    
    // Add call count badge for repeated calls
    nodeEnter.filter(d => (d.callCount || 1) > 1)
        .append('circle')
        .attr('cx', 18)
        .attr('cy', -18)
        .attr('r', 10)
        .attr('fill', '#ef4444')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    
    nodeEnter.filter(d => (d.callCount || 1) > 1)
        .append('text')
        .attr('x', 18)
        .attr('y', -14)
        .attr('text-anchor', 'middle')
        .attr('fill', '#fff')
        .attr('font-size', '10px')
        .attr('font-weight', 'bold')
        .text(d => d.callCount);
    
    // Add icon
    nodeEnter.append('text')
        .attr('dy', 5)
        .attr('text-anchor', 'middle')
        .attr('fill', '#fff')
        .attr('font-size', '14px')
        .attr('font-family', 'FontAwesome')
        .text(d => {
            if (d.type === 'start') return '\uf04b'; // play
            if (d.type === 'agent') return '\uf544'; // robot
            if (d.type === 'tool') return '\uf0ad'; // wrench
            if (d.type === 'complete') return '\uf00c'; // check
            return '\uf111'; // circle
        });
    
    const nodeMerge = nodeEnter.merge(node);
    
    // Update call count badges for existing nodes
    nodeMerge.selectAll('circle').filter(function() {
        return d3.select(this).attr('cx') === '18'; // Only the badge circles
    }).remove();
    
    nodeMerge.selectAll('text').filter(function() {
        return d3.select(this).attr('x') === '18'; // Only the badge text
    }).remove();
    
    nodeMerge.filter(d => (d.callCount || 1) > 1)
        .append('circle')
        .attr('cx', 18)
        .attr('cy', -18)
        .attr('r', 10)
        .attr('fill', '#ef4444')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    
    nodeMerge.filter(d => (d.callCount || 1) > 1)
        .append('text')
        .attr('x', 18)
        .attr('y', -14)
        .attr('text-anchor', 'middle')
        .attr('fill', '#fff')
        .attr('font-size', '10px')
        .attr('font-weight', 'bold')
        .text(d => d.callCount);
    
    // Update simulation
    simulation.nodes(graphNodes);
    simulation.force('link').links(graphLinks);
    simulation.alpha(1).restart();
    
    simulation.on('tick', () => {
        // Update regular links
        linkMerge
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        // Update self-loops as curved paths
        selfLoopMerge.attr('d', d => {
            const x = d.source.x;
            const y = d.source.y;
            const loopSize = 40;
            return `M ${x},${y - 25} 
                    C ${x + loopSize},${y - loopSize} 
                      ${x + loopSize},${y + loopSize} 
                      ${x},${y + 25}`;
        });
        
        nodeMerge.attr('transform', d => `translate(${d.x},${d.y})`);
    });
}

// Pulsing animation for active nodes
function pulse(selection) {
    (function repeat() {
        selection
            .transition()
            .duration(1000)
            .attr('r', 35)
            .attr('opacity', 0)
            .transition()
            .duration(0)
            .attr('r', 25)
            .attr('opacity', 0.8)
            .on('end', repeat);
    })();
}

// Drag functions
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// Clear graph
function clearGraph() {
    graphNodes = [];
    graphLinks = [];
    lastNodeInFlow = null;
    if (simulation) {
        simulation.stop();
        simulation = null;
    }
    if (svg) {
        svg.selectAll('*').remove();
        svg = null;
    }
    g = null;
}

// Toggle workflow panel visibility
function toggleWorkflowPanel() {
    const panel = document.getElementById('agentWorkflowPanel');
    const toggleText = document.getElementById('workflowToggleText');
    const toggleBtn = document.getElementById('workflowToggleBtn');
    
    if (!panel || !toggleText) return;
    
    workflowPanelVisible = !workflowPanelVisible;
    
    if (workflowPanelVisible) {
        panel.classList.remove('hidden');
        toggleText.textContent = 'Hide Agent Workflow';
        if (toggleBtn) {
            toggleBtn.classList.add('bg-emerald-100', 'border-emerald-400');
        }
        
        // Animate panel opening
        if (window.anime) {
            anime({
                targets: '#agentWorkflowPanel',
                maxHeight: ['0px', '300px'],
                opacity: [0, 1],
                duration: 400,
                easing: 'easeOutCubic'
            });
        }
    } else {
        panel.classList.add('hidden');
        toggleText.textContent = 'Show Agent Workflow';
        if (toggleBtn) {
            toggleBtn.classList.remove('bg-emerald-100', 'border-emerald-400');
        }
    }
}

// Clear workflow panel
function clearWorkflowPanel() {
    const container = document.getElementById('agentFlowContainer');
    if (container) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-400 text-sm">
                <i class="fas fa-robot text-3xl mb-2 opacity-50"></i>
                <p>Agent workflow will appear here...</p>
            </div>
        `;
    }
    // Clear graph
    clearGraph();
}

// Add agent workflow step with beautiful animation
function addAgentStep(stepData) {
    const container = document.getElementById('agentFlowContainer');
    if (!container) return;
    
    // Remove placeholder if it exists
    const placeholder = container.querySelector('.text-center');
    if (placeholder) {
        placeholder.remove();
    }
    
    const stepDiv = document.createElement('div');
    stepDiv.className = 'workflow-step flex items-start gap-3 p-3 bg-white rounded-xl shadow-sm border-l-4 animate-fadeInUp';
    
    let icon, iconClass, borderColor, statusColor, statusBg, title;
    
    // Determine step styling based on type
    if (stepData.type === 'start') {
        icon = 'fa-play-circle';
        iconClass = 'text-blue-500 bg-blue-100';
        borderColor = 'border-blue-500';
        statusBg = 'bg-blue-100';
        statusColor = 'text-blue-700';
        title = 'Starting...';
    } else if (stepData.type === 'agent_active') {
        icon = 'fa-robot';
        iconClass = 'text-emerald-500 bg-emerald-100';
        borderColor = 'border-emerald-500';
        statusBg = 'bg-emerald-100';
        statusColor = 'text-emerald-700';
        title = stepData.agent ? formatAgentName(stepData.agent) : 'Agent Active';
    } else if (stepData.type === 'tool_call') {
        icon = 'fa-wrench';
        iconClass = 'text-purple-500 bg-purple-100';
        borderColor = 'border-purple-500';
        statusBg = 'bg-purple-100';
        statusColor = 'text-purple-700';
        title = stepData.tool ? `Tool: ${formatToolName(stepData.tool)}` : 'Tool Call';
    } else if (stepData.type === 'thinking') {
        icon = 'fa-brain';
        iconClass = 'text-amber-500 bg-amber-100';
        borderColor = 'border-amber-500';
        statusBg = 'bg-amber-100';
        statusColor = 'text-amber-700';
        title = 'Processing...';
    } else if (stepData.type === 'final_response') {
        icon = 'fa-check-circle';
        iconClass = 'text-green-500 bg-green-100';
        borderColor = 'border-green-500';
        statusBg = 'bg-green-100';
        statusColor = 'text-green-700';
        title = 'Complete';
    } else if (stepData.type === 'error') {
        icon = 'fa-exclamation-circle';
        iconClass = 'text-red-500 bg-red-100';
        borderColor = 'border-red-500';
        statusBg = 'bg-red-100';
        statusColor = 'text-red-700';
        title = 'Error';
    } else {
        icon = 'fa-circle';
        iconClass = 'text-gray-500 bg-gray-100';
        borderColor = 'border-gray-500';
        statusBg = 'bg-gray-100';
        statusColor = 'text-gray-700';
        title = 'Processing';
    }
    
    stepDiv.classList.add(borderColor);
    
    // Format timestamp
    const time = stepData.timestamp ? new Date(stepData.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }) : '';
    
    stepDiv.innerHTML = `
        <div class="flex-shrink-0">
            <div class="w-10 h-10 ${iconClass} rounded-lg flex items-center justify-center">
                <i class="fas ${icon} text-lg"></i>
            </div>
        </div>
        <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-bold text-navy-700">${title}</span>
                ${stepData.type === 'agent_active' || stepData.type === 'thinking' ? 
                    '<span class="status-dot bg-emerald-500"></span>' : ''}
            </div>
            <p class="text-xs text-gray-600">${stepData.status || ''}</p>
            ${time ? `<p class="text-xs text-gray-400 mt-1"><i class="fas fa-clock mr-1"></i>${time}</p>` : ''}
        </div>
    `;
    
    container.appendChild(stepDiv);
    
    // Auto-scroll to bottom
    container.scrollTop = container.scrollHeight;
    
    // Animate with anime.js if available
    if (window.anime) {
        anime({
            targets: stepDiv,
            scale: [0.95, 1],
            opacity: [0, 1],
            duration: 400,
            easing: 'easeOutElastic(1, 0.8)'
        });
    }
    
    // Also add to graph if graph view is active
    addGraphNode(stepData);
}

// Format agent name for display
function formatAgentName(agentName) {
    return agentName
        .replace(/_/g, ' ')
        .replace(/agent/gi, '')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
        .trim();
}

// Format tool name for display
function formatToolName(toolName) {
    return toolName
        .replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Ask AI function with streaming support
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
    
    // Clear previous workflow and automatically show panel if streaming enabled
    if (useStreaming) {
        clearWorkflowPanel();
        if (!workflowPanelVisible) {
            toggleWorkflowPanel();
        }
        
        // Use streaming version
        await askAIStream(question);
    } else {
        // Use original non-streaming version
        await askAINonStream(question);
    }
}

// Original non-streaming version (renamed)
async function askAINonStream(question) {
    const chatMessages = document.getElementById('chatMessages');

    // Show loading
    const loadingMsg = addMessage('Thinking...', 'bot');
    
    try {
        // Get stored location data for chat agent
        const storedLocationData = localStorage.getItem('currentLocationData');
        let locationContext = null;
        const storedPersonaType = sessionStorage.getItem('persona');
        
        if (storedLocationData) {
            try {
                locationContext = JSON.parse(storedLocationData);
                console.log('[Chat] Using stored location data:', locationContext);
            } catch (e) {
                console.warn('[Chat] Failed to parse stored location data:', e);
            }
        }

        
        // Try ADK agent first
        const response = await fetch('/api/agent-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                state: currentState,
                days: currentDays,
                location_context: locationContext,
                persona: storedPersonaType
            })
        });

        const data = await response.json();

        // Remove loading message
        loadingMsg.remove();

        if (data.success) {
            // Debug: Log response data
            console.log('[Chat Debug] Response data:', data);
            
            // Build context indicators
            let contextIndicators = '';
            
            // Add location context badge if available
            if (data.location) {
                contextIndicators += `<div class="text-xs text-emerald-600 font-medium mt-1 flex items-center">
                    <i class="fas fa-map-marker-alt mr-1"></i>
                    Location: ${data.location}
                </div>`;
            } else if (actualState || actualCity) {
                // Show location even if backend doesn't return it
                const locationParts = [actualCity, actualState];
                if (actualZip) {
                    locationParts.push(`(${actualZip})`);
                }
                const locationText = locationParts.filter(Boolean).join(', ');
                contextIndicators += `<div class="text-xs text-emerald-600 font-medium mt-1 flex items-center">
                    <i class="fas fa-map-marker-alt mr-1"></i>
                    Location: ${locationText}
                </div>`;
            }
            
            // Add time frame indicator if we have time frame data
            if (data.time_frame) {
                contextIndicators += `<div class="text-xs text-blue-600 font-medium mt-1 flex items-center">
                    <i class="fas fa-calendar-alt mr-1"></i>
                    Time Frame: ${data.time_frame.period || data.time_frame}
                </div>`;
            }
            
            // Add current time indicator
            const now = new Date();
            const currentTime = now.toLocaleString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            contextIndicators += `<div class="text-xs text-purple-600 font-medium mt-1 flex items-center">
                <i class="fas fa-clock mr-1"></i>
                Current Time: ${currentTime}
            </div>`;
            
            // Add agent badge if available
            const agentBadge = data.agent ? `<div class="text-xs text-gray-500 mt-1">via ${data.agent}</div>` : '';
            
            // Add location context indicator if location data is available
            let locationIndicator = '';
            if (locationContext) {
                const locationText = [locationContext.city, locationContext.state, locationContext.zipCode].filter(Boolean).join(', ');
                locationIndicator = `<div class="text-xs text-emerald-600 mt-1 flex items-center">
                    <i class="fas fa-map-marker-alt mr-1"></i>
                    Using location: ${locationText}
                </div>`;
            }
            
            addMessage(data.response + agentBadge + locationIndicator, 'bot');
            
            // If video generation started, begin polling
            if (data.task_id) {
                console.log('[VIDEO] Task ID received:', data.task_id);
                pollForVideoCompletion(data.task_id);
            }
        } else {
            console.error('[ERROR] Response success=false or missing:', data);
            addMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        loadingMsg.remove();
        console.error('[ERROR] Exception in askAI:', error);
        console.error('[ERROR] Error stack:', error.stack);
        addMessage('Sorry, I could not connect to the AI service.', 'bot');
        console.error('Error asking AI:', error);
    }
}

// Streaming version with workflow visualization
async function askAIStream(question) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Show loading message
    const loadingMsg = addMessage('Thinking...', 'bot');
    
    try {
        // Get stored location data for chat agent
        const storedLocationData = localStorage.getItem('currentLocationData');
        let locationContext = null;
        const storedPersonaType = sessionStorage.getItem('persona');
        
        if (storedLocationData) {
            try {
                locationContext = JSON.parse(storedLocationData);
                console.log('[Chat Stream] Using stored location data:', locationContext);
            } catch (e) {
                console.warn('[Chat Stream] Failed to parse stored location data:', e);
            }
        }
        
        // Make POST request and read streaming response
        const response = await fetch('/api/agent-chat-stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                state: currentState,
                days: currentDays,
                location_context: locationContext,
                persona: storedPersonaType
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finalResponse = '';
        
        while (true) {
            const { value, done } = await reader.read();
            
            if (done) {
                break;
            }
            
            // Decode the chunk and add to buffer
            buffer += decoder.decode(value, { stream: true });
            
            // Process complete lines (Server-Sent Events format)
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete line in buffer
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const eventData = JSON.parse(line.substring(6));
                        console.log('[Stream Event]', eventData);
                        
                        // Add to workflow visualization
                        addAgentStep(eventData);
                        
                        // If final response, save it
                        if (eventData.type === 'final_response') {
                            finalResponse = eventData.content || '';
                        }
                        
                        // If error, save error message
                        if (eventData.type === 'error') {
                            finalResponse = eventData.content || 'An error occurred';
                        }
                    } catch (e) {
                        console.error('[Stream] Error parsing event:', e);
                    }
                }
            }
        }
        
        // Remove loading message
        loadingMsg.remove();
        
        // Display final response
        if (finalResponse) {
            addMessage(finalResponse, 'bot');
            
            // Check if response contains video task_id
            const taskIdMatch = finalResponse.match(/task[_-]?id[:\s]+([a-zA-Z0-9_-]+)/i);
            if (taskIdMatch) {
                const taskId = taskIdMatch[1];
                console.log('[VIDEO] Task ID extracted from stream:', taskId);
                pollForVideoCompletion(taskId);
            }
        } else {
            addMessage('I received your question but couldn\'t generate a response. Please try again.', 'bot');
        }
        
    } catch (error) {
        loadingMsg.remove();
        console.error('[ERROR] Exception in askAIStream:', error);
        console.error('[ERROR] Error stack:', error.stack);
        
        // Add error to workflow
        addAgentStep({
            type: 'error',
            timestamp: new Date().toISOString(),
            status: 'Connection error',
            content: error.message
        });
        
        addMessage('Sorry, I could not connect to the AI service. Please try again.', 'bot');
    }
}

// Check if user message is Twitter approval
function isTwitterApproval(message) {
    const lowerMsg = message.toLowerCase().trim();
    const approvalPhrases = ['yes', 'yeah', 'sure', 'ok', 'okay', 'post it', 'post to twitter', 'tweet it', 'share it'];
    return approvalPhrases.some(phrase => lowerMsg === phrase || lowerMsg.includes(phrase));
}

// Post video to Twitter
const isPostingToTwitter = { value: false }; // Flag to prevent duplicate posts

async function postToTwitter(videoData) {
    const questionInput = document.getElementById('questionInput');
    
    // Prevent duplicate posting
    if (isPostingToTwitter.value) {
        console.log('[TWITTER] Already posting, ignoring duplicate call');
        return;
    }
    isPostingToTwitter.value = true;
    
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
            const successMessage = `Posted to Twitter successfully!\n\nView your post: ${result.tweet_url}\n\n${result.message}`;
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
    } finally {
        // Reset posting flag
        isPostingToTwitter.value = false;
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
    
    const maxAttempts = 48; // 48 * 5 sec = 4 minutes (Veo 3 can take 2-3 minutes)
    
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
                const videoMessage = `Your PSA video is ready!

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

// Clear chat history
function clearChat() {
    const chatMessages = document.getElementById('chatMessages');
    if (!chatMessages) return;
    
    // Stop any ongoing speech
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    
    // Clear all messages
    chatMessages.innerHTML = '';
    
    // Add welcome message back
    const welcomeDiv = document.createElement('div');
    welcomeDiv.className = 'flex items-start space-x-3';
    welcomeDiv.innerHTML = `
        <div class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
            <i class="fas fa-robot text-white"></i>
        </div>
        <div class="bg-white rounded-2xl rounded-tl-none p-4 shadow-md max-w-lg">
            <p class="text-gray-700">Hello! I'm your AI health advisor. Ask me anything about air quality, disease risks, or health recommendations for your community.</p>
        </div>
    `;
    chatMessages.appendChild(welcomeDiv);
    
    console.log('[CHAT] Chat history cleared');
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
        
        // Speak the bot's response if speech is enabled
        if (speechEnabled) {
            speakText(text);
        }
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
    console.log('┌─────────────────────────────────────────────────────┐');
    console.log('│ [WEATHER] Starting loadWeatherData()               │');
    console.log('├─────────────────────────────────────────────────────┤');
    console.log('│ Location Variables:                                 │');
    console.log('│  - State:', currentState || '(empty)');
    console.log('│  - City:', currentCity || '(empty)');
    console.log('│  - ZIP:', currentZip || '(empty)');
    
    if (!currentZip && !currentCity) {
        console.log('│ ❌ STOPPING: No ZIP or City set                    │');
        console.log('└─────────────────────────────────────────────────────┘');
        return;
    }
    console.log('│ ✓ Location check passed                            │');
    console.log('└─────────────────────────────────────────────────────┘');
    
    console.log('[Weather] Loading data for ZIP:', currentZip, 'City:', currentCity, 'State:', currentState);
    
    try {
        const params = new URLSearchParams();
        if (currentZip) params.append('zipCode', currentZip);
        else if (currentCity && currentState) {
            params.append('city', currentCity);
            params.append('state', currentState);
        }
        
        // Add date range parameters
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (startDateInput && startDateInput.value) {
            params.append('start_date', startDateInput.value);
        }
        
        if (endDateInput && endDateInput.value) {
            params.append('end_date', endDateInput.value);
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
    
    // Load detailed pollutant charts
    if (typeof initializePollutantCharts === 'function') {
        console.log('');
        console.log('📊 [WEATHER] Calling initializePollutantCharts with:');
        console.log('   ZIP:', currentZip);
        console.log('   City:', currentCity);
        console.log('   State:', currentState);
        initializePollutantCharts(currentZip, currentCity, currentState);
    }
}

// Load pollen data
async function loadPollenData() {
    console.log('┌─────────────────────────────────────────────────────┐');
    console.log('│ [POLLEN] Starting loadPollenData()                 │');
    console.log('├─────────────────────────────────────────────────────┤');
    console.log('│ Location Variables:                                 │');
    console.log('│  - State:', currentState || '(empty)');
    console.log('│  - City:', currentCity || '(empty)');
    console.log('│  - ZIP:', currentZip || '(empty)');
    
    if (!currentZip && !currentCity) {
        console.log('│ ❌ STOPPING: No ZIP or City set                    │');
        console.log('└─────────────────────────────────────────────────────┘');
        return;
    }
    console.log('│ ✓ Location check passed                            │');
    console.log('└─────────────────────────────────────────────────────┘');
    
    console.log('[Pollen] Loading data for ZIP:', currentZip, 'City:', currentCity, 'State:', currentState);
    
    try {
        const params = new URLSearchParams();
        if (currentZip) params.append('zipCode', currentZip);
        else if (currentCity && currentState) {
            params.append('city', currentCity);
            params.append('state', currentState);
        }
        
        // Add date range parameters
        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');
        
        if (startDateInput && startDateInput.value) {
            params.append('start_date', startDateInput.value);
        }
        
        if (endDateInput && endDateInput.value) {
            params.append('end_date', endDateInput.value);
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
    
    // Store weather data for temperature unit conversion
    weatherData = weather;
    
    const current = weather.current;
    console.log('[Weather] Current data:', current);
    
    // Temperature - use conversion function
    updateTemperatureDisplay();
    
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
    
    // Update summary card
    const summaryTempEl = document.getElementById('summaryTemp');
    if (summaryTempEl) {
        summaryTempEl.textContent = `${temp}°`;
    }
    
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
    
    // Update summary card
    const summaryPollenEl = document.getElementById('summaryPollen');
    if (summaryPollenEl) {
        summaryPollenEl.textContent = upi;
    }
    
    
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

// Load additional summary cards (Fire, COVID, Alerts)
async function loadSummaryCards() {
    console.log('[Summary Cards] Loading additional data...');
    
    try {
        // Load wildfire data - uses 'count' field from API
        const fireUrl = currentState 
            ? `/api/wildfires?state=${encodeURIComponent(currentState)}`
            : `/api/wildfires`;
        
        console.log('[Summary Cards] Fetching wildfire data from:', fireUrl);
        const fireResponse = await fetch(fireUrl);
        const fireData = await fireResponse.json();
        console.log('[Summary Cards] Fire data received:', fireData);
        
        const summaryFireEl = document.getElementById('summaryFire');
        if (summaryFireEl) {
            // API returns 'count' field directly
            summaryFireEl.textContent = fireData.count || '0';
            console.log('[Summary Cards] Fire count:', fireData.count || '0');
        }
    } catch (error) {
        console.error('[Summary Cards] Error loading fire data:', error);
        const summaryFireEl = document.getElementById('summaryFire');
        if (summaryFireEl) summaryFireEl.textContent = '0';
    }
    
    try {
        // Load COVID data - use /api/covid which returns cases_per_100k
        const url = currentState 
            ? `/api/covid?state=${encodeURIComponent(currentState)}`
            : `/api/covid`;
        
        console.log('[Summary Cards] Fetching COVID data from:', url);
        const covidResponse = await fetch(url);
        const covidData = await covidResponse.json();
        console.log('[Summary Cards] COVID data received:', covidData);
        
        const summaryCovidEl = document.getElementById('summaryCovid');
        if (summaryCovidEl) {
            // API returns cases_per_100k directly
            if (covidData.cases_per_100k && covidData.cases_per_100k !== '-') {
                summaryCovidEl.textContent = covidData.cases_per_100k;
                console.log('[Summary Cards] COVID cases per 100K:', covidData.cases_per_100k);
            } else {
                summaryCovidEl.textContent = '-';
                console.log('[Summary Cards] No COVID data available');
            }
        }
    } catch (error) {
        console.error('[Summary Cards] Error loading COVID data:', error);
        const summaryCovidEl = document.getElementById('summaryCovid');
        if (summaryCovidEl) summaryCovidEl.textContent = '-';
    }
    
    try {
        // Load alerts data - uses 'count' field from API
        const alertsUrl = currentState 
            ? `/api/alerts?state=${encodeURIComponent(currentState)}`
            : `/api/alerts`;
        
        console.log('[Summary Cards] Fetching alerts data from:', alertsUrl);
        const alertsResponse = await fetch(alertsUrl);
        const alertsData = await alertsResponse.json();
        console.log('[Summary Cards] Alerts data received:', alertsData);
        
        const summaryAlertsEl = document.getElementById('summaryAlerts');
        if (summaryAlertsEl) {
            // API returns 'count' field directly
            summaryAlertsEl.textContent = alertsData.count || '0';
            console.log('[Summary Cards] Alerts count:', alertsData.count || '0');
        }
    } catch (error) {
        console.error('[Summary Cards] Error loading alerts data:', error);
        const summaryAlertsEl = document.getElementById('summaryAlerts');
        if (summaryAlertsEl) summaryAlertsEl.textContent = '0';
    }
    
    console.log('[Summary Cards] Data loading complete');
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

// Temperature unit conversion
let weatherData = null; // Store weather data for unit conversion
let currentTempUnit = 'F'; // Track current unit

function setTemperatureUnit(unit) {
    currentTempUnit = unit;
    
    // Update button styles
    const btnF = document.getElementById('tempUnitF');
    const btnC = document.getElementById('tempUnitC');
    
    if (unit === 'F') {
        btnF.className = 'px-3 py-1 rounded bg-white text-blue-600 font-semibold text-sm transition-all';
        btnC.className = 'px-3 py-1 rounded text-white font-semibold text-sm transition-all hover:bg-white/20';
    } else {
        btnC.className = 'px-3 py-1 rounded bg-white text-blue-600 font-semibold text-sm transition-all';
        btnF.className = 'px-3 py-1 rounded text-white font-semibold text-sm transition-all hover:bg-white/20';
    }
    
    // Update temperature display
    updateTemperatureDisplay();
}

function updateTemperatureDisplay() {
    if (!weatherData || !weatherData.current) return;
    
    const current = weatherData.current;
    let temp = current.temperature || 0;
    let feelsLike = current.feels_like || 0;
    
    // Convert if needed
    if (currentTempUnit === 'C' && current.temperature_unit === 'F') {
        temp = (temp - 32) * 5/9;
        feelsLike = (feelsLike - 32) * 5/9;
    } else if (currentTempUnit === 'F' && current.temperature_unit === 'C') {
        temp = (temp * 9/5) + 32;
        feelsLike = (feelsLike * 9/5) + 32;
    }
    
    document.getElementById('temperature').textContent = `${Math.round(temp)}°${currentTempUnit}`;
    document.getElementById('feelsLike').textContent = `Feels like ${Math.round(feelsLike)}°${currentTempUnit}`;
}
