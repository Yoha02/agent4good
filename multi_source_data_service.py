"""
Multi-Source Data Ingestion Service
Fetches data from RSS/XML/GeoJSON sources and prepares for BigQuery
"""

import feedparser
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
from google.cloud import bigquery
import hashlib
import re

class MultiSourceDataService:
    def __init__(self, project_id: str, dataset_id: str = 'health_environmental_data'):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = bigquery.Client(project=project_id)
        
        # Data sources configuration
        self.sources = {
            1: {
                'name': 'InciWeb Wildfire Incidents',
                'url': 'https://inciweb.wildfire.gov/incidents/rss.xml',
                'type': 'rss',
                'category': 'wildfire',
                'parser': self.parse_wildfire_rss
            },
            2: {
                'name': 'USGS Earthquakes',
                'url': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.atom',
                'type': 'atom',
                'category': 'earthquake',
                'parser': self.parse_earthquake_atom
            },
            3: {
                'name': 'NOAA Storm Prediction',
                'url': 'https://www.spc.noaa.gov/products/spcrss.xml',
                'type': 'rss',
                'category': 'severe_weather',
                'parser': self.parse_noaa_rss
            },
            4: {
                'name': 'NY State Health Data',
                'url': 'https://health.data.ny.gov/api/views/jvfi-ffup/rows.xml?accessType=DOWNLOAD',
                'type': 'xml',
                'category': 'health',
                'parser': self.parse_ny_health_xml
            },
            5: {
                'name': 'CDC COVID-19 Data',
                'url': 'https://data.cdc.gov/api/views/gvsb-yw6g/rows.xml?accessType=DOWNLOAD',
                'type': 'xml',
                'category': 'health',
                'parser': self.parse_cdc_covid_xml
            },
            6: {
                'name': 'US Drug Availability',
                'url': 'https://healthdata.gov/resource/879u-23sm.geojson',
                'type': 'geojson',
                'category': 'health',
                'parser': self.parse_drug_geojson
            },
            7: {
                'name': 'Colorado Respiratory Infections',
                'url': 'https://services3.arcgis.com/66aUo8zsujfVXRIT/arcgis/rest/services/CDPHE_Viral_Respiratory_Emerging_Infections_/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson',
                'type': 'geojson',
                'category': 'health',
                'parser': self.parse_colorado_respiratory_geojson
            }
        }
    
    def fetch_all_sources(self):
        """Fetch and process all data sources"""
        all_items = []
        
        for source_id, source in self.sources.items():
            print(f"[FETCH] Processing {source['name']}...")
            try:
                items = source['parser'](source_id, source['url'])
                all_items.extend(items)
                print(f"[SUCCESS] Got {len(items)} items from {source['name']}")
            except Exception as e:
                print(f"[ERROR] Failed to fetch {source['name']}: {e}")
        
        return all_items
    
    # ===========================================
    # WILDFIRE RSS PARSER
    # ===========================================
    def parse_wildfire_rss(self, source_id: int, url: str) -> List[Dict]:
        """Parse InciWeb wildfire RSS feed"""
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries:
            # Extract location from title or description
            location_data = self.extract_location_from_text(
                f"{entry.title} {entry.get('summary', '')}"
            )
            
            item = {
                'item_id': self.generate_id(entry.get('id', entry.link)),
                'source_id': source_id,
                'title': entry.title,
                'description': entry.get('summary', ''),
                'link': entry.link,
                'published_date': self.parse_date(entry.get('published')),
                'category': 'alert',
                'severity': self.detect_wildfire_severity(entry),
                'event_type': 'wildfire',
                'location_name': location_data.get('location'),
                'state_code': location_data.get('state'),
                'alert_level': self.detect_alert_level(entry),
                'metadata_json': json.dumps(dict(entry)),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            # Try to geocode
            if item['location_name']:
                coords = self.geocode_location(item['location_name'], item['state_code'])
                item['latitude'] = coords.get('lat')
                item['longitude'] = coords.get('lon')
            
            items.append(item)
        
        return items
    
    # ===========================================
    # EARTHQUAKE ATOM PARSER
    # ===========================================
    def parse_earthquake_atom(self, source_id: int, url: str) -> List[Dict]:
        """Parse USGS earthquake Atom feed"""
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries:
            # USGS provides coordinates directly
            if hasattr(entry, 'geo_lat') and hasattr(entry, 'geo_long'):
                lat = float(entry.geo_lat)
                lon = float(entry.geo_long)
            else:
                lat, lon = None, None
            
            # Extract magnitude from title (e.g., "M 4.5 - 10km NE of...")
            magnitude = self.extract_magnitude(entry.title)
            
            item = {
                'item_id': self.generate_id(entry.get('id', entry.link)),
                'source_id': source_id,
                'title': entry.title,
                'description': entry.get('summary', ''),
                'link': entry.link,
                'published_date': self.parse_date(entry.get('published')),
                'category': 'alert' if magnitude and magnitude >= 4.0 else 'info',
                'severity': self.earthquake_severity(magnitude),
                'event_type': 'earthquake',
                'magnitude': magnitude,
                'latitude': lat,
                'longitude': lon,
                'location_name': self.extract_earthquake_location(entry.title),
                'alert_level': self.earthquake_alert_level(magnitude),
                'metadata_json': json.dumps(dict(entry)),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            items.append(item)
        
        return items
    
    # ===========================================
    # NOAA STORM RSS PARSER
    # ===========================================
    def parse_noaa_rss(self, source_id: int, url: str) -> List[Dict]:
        """Parse NOAA Storm Prediction Center RSS"""
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries:
            location_data = self.extract_location_from_text(
                f"{entry.title} {entry.get('summary', '')}"
            )
            
            item = {
                'item_id': self.generate_id(entry.get('id', entry.link)),
                'source_id': source_id,
                'title': entry.title,
                'description': entry.get('summary', ''),
                'link': entry.link,
                'published_date': self.parse_date(entry.get('published')),
                'category': 'alert',
                'severity': self.detect_storm_severity(entry.title),
                'event_type': 'severe_weather',
                'location_name': location_data.get('location'),
                'state_code': location_data.get('state'),
                'alert_level': self.detect_alert_level(entry),
                'metadata_json': json.dumps(dict(entry)),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            items.append(item)
        
        return items
    
    # ===========================================
    # NY HEALTH XML PARSER
    # ===========================================
    def parse_ny_health_xml(self, source_id: int, url: str) -> List[Dict]:
        """Parse NY State health data XML"""
        response = requests.get(url, timeout=30)
        root = ET.fromstring(response.content)
        items = []
        
        # Parse Socrata XML format
        for row in root.findall('.//{http://www.socrata.com/api/}row'):
            item_data = {}
            for child in row:
                tag = child.tag.split('}')[1] if '}' in child.tag else child.tag
                item_data[tag] = child.text
            
            item = {
                'item_id': self.generate_id(f"ny_health_{item_data.get('_id', '')}"),
                'source_id': source_id,
                'event_type': 'health_metric',
                'state_code': 'NY',
                'health_metric': item_data.get('indicator_name'),
                'health_value': self.safe_float(item_data.get('value')),
                'health_unit': item_data.get('unit'),
                'location_name': item_data.get('county'),
                'published_date': self.parse_date(item_data.get('date')),
                'metadata_json': json.dumps(item_data),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            items.append(item)
        
        return items
    
    # ===========================================
    # CDC COVID XML PARSER
    # ===========================================
    def parse_cdc_covid_xml(self, source_id: int, url: str) -> List[Dict]:
        """Parse CDC COVID-19 data XML"""
        response = requests.get(url, timeout=30)
        root = ET.fromstring(response.content)
        items = []
        
        for row in root.findall('.//{http://www.socrata.com/api/}row'):
            item_data = {}
            for child in row:
                tag = child.tag.split('}')[1] if '}' in child.tag else child.tag
                item_data[tag] = child.text
            
            item = {
                'item_id': self.generate_id(f"cdc_covid_{item_data.get('_id', '')}"),
                'source_id': source_id,
                'event_type': 'covid_metric',
                'state_code': item_data.get('state'),
                'health_metric': 'covid_positivity',
                'health_value': self.safe_float(item_data.get('percent_positivity')),
                'health_unit': 'percent',
                'published_date': self.parse_date(item_data.get('week_ending_date')),
                'metadata_json': json.dumps(item_data),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            items.append(item)
        
        return items
    
    # ===========================================
    # DRUG AVAILABILITY GEOJSON PARSER
    # ===========================================
    def parse_drug_geojson(self, source_id: int, url: str) -> List[Dict]:
        """Parse drug availability GeoJSON"""
        response = requests.get(url, timeout=30)
        geojson_data = response.json()
        items = []
        
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [])
            
            item = {
                'item_id': self.generate_id(f"drug_{props.get('id', '')}"),
                'source_id': source_id,
                'event_type': 'drug_availability',
                'drug_name': props.get('drug_name'),
                'availability_status': props.get('status'),
                'facility_name': props.get('facility'),
                'latitude': coords[1] if len(coords) >= 2 else None,
                'longitude': coords[0] if len(coords) >= 2 else None,
                'state_code': props.get('state'),
                'location_name': props.get('city'),
                'metadata_json': json.dumps(props),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            items.append(item)
        
        return items
    
    # ===========================================
    # COLORADO RESPIRATORY GEOJSON PARSER
    # ===========================================
    def parse_colorado_respiratory_geojson(self, source_id: int, url: str) -> List[Dict]:
        """Parse Colorado respiratory infections GeoJSON"""
        response = requests.get(url, timeout=30)
        geojson_data = response.json()
        items = []
        
        for feature in geojson_data.get('features', []):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [])
            
            item = {
                'item_id': self.generate_id(f"co_respiratory_{props.get('OBJECTID', '')}"),
                'source_id': source_id,
                'event_type': 'respiratory_infection',
                'state_code': 'CO',
                'health_metric': props.get('Disease') or 'respiratory_illness',
                'health_value': self.safe_float(props.get('CaseCount')),
                'facility_name': props.get('Facility'),
                'latitude': coords[1] if len(coords) >= 2 else None,
                'longitude': coords[0] if len(coords) >= 2 else None,
                'published_date': self.parse_date(props.get('ReportDate')),
                'metadata_json': json.dumps(props),
                'is_active': True,
                'created_at': datetime.now().isoformat()
            }
            
            items.append(item)
        
        return items
    
    # ===========================================
    # HELPER METHODS
    # ===========================================
    
    def generate_id(self, seed: str) -> str:
        """Generate unique ID from seed"""
        return hashlib.md5(seed.encode()).hexdigest()
    
    def parse_date(self, date_str: str) -> str:
        """Parse various date formats to ISO"""
        if not date_str:
            return datetime.now().isoformat()
        # Add parsing logic for different date formats
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
        except:
            return datetime.now().isoformat()
    
    def extract_location_from_text(self, text: str) -> Dict[str, str]:
        """Extract location and state from text"""
        # Regex patterns for location extraction
        state_pattern = r'\b([A-Z]{2})\b'
        location_pattern = r'in ([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        
        state_match = re.search(state_pattern, text)
        location_match = re.search(location_pattern, text)
        
        return {
            'state': state_match.group(1) if state_match else None,
            'location': location_match.group(1) if location_match else None
        }
    
    def geocode_location(self, location: str, state: str = None) -> Dict[str, float]:
        """Geocode location using Google or other service"""
        # Implement geocoding logic
        return {'lat': None, 'lon': None}
    
    def safe_float(self, value: Any) -> float:
        """Safely convert to float"""
        try:
            return float(value) if value else None
        except:
            return None
    
    def extract_magnitude(self, title: str) -> float:
        """Extract earthquake magnitude from title"""
        match = re.search(r'M\s*([\d.]+)', title)
        return float(match.group(1)) if match else None
    
    def earthquake_severity(self, magnitude: float) -> str:
        """Determine earthquake severity"""
        if not magnitude:
            return 'info'
        if magnitude >= 7.0:
            return 'critical'
        elif magnitude >= 5.0:
            return 'high'
        elif magnitude >= 3.0:
            return 'moderate'
        return 'low'
    
    def earthquake_alert_level(self, magnitude: float) -> str:
        """Earthquake alert level color"""
        if not magnitude:
            return 'green'
        if magnitude >= 7.0:
            return 'red'
        elif magnitude >= 5.0:
            return 'orange'
        elif magnitude >= 3.0:
            return 'yellow'
        return 'green'
    
    def detect_wildfire_severity(self, entry) -> str:
        """Detect wildfire severity from entry data"""
        text = f"{entry.title} {entry.get('summary', '')}".lower()
        if any(word in text for word in ['evacuation', 'critical', 'extreme']):
            return 'critical'
        elif any(word in text for word in ['warning', 'large', 'growing']):
            return 'high'
        return 'moderate'
    
    def detect_storm_severity(self, title: str) -> str:
        """Detect storm severity from title"""
        title_lower = title.lower()
        if any(word in title_lower for word in ['tornado', 'severe', 'warning']):
            return 'high'
        elif 'watch' in title_lower:
            return 'moderate'
        return 'low'
    
    def detect_alert_level(self, entry) -> str:
        """Detect alert level color"""
        text = f"{entry.title} {entry.get('summary', '')}".lower()
        if any(word in text for word in ['critical', 'extreme', 'emergency']):
            return 'red'
        elif any(word in text for word in ['warning', 'severe']):
            return 'orange'
        elif 'watch' in text:
            return 'yellow'
        return 'green'
    
    def extract_earthquake_location(self, title: str) -> str:
        """Extract location from earthquake title"""
        # Example: "M 4.5 - 10km NE of Los Angeles, CA"
        match = re.search(r'of (.+)$', title)
        return match.group(1) if match else None
    
    # ===========================================
    # BIGQUERY UPLOAD
    # ===========================================
    
    def upload_to_bigquery(self, items: List[Dict]):
        """Upload items to BigQuery"""
        if not items:
            print("[BIGQUERY] No items to upload")
            return
        
        table_id = f"{self.project_id}.{self.dataset_id}.data_items"
        
        # Convert to DataFrame
        df = pd.DataFrame(items)
        
        # Upload to BigQuery
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[
                bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION
            ]
        )
        
        job = self.client.load_table_from_dataframe(
            df, table_id, job_config=job_config
        )
        
        job.result()  # Wait for completion
        print(f"[BIGQUERY] Uploaded {len(items)} items to {table_id}")

# Example usage
if __name__ == "__main__":
    service = MultiSourceDataService(
        project_id="your-project-id"
    )
    
    # Fetch all data
    items = service.fetch_all_sources()
    
    # Upload to BigQuery
    service.upload_to_bigquery(items)
