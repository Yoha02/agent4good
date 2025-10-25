"""
EPA AQS API Service
Uses the EPA Air Quality System (AQS) API to fetch detailed pollutant data
API Documentation: https://aqs.epa.gov/aqsweb/documents/data_api.html
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json

class EPAAQSService:
    """
    Service for interacting with EPA Air Quality System (AQS) API
    Provides detailed pollutant-specific data for PM2.5, PM10, O3, CO, SO2, NO2
    """
    
    # EPA AQS Parameter Codes
    PARAMETERS = {
        'PM2.5': '88101',    # PM2.5 - Local Conditions
        'PM10': '81102',     # PM10 Total 0-10um STP
        'OZONE': '44201',    # Ozone
        'CO': '42101',       # Carbon monoxide
        'SO2': '42401',      # Sulfur dioxide
        'NO2': '42602'       # Nitrogen dioxide (NO2)
    }
    
    def __init__(self):
        # Use test credentials from EPA AQS API documentation
        # To get your own key, visit: https://aqs.epa.gov/data/api/signup?email=your_email@example.com
        self.api_key = os.getenv('AQS_API_KEY', 'test')  # Default to 'test' if not set
        self.base_url = "https://aqs.epa.gov/data/api"
        self.email = os.getenv('AQS_EMAIL', 'test@aqs.api')  # Default to test email
        self.timeout = 15
        
        # Rate limiting and caching
        self.last_request_time = 0
        self.min_request_interval = 2.0  # AQS API is slower, 2 seconds between requests
        self.cache = {}
        self.cache_duration = 600  # Cache for 10 minutes (AQS data updates less frequently)
        
        if not self.api_key:
            print("[WARNING] AQS_API_KEY not found in .env file")
        else:
            print(f"[OK] EPA AQS API initialized with key: {self.api_key[:8]}...")
    
    def _make_request(self, endpoint: str, params: dict, max_retries: int = 2) -> Optional[dict]:
        """Make HTTP request to EPA AQS API with caching and rate limiting"""
        # Create cache key
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if time.time() - cached_time < self.cache_duration:
                print(f"[AQS CACHE HIT] Using cached data")
                return cached_data
        
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"[AQS RATE LIMIT] Waiting {sleep_time:.2f}s...")
            time.sleep(sleep_time)
        
        # Add required params
        params['email'] = self.email
        params['key'] = self.api_key or 'test'
        
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(max_retries + 1):
            try:
                self.last_request_time = time.time()
                print(f"[AQS API] Requesting: {endpoint} with params: {params}")
                
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[AQS API] Response: {json.dumps(data, indent=2)[:500]}")  # Log first 500 chars
                    # AQS API returns data in specific format
                    if data.get('Header') and data['Header'][0].get('status') == 'Success':
                        result = data.get('Data', [])
                        self.cache[cache_key] = (result, time.time())
                        print(f"[AQS API] Success: {len(result)} records")
                        return result
                    else:
                        error_msg = data.get('Header', [{}])[0].get('status', 'Unknown error')
                        print(f"[AQS API] API returned error: {error_msg}")
                        print(f"[AQS API] Full header: {data.get('Header')}")
                        return []
                elif response.status_code == 429:
                    wait_time = 10 * (attempt + 1)
                    print(f"[AQS API] Rate limited - waiting {wait_time}s...")
                    if attempt < max_retries:
                        time.sleep(wait_time)
                else:
                    print(f"[AQS API] HTTP {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.Timeout:
                print(f"[AQS API] Timeout (attempt {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    time.sleep(3)
            except Exception as e:
                print(f"[AQS API] Error: {e}")
        
        return None
    
    def get_daily_data_by_box(self, param_code: str, min_lat: float, max_lat: float, 
                              min_lon: float, max_lon: float, start_date: str, end_date: str) -> List[Dict]:
        """
        Get daily summary data by geographic bounding box
        This is the most reliable way to get data for a location
        """
        params = {
            'param': param_code,
            'bdate': start_date.replace('-', ''),  # Format: YYYYMMDD
            'edate': end_date.replace('-', ''),
            'minlat': min_lat,
            'maxlat': max_lat,
            'minlon': min_lon,
            'maxlon': max_lon
        }
        
        return self._make_request('dailyData/byBox', params)
    
    def get_data_for_location(self, lat: float, lon: float, days: int = 7) -> Dict[str, List[Dict]]:
        """
        Get data for all pollutants for a location
        Uses a bounding box around the lat/lon
        """
        # Create bounding box (±0.5 degrees, approximately 55km radius)
        box_size = 0.5
        min_lat = lat - box_size
        max_lat = lat + box_size
        min_lon = lon - box_size
        max_lon = lon + box_size
        
        # Use May 2025 dates - most recent data available via AQS API
        # (Note: CSV downloads from AirNow may have more recent data, but API lags)
        end_date = datetime(2025, 5, 19)  # Last date confirmed in CSV
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"[AQS] Fetching data from {start_str} to {end_str} (most recent available via API)")
        
        results = {}
        
        # Fetch data for each parameter
        for param_name, param_code in self.PARAMETERS.items():
            print(f"[AQS] Fetching {param_name} (code: {param_code})...")
            data = self.get_daily_data_by_box(
                param_code, min_lat, max_lat, min_lon, max_lon, start_str, end_str
            )
            
            if data:
                results[param_name] = data
                print(f"[AQS] {param_name}: {len(data)} records")
            else:
                print(f"[AQS] {param_name}: No data available")
                results[param_name] = []
        
        return results
    
    def process_parameter_data(self, raw_data: List[Dict], param_name: str) -> Dict:
        """
        Process raw AQS data into format needed for charts
        Returns: {values: [], dates: [], current: float, min: float, max: float, avg: float}
        """
        if not raw_data:
            return {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0}
        
        # Sort by date
        sorted_data = sorted(raw_data, key=lambda x: x.get('date_local', ''))
        
        values = []
        dates = []
        
        for item in sorted_data:
            # AQS returns actual concentration values
            value = item.get('arithmetic_mean')  # or 'first_max_value'
            date = item.get('date_local')
            
            if value is not None and date:
                values.append(float(value))
                dates.append(date)
        
        if not values:
            return {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0}
        
        return {
            'values': values,
            'dates': dates,
            'current': values[-1] if values else 0,
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'unit': self._get_unit(param_name),
            'sample_count': len(values)
        }
    
    def _get_unit(self, param_name: str) -> str:
        """Get measurement unit for parameter"""
        units = {
            'PM2.5': 'μg/m³',
            'PM10': 'μg/m³',
            'OZONE': 'ppm',
            'CO': 'ppm',
            'SO2': 'ppb',
            'NO2': 'ppb'
        }
        return units.get(param_name, '')
    
    def test_connection(self, lat: float = 37.7749, lon: float = -122.4194) -> Dict:
        """Test AQS API connection (default: San Francisco)"""
        try:
            # Try to get 1 day of PM2.5 data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            data = self.get_daily_data_by_box(
                self.PARAMETERS['PM2.5'],
                lat - 0.1, lat + 0.1,
                lon - 0.1, lon + 0.1,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            return {
                'success': data is not None and len(data) > 0,
                'message': f'AQS API working - got {len(data) if data else 0} records',
                'sample_data': data[0] if data else None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'AQS API test failed: {str(e)}',
                'sample_data': None
            }
