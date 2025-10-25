import os
import requests
from typing import Dict, Optional, List
import time
from datetime import datetime

class GooglePollenService:
    """
    Service for Google Pollen API integration
    https://developers.google.com/maps/documentation/pollen
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
        self.base_url = "https://pollen.googleapis.com/v1"
        self.timeout = 10
        
        # Rate limiting & caching
        self.last_request_time = 0
        self.min_request_interval = 1.0
        self.cache = {}
        self.cache_duration = 3600  # 1 hour for pollen (updates less frequently)
        
        if not self.api_key:
            raise ValueError("Google API key is required for Pollen API")
        else:
            # Show first/last 4 chars of API key for verification
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
            print(f"[OK] Google Pollen Service initialized with API key: {masked_key}")
    
    def _make_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """Make HTTP request with caching and rate limiting"""
        cache_key = f"{endpoint}_{str(params)}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                print(f"[CACHE HIT] Pollen data")
                return cached_data
        
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        params['key'] = self.api_key
        
        try:
            self.last_request_time = time.time()
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                self.cache[cache_key] = (data, time.time())
                return data
            elif response.status_code == 404:
                print(f"[INFO] No pollen data available for location")
                return None
            else:
                print(f"[ERROR] Pollen API Status {response.status_code}")
                return None
        except Exception as e:
            print(f"[ERROR] Pollen API request failed: {e}")
            return None
    
    def get_pollen_forecast(self, lat: float, lon: float, days: int = 5) -> Optional[List[Dict]]:
        """
        Get pollen forecast for location
        
        Returns:
            List of daily pollen forecasts with UPI (Universal Pollen Index) 0-5 scale
        """
        endpoint = f"{self.base_url}/forecast:lookup"
        params = {
            'location.latitude': lat,
            'location.longitude': lon,
            'days': min(days, 5),  # Max 5 days
            'languageCode': 'en'
        }
        
        data = self._make_request(endpoint, params)
        
        if not data:
            return None
        
        # Parse pollen data
        try:
            forecasts = []
            for day_info in data.get('dailyInfo', []):
                date_obj = day_info.get('date', {})
                date_str = f"{date_obj.get('year')}-{date_obj.get('month'):02d}-{date_obj.get('day'):02d}"
                
                pollen_types = day_info.get('pollenTypeInfo', [])
                plant_info = day_info.get('plantInfo', [])
                
                # Extract main allergens
                tree_index = 0
                grass_index = 0
                weed_index = 0
                
                for pollen in pollen_types:
                    code = pollen.get('code', '')
                    index_info = pollen.get('indexInfo', {})
                    value = index_info.get('value', 0)
                    
                    if code == 'TREE':
                        tree_index = value
                    elif code == 'GRASS':
                        grass_index = value
                    elif code == 'WEED':
                        weed_index = value
                
                # Get overall UPI
                upi = max(tree_index, grass_index, weed_index)
                
                # Get plant descriptions
                plants = [plant.get('displayName', '') for plant in plant_info[:3]]  # Top 3
                
                forecasts.append({
                    'date': date_str,
                    'upi': upi,  # Universal Pollen Index (0-5)
                    'level': self._get_pollen_level(upi),
                    'tree_index': tree_index,
                    'grass_index': grass_index,
                    'weed_index': weed_index,
                    'primary_plants': plants,
                    'health_recommendations': self._get_health_recommendations(upi)
                })
            
            return forecasts
        except Exception as e:
            print(f"[ERROR] Failed to parse pollen data: {e}")
            return None
    
    def _get_pollen_level(self, upi: int) -> str:
        """Convert UPI to level description"""
        if upi == 0:
            return 'None'
        elif upi == 1:
            return 'Low'
        elif upi == 2:
            return 'Moderate'
        elif upi == 3:
            return 'High'
        elif upi == 4:
            return 'Very High'
        else:
            return 'Extreme'
    
    def _get_health_recommendations(self, upi: int) -> str:
        """Get health recommendations based on UPI"""
        if upi <= 1:
            return "Pollen levels are low. Safe for outdoor activities."
        elif upi == 2:
            return "Moderate pollen levels. Most people can enjoy outdoor activities."
        elif upi == 3:
            return "High pollen levels. Sensitive individuals should limit outdoor exposure."
        elif upi == 4:
            return "Very high pollen levels. Allergy sufferers should stay indoors when possible."
        else:
            return "Extreme pollen levels. Avoid outdoor activities if you have allergies."
    
    def get_current_pollen(self, lat: float, lon: float) -> Optional[Dict]:
        """Get current day pollen data"""
        forecast = self.get_pollen_forecast(lat, lon, days=1)
        return forecast[0] if forecast else None
