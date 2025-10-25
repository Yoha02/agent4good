import os
import requests
from typing import Dict, Optional
import time

class GoogleWeatherService:
    """
    Service for Google Weather API integration
    https://developers.google.com/maps/documentation/weather
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.base_url = "https://weather.googleapis.com/v1"
        self.timeout = 10
        
        # Rate limiting & caching
        self.last_request_time = 0
        self.min_request_interval = 1.0
        self.cache = {}
        self.cache_duration = 600  # 10 minutes for weather
        
        if not self.api_key:
            print("[WARNING] No Google API key - Weather service will be limited")
        else:
            # Show first/last 4 chars of API key for verification
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
            print(f"[OK] Google Weather Service initialized with API key: {masked_key}")
    
    def _make_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make HTTP request with caching and rate limiting"""
        if not self.api_key:
            print("[WARNING] No API key configured - skipping weather request")
            return None
            
        cache_key = f"{endpoint}_{str(params)}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                print(f"[CACHE HIT] Weather data")
                return cached_data
        
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        # Add API key to params (not already included)
        if 'key' not in params:
            params['key'] = self.api_key
        
        try:
            self.last_request_time = time.time()
            url = f"{self.base_url}{endpoint}"
            print(f"[WEATHER API] Requesting: {url}")
            
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = (data, time.time())
                print(f"[SUCCESS] Google Weather API returned data")
                return data
            else:
                print(f"[ERROR] Weather API Status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"[ERROR] Weather API request failed: {e}")
            return None
    
    def get_current_weather(self, lat: float = None, lon: float = None, 
                           location: str = None) -> Optional[Dict]:
        """
        Get current weather conditions using Google Weather API
        https://developers.google.com/maps/documentation/weather/current-conditions
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dict with weather data (temperature, humidity, wind, UV, conditions)
        """
        if not lat or not lon:
            return None
        
        # Google Weather API endpoint (just the path, base_url is added by _make_request)
        endpoint = "/currentConditions:lookup"
        
        # Parameters for Google Weather API
        params = {
            'location.latitude': lat,
            'location.longitude': lon,
            'unitsSystem': 'IMPERIAL'  # Fahrenheit, mph, etc.
        }
        
        data = self._make_request(endpoint, params)
        
        if not data:
            return None
        
        # Parse Google Weather API response
        try:
            # Response structure: data is the root object with all fields directly
            # NOT nested under 'currentConditions'
            
            # Extract nested fields
            temperature = data.get('temperature', {})
            feels_like = data.get('feelsLikeTemperature', {})
            wind = data.get('wind', {})
            wind_direction = wind.get('direction', {})
            wind_speed = wind.get('speed', {})
            weather_condition = data.get('weatherCondition', {})
            description = weather_condition.get('description', {})
            visibility_obj = data.get('visibility', {})
            precipitation_obj = data.get('precipitation', {})
            
            return {
                'temperature': temperature.get('degrees', 0),
                'temperature_unit': 'F',  # Always Fahrenheit with IMPERIAL
                'feels_like': feels_like.get('degrees', 0),
                'humidity': data.get('relativeHumidity', 0),
                'uv_index': data.get('uvIndex', 0),
                'wind_speed': wind_speed.get('value', 0),
                'wind_speed_unit': 'mph',  # Always mph with IMPERIAL
                'wind_direction': wind_direction.get('cardinal', 'N'),
                'wind_degrees': wind_direction.get('degrees', 0),
                'conditions': description.get('text', 'Unknown'),
                'condition_type': weather_condition.get('type', 'unknown'),
                'icon': weather_condition.get('iconBaseUri', ''),
                'visibility': visibility_obj.get('distance', 0),
                'cloud_cover': data.get('cloudCover', 0),
                'precipitation': precipitation_obj.get('qpf', {}).get('quantity', 0),
                'timestamp': data.get('currentTime', ''),
                'source': 'Google Weather API'
            }
        except Exception as e:
            print(f"[ERROR] Failed to parse Google Weather data: {e}")
            return None
    
    def get_forecast(self, lat: float = None, lon: float = None,
                    location: str = None, days: int = 7) -> Optional[list]:
        """
        Get weather forecast - Google Weather API doesn't provide forecast yet
        This is a placeholder for future implementation
        """
        print("[INFO] Weather forecast not yet implemented for Google Weather API")
        return None

