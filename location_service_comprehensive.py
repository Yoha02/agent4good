"""
Comprehensive US Location Service using zipcodes library
Provides access to ALL US states, cities, counties, and ZIP codes
Simple, lightweight, no complex dependencies - uses 43,000+ actual US ZIP codes
"""

import zipcodes
from typing import Dict, List, Optional

class ComprehensiveLocationService:
    """
    Service for accessing complete US location data
    Uses zipcodes library which has all 43,000+ US ZIP codes
    """
    
    def __init__(self):
        # US State mapping (all 50 states + DC)
        self.states = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
            'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
            'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
            'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
            'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
            'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
            'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
            'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
            'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
            'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
        }
        
        print("[OK] Comprehensive Location Service initialized (43,000+ US ZIP codes, all cities & counties)")
    
    def get_all_states(self) -> List[Dict]:
        """Get all US states"""
        states = []
        for code, name in sorted(self.states.items(), key=lambda x: x[1]):
            states.append({
                'code': code,
                'name': name
            })
        return states
    
    def get_state_code_from_name(self, state_name: str) -> Optional[str]:
        """Convert state name to state code"""
        if not state_name:
            return None
        
        state_name_lower = state_name.strip().lower()
        
        # Check if it's already a code
        if len(state_name) == 2:
            code = state_name.upper()
            if code in self.states:
                return code
        
        # Search for matching state name
        for code, name in self.states.items():
            if name.lower() == state_name_lower:
                return code
        
        return None
    
    def get_cities_by_state(self, state_code: str) -> List[Dict]:
        """Get all cities in a state from ZIP code database"""
        if state_code not in self.states:
            return []
        
        # Get all ZIP codes for this state
        all_zips = zipcodes.filter_by(state=state_code)
        
        # Extract unique cities with their data
        cities_dict = {}
        
        for zip_data in all_zips:
            city_name = zip_data.get('city')
            county = zip_data.get('county')
            
            if city_name:
                if city_name not in cities_dict:
                    cities_dict[city_name] = {
                        'name': city_name,
                        'state_code': state_code,
                        'state_name': self.states[state_code],
                        'county': county,
                        'zipcodes_count': 0
                    }
                cities_dict[city_name]['zipcodes_count'] += 1
        
        # Convert to sorted list
        cities = sorted(cities_dict.values(), key=lambda x: x['name'])
        
        print(f"[INFO] Found {len(cities)} cities in {state_code}")
        return cities
    
    def get_counties_by_state(self, state_code: str) -> List[Dict]:
        """Get all counties in a state"""
        if state_code not in self.states:
            return []
        
        all_zips = zipcodes.filter_by(state=state_code)
        
        # Extract unique counties
        counties_set = set()
        for zip_data in all_zips:
            county = zip_data.get('county')
            if county:
                counties_set.add(county)
        
        counties = []
        for county_name in sorted(counties_set):
            counties.append({
                'name': county_name,
                'state_code': state_code,
                'state_name': self.states[state_code]
            })
        
        return counties
    
    def get_counties_by_city(self, state_code: str, city_name: str) -> List[Dict]:
        """Get counties for a specific city"""
        if state_code not in self.states:
            return []
        
        all_zips = zipcodes.filter_by(city=city_name, state=state_code)
        
        counties_set = set()
        for zip_data in all_zips:
            county = zip_data.get('county')
            if county:
                counties_set.add(county)
        
        counties = []
        for county_name in sorted(counties_set):
            counties.append({
                'name': county_name,
                'city': city_name,
                'state_code': state_code,
                'state_name': self.states[state_code]
            })
        
        return counties
    
    def get_zipcodes_by_location(self, state_code: str, city_name: str = None, county_name: str = None) -> List[Dict]:
        """Get ZIP codes by location (state, city, or county)"""
        if state_code not in self.states:
            return []
        
        zipcodes_list = []
        
        if city_name:
            # Get ZIP codes for specific city
            results = zipcodes.filter_by(city=city_name, state=state_code)
        elif county_name:
            # Get ZIP codes for specific county
            all_state_zips = zipcodes.filter_by(state=state_code)
            results = [z for z in all_state_zips if z.get('county') == county_name]
        else:
            # Get all ZIP codes for state (limit to first 100 for performance)
            results = zipcodes.filter_by(state=state_code)[:100]
        
        for zip_data in results:
            zip_code = zip_data.get('zip_code')
            if zip_code:
                zipcodes_list.append({
                    'zipcode': zip_code,
                    'city': zip_data.get('city', city_name),
                    'county': zip_data.get('county'),
                    'state_code': state_code,
                    'state_name': self.states[state_code],
                    'lat': zip_data.get('lat'),
                    'lng': zip_data.get('long')
                })
        
        print(f"[INFO] Found {len(zipcodes_list)} ZIP codes for {city_name or county_name or state_code}")
        return sorted(zipcodes_list, key=lambda x: x['zipcode'])
    
    def get_location_info(self, zipcode: str = None, state_code: str = None, 
                         city_name: str = None, county_name: str = None) -> Optional[Dict]:
        """Get complete location information"""
        
        if zipcode:
            # Look up by ZIP code
            results = zipcodes.matching(zipcode)
            if results:
                result = results[0]
                return {
                    'zipcode': result.get('zip_code'),
                    'city': result.get('city'),
                    'county': result.get('county'),
                    'state_code': result.get('state'),
                    'state_name': self.states.get(result.get('state'), result.get('state')),
                    'lat': result.get('lat'),
                    'lng': result.get('long'),
                    'zipcodes': [result.get('zip_code')]
                }
        
        elif state_code and city_name:
            # Get first ZIP code for city
            results = zipcodes.filter_by(city=city_name, state=state_code)
            if results:
                result = results[0]
                all_zips = [z.get('zip_code') for z in results if z.get('zip_code')]
                return {
                    'city': city_name,
                    'county': result.get('county'),
                    'state_code': state_code,
                    'state_name': self.states.get(state_code, state_code),
                    'lat': result.get('lat'),
                    'lng': result.get('long'),
                    'zipcodes': all_zips[:10]  # Limit to first 10
                }
        
        elif state_code:
            # Get first ZIP code for state
            results = zipcodes.filter_by(state=state_code)
            if results:
                result = results[0]
                return {
                    'state_code': state_code,
                    'state_name': self.states.get(state_code, state_code),
                    'city': result.get('city'),
                    'county': result.get('county'),
                    'lat': result.get('lat'),
                    'lng': result.get('long'),
                    'zipcodes': [result.get('zip_code')]
                }
        
        return None
    
    def search_zipcodes(self, query: str, state_code: str = None, limit: int = 20) -> List[Dict]:
        """Search for ZIP codes by city name or ZIP code"""
        results = []
        
        # Check if query is a ZIP code (5 digits)
        if query.isdigit() and len(query) == 5:
            zip_results = zipcodes.matching(query)
            for result in zip_results:
                results.append({
                    'zipcode': result.get('zip_code'),
                    'city': result.get('city'),
                    'county': result.get('county'),
                    'state_code': result.get('state'),
                    'state_name': self.states.get(result.get('state'), result.get('state'))
                })
        else:
            # Search by city name
            if state_code:
                search_results = zipcodes.filter_by(city=query, state=state_code)
            else:
                search_results = zipcodes.filter_by(city=query)
            
            for zip_data in search_results[:limit]:
                if zip_data.get('zip_code'):
                    results.append({
                        'zipcode': zip_data.get('zip_code'),
                        'city': zip_data.get('city'),
                        'county': zip_data.get('county'),
                        'state_code': zip_data.get('state'),
                        'state_name': self.states.get(zip_data.get('state'), zip_data.get('state'))
                    })
        
        return results

    def get_zipcode_info(self, zipcode: str) -> Optional[Dict]:
        """
        Get detailed information for a specific ZIP code including coordinates
        """
        results = zipcodes.matching(zipcode)
        
        if results and len(results) > 0:
            result = results[0]
            return {
                'zipcode': result.get('zip_code'),
                'city': result.get('city'),
                'county': result.get('county'),
                'state_code': result.get('state'),
                'state_name': self.states.get(result.get('state'), result.get('state')),
                'latitude': float(result.get('lat', 0)),
                'longitude': float(result.get('long', 0))
            }
        
        return None
    
    def get_coordinates_for_city(self, city: str, state: str) -> Optional[Dict]:
        """
        Get coordinates for a city/state combination
        Returns the first ZIP code's coordinates for that city
        """
        # Convert state name to code if needed
        state_code = state
        if len(state) > 2:
            # It's a state name, convert to code
            state_code = next((code for code, name in self.states.items() if name == state), None)
            if not state_code:
                print(f"[WARNING] Could not find state code for: {state}")
                return None
        
        # zipcodes library stores city names in title case (e.g., "San Jose")
        # Try exact match first, then title case
        results = zipcodes.filter_by(city=city, state=state_code)
        
        if not results:
            # Try with title case
            city_title = city.title()
            results = zipcodes.filter_by(city=city_title, state=state_code)
        
        if results and len(results) > 0:
            result = results[0]  # Use first ZIP for this city
            print(f"[SUCCESS] Found coordinates for {city}, {state_code}: {result.get('lat')}, {result.get('long')}")
            return {
                'zipcode': result.get('zip_code'),
                'city': result.get('city'),
                'county': result.get('county'),
                'state_code': result.get('state'),
                'state_name': self.states.get(result.get('state'), result.get('state')),
                'latitude': float(result.get('lat', 0)),
                'longitude': float(result.get('long', 0))
            }
        
        print(f"[WARNING] No coordinates found for {city}, {state_code}")
        return None
