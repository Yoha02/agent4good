"""
External Data Ingestion for Agent4Good
Fetches data from various RSS, XML, and GeoJSON feeds and inserts into BigQuery
"""

import os
import requests
import feedparser
import xmltodict
import json
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize BigQuery client
bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
DATASET = os.getenv('BIGQUERY_DATASET', 'CrowdsourceData')


class WildfireDataFetcher:
    """Fetch wildfire data from InciWeb RSS feed"""
    
    FEED_URL = "https://inciweb.wildfire.gov/incidents/rss.xml"
    TABLE_NAME = "wildfire_incidents"
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch and parse InciWeb RSS feed"""
        try:
            logger.info(f"Fetching wildfire data from {self.FEED_URL}")
            feed = feedparser.parse(self.FEED_URL)
            
            incidents = []
            for entry in feed.entries:
                # Use entry ID as unique identifier
                incident_id = entry.get('id', hashlib.md5(entry.link.encode()).hexdigest())
                
                # Parse summary for structured data
                summary = entry.get('summary', '')
                
                # Extract state from summary
                state = None
                if 'State:' in summary:
                    state_line = [line for line in summary.split('\n') if 'State:' in line]
                    if state_line:
                        state = state_line[0].split('State:')[1].strip()
                
                # Extract coordinates from summary
                latitude = None
                longitude = None
                if 'Latitude:' in summary and 'Longitude:' in summary:
                    try:
                        # Format: "Latitude: 42° 41 15  Longitude: 123° 54 55"
                        coord_line = [line for line in summary.split('\n') if 'Latitude:' in line]
                        if coord_line:
                            coords = coord_line[0].strip()
                            lat_part = coords.split('Latitude:')[1].split('Longitude:')[0].strip()
                            lon_part = coords.split('Longitude:')[1].strip()
                            
                            # Convert degrees/minutes/seconds to decimal
                            lat_parts = lat_part.replace('°', ' ').split()
                            lon_parts = lon_part.replace('°', ' ').split()
                            
                            if len(lat_parts) >= 1:
                                latitude = float(lat_parts[0])
                                if len(lat_parts) >= 2:
                                    latitude += float(lat_parts[1]) / 60
                                if len(lat_parts) >= 3:
                                    latitude += float(lat_parts[2]) / 3600
                            
                            if len(lon_parts) >= 1:
                                longitude = -float(lon_parts[0])  # Western hemisphere is negative
                                if len(lon_parts) >= 2:
                                    longitude -= float(lon_parts[1]) / 60
                                if len(lon_parts) >= 3:
                                    longitude -= float(lon_parts[2]) / 3600
                    except Exception as e:
                        logger.warning(f"Could not parse coordinates: {e}")
                
                # Extract location from title
                incident_name = entry.title
                location = incident_name
                
                # Parse published date
                published_dt = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    published_dt = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed),
                        tz=timezone.utc
                    ).isoformat()
                
                incident = {
                    'incident_id': incident_id,
                    'incident_name': incident_name,
                    'location': location,
                    'state': state,
                    'latitude': latitude,
                    'longitude': longitude,
                    'acres_burned': None,  # Would need to parse from description
                    'containment_percent': None,
                    'start_date': published_dt,
                    'updated_date': published_dt or datetime.now(timezone.utc).isoformat(),
                    'status': 'Active',
                    'cause': None,
                    'url': entry.link,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                incidents.append(incident)
            
            logger.info(f"Fetched {len(incidents)} wildfire incidents")
            return incidents
            
        except Exception as e:
            logger.error(f"Error fetching wildfire data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def insert_to_bigquery(self, incidents: List[Dict[str, Any]]):
        """Insert wildfire data into BigQuery"""
        if not incidents:
            logger.warning("No wildfire data to insert")
            return
        
        table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{self.TABLE_NAME}"
        
        try:
            errors = bq_client.insert_rows_json(table_id, incidents)
            if errors:
                logger.error(f"Errors inserting wildfire data: {errors}")
            else:
                logger.info(f"Successfully inserted {len(incidents)} wildfire incidents")
        except Exception as e:
            logger.error(f"Error inserting to BigQuery: {e}")


class EarthquakeDataFetcher:
    """Fetch earthquake data from USGS Atom feed"""
    
    # All earthquakes in past hour
    FEED_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.atom"
    TABLE_NAME = "earthquake_events"
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch and parse USGS Atom feed"""
        try:
            logger.info(f"Fetching earthquake data from {self.FEED_URL}")
            feed = feedparser.parse(self.FEED_URL)
            
            earthquakes = []
            for entry in feed.entries:
                # Parse entry data
                event_id = entry.get('id', hashlib.md5(entry.link.encode()).hexdigest())
                
                # Title format: "M 3.2 - 10km E of Example, CA"
                title = entry.get('title', '')
                magnitude = None
                location = title
                
                if ' - ' in title:
                    parts = title.split(' - ')
                    mag_part = parts[0].strip()
                    location = parts[1].strip() if len(parts) > 1 else title
                    
                    # Extract magnitude from "M 3.2"
                    if mag_part.startswith('M '):
                        try:
                            magnitude = float(mag_part.split('M ')[1])
                        except:
                            pass
                
                # Parse published date
                event_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    event_time = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed),
                        tz=timezone.utc
                    ).isoformat()
                
                # Try to parse coordinates from 'where' field
                latitude = None
                longitude = None
                depth_km = None
                
                if hasattr(entry, 'where') and 'coordinates' in entry.where:
                    # Format: (lon, lat) tuple
                    try:
                        coords = entry.where['coordinates']
                        if len(coords) >= 2:
                            longitude = float(coords[0])
                            latitude = float(coords[1])
                    except:
                        pass
                
                # Try georss_elev for depth
                if hasattr(entry, 'georss_elev'):
                    try:
                        depth_km = abs(float(entry.georss_elev)) / 1000.0  # Convert meters to km
                    except:
                        pass
                
                # Parse summary for additional details
                summary = entry.get('summary', '')
                
                earthquake = {
                    'event_id': event_id,
                    'magnitude': magnitude,
                    'magnitude_type': 'M',  # Default, could parse from summary
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude,
                    'depth_km': depth_km,
                    'event_time': event_time or datetime.now(timezone.utc).isoformat(),
                    'updated_time': event_time,
                    'significance': None,
                    'alert_level': None,
                    'tsunami_warning': False,
                    'felt_reports': None,
                    'url': entry.link,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                earthquakes.append(earthquake)
            
            logger.info(f"Fetched {len(earthquakes)} earthquake events")
            return earthquakes
            
        except Exception as e:
            logger.error(f"Error fetching earthquake data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def insert_to_bigquery(self, earthquakes: List[Dict[str, Any]]):
        """Insert earthquake data into BigQuery"""
        if not earthquakes:
            logger.warning("No earthquake data to insert")
            return
        
        table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{self.TABLE_NAME}"
        
        try:
            errors = bq_client.insert_rows_json(table_id, earthquakes)
            if errors:
                logger.error(f"Errors inserting earthquake data: {errors}")
            else:
                logger.info(f"Successfully inserted {len(earthquakes)} earthquake events")
        except Exception as e:
            logger.error(f"Error inserting to BigQuery: {e}")


class StormReportsFetcher:
    """Fetch severe weather reports from NOAA Storm Prediction Center RSS"""
    
    FEED_URL = "https://www.spc.noaa.gov/products/spcrss.xml"
    TABLE_NAME = "storm_reports"
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch and parse NOAA SPC RSS feed"""
        try:
            logger.info(f"Fetching storm reports from {self.FEED_URL}")
            feed = feedparser.parse(self.FEED_URL)
            
            all_reports = []
            
            for entry in feed.entries:
                report_id = hashlib.md5(entry.link.encode()).hexdigest()
                
                # Parse title for event type
                title = entry.get('title', '')
                event_type = 'Severe Weather'
                
                if 'Tornado' in title or 'tornado' in title:
                    event_type = 'Tornado'
                elif 'Hail' in title or 'hail' in title:
                    event_type = 'Hail'
                elif 'Wind' in title or 'wind' in title:
                    event_type = 'Wind'
                elif 'Severe' in title:
                    event_type = 'Severe Thunderstorm'
                
                # Parse published date
                event_time = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    import time
                    event_time = datetime.fromtimestamp(
                        time.mktime(entry.published_parsed),
                        tz=timezone.utc
                    ).isoformat()
                
                # Get description/summary
                description = entry.get('summary', '')
                
                report = {
                    'report_id': report_id,
                    'event_type': event_type,
                    'location': title,
                    'state': None,  # Would need to parse from description
                    'county': None,
                    'latitude': None,
                    'longitude': None,
                    'event_time': event_time or datetime.now(timezone.utc).isoformat(),
                    'magnitude': None,
                    'description': description[:500] if description else title,  # Limit description length
                    'source': 'NOAA SPC',
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                all_reports.append(report)
            
            logger.info(f"Fetched {len(all_reports)} storm reports")
            return all_reports
            
        except Exception as e:
            logger.error(f"Error fetching storm reports: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def insert_to_bigquery(self, reports: List[Dict[str, Any]]):
        """Insert storm reports into BigQuery"""
        if not reports:
            logger.warning("No storm reports to insert")
            return
        
        table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{self.TABLE_NAME}"
        
        try:
            errors = bq_client.insert_rows_json(table_id, reports)
            if errors:
                logger.error(f"Errors inserting storm reports: {errors}")
            else:
                logger.info(f"Successfully inserted {len(reports)} storm reports")
        except Exception as e:
            logger.error(f"Error inserting to BigQuery: {e}")


class DrugAvailabilityFetcher:
    """Fetch drug availability data from HealthData.gov GeoJSON"""
    
    FEED_URL = "https://healthdata.gov/resource/879u-23sm.geojson"
    TABLE_NAME = "drug_availability"
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch and parse drug availability GeoJSON"""
        try:
            logger.info(f"Fetching drug availability data from {self.FEED_URL}")
            response = requests.get(self.FEED_URL, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            
            drug_records = []
            features = data.get('features', [])
            
            for feature in features[:200]:  # Limit to 200 records
                props = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                coords = geometry.get('coordinates', [])
                
                # Extract key fields
                record_id = hashlib.md5(f"{props.get('ndc', '')}_{datetime.now().isoformat()}".encode()).hexdigest()
                
                drug_record = {
                    'record_id': record_id,
                    'drug_name': props.get('nonproprietaryname'),
                    'manufacturer': props.get('labelername'),
                    'ndc': props.get('ndc'),
                    'status': props.get('currentmarketingstatus'),
                    'dosage_form': props.get('dosageformname'),
                    'route': props.get('routename'),
                    'latitude': coords[1] if len(coords) > 1 else None,
                    'longitude': coords[0] if len(coords) > 0 else None,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                drug_records.append(drug_record)
            
            logger.info(f"Fetched {len(drug_records)} drug availability records")
            return drug_records
            
        except Exception as e:
            logger.error(f"Error fetching drug availability data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def insert_to_bigquery(self, records: List[Dict[str, Any]]):
        """Insert drug availability data into BigQuery"""
        if not records:
            logger.warning("No drug availability data to insert")
            return
        
        table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{self.TABLE_NAME}"
        
        try:
            errors = bq_client.insert_rows_json(table_id, records)
            if errors:
                logger.error(f"Errors inserting drug availability data: {errors}")
            else:
                logger.info(f"Successfully inserted {len(records)} drug availability records")
        except Exception as e:
            logger.error(f"Error inserting to BigQuery: {e}")


class CDCCovidDataFetcher:
    """Fetch CDC COVID data from XML feed with proper column structure"""
    
    FEED_URL = "https://data.cdc.gov/api/views/gvsb-yw6g/rows.xml?accessType=DOWNLOAD"
    TABLE_NAME = "cdc_covid_data"
    
    def fetch_data(self) -> List[Dict[str, Any]]:
        """Fetch and parse CDC COVID XML data into columns"""
        try:
            logger.info(f"Fetching CDC COVID data from {self.FEED_URL}")
            response = requests.get(self.FEED_URL, timeout=60)
            response.raise_for_status()
            
            # Parse XML
            data = xmltodict.parse(response.text)
            
            covid_records = []
            rows = data.get('response', {}).get('row', {}).get('row', [])
            
            # Ensure rows is a list
            if not isinstance(rows, list):
                rows = [rows] if rows else []
            
            for row in rows[:200]:  # Limit to 200 records
                # Generate unique record ID
                record_id = hashlib.md5(
                    f"{row.get('@_id', '')}_{row.get('mmwrweek_end', '')}".encode()
                ).hexdigest()
                
                # Parse dates safely
                def parse_timestamp(date_str):
                    if not date_str:
                        return None
                    try:
                        from dateutil import parser
                        return parser.parse(date_str).isoformat()
                    except:
                        return None
                
                # Convert to proper data types
                covid_record = {
                    'record_id': record_id,
                    'row_id': row.get('@_id'),
                    'level': row.get('level'),
                    'perc_diff': float(row.get('perc_diff')) if row.get('perc_diff') else None,
                    'percent_pos': float(row.get('percent_pos')) if row.get('percent_pos') else None,
                    'percent_pos_2_week': float(row.get('percent_pos_2_week')) if row.get('percent_pos_2_week') else None,
                    'percent_pos_4_week': float(row.get('percent_pos_4_week')) if row.get('percent_pos_4_week') else None,
                    'number_tested': int(row.get('number_tested')) if row.get('number_tested') else None,
                    'number_tested_2_week': int(row.get('number_tested_2_week')) if row.get('number_tested_2_week') else None,
                    'number_tested_4_week': int(row.get('number_tested_4_week')) if row.get('number_tested_4_week') else None,
                    'posted': parse_timestamp(row.get('posted')),
                    'mmwr_week_end': parse_timestamp(row.get('mmwrweek_end')),
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                covid_records.append(covid_record)
            
            logger.info(f"Fetched {len(covid_records)} CDC COVID records")
            return covid_records
            
        except Exception as e:
            logger.error(f"Error fetching CDC COVID data: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def insert_to_bigquery(self, records: List[Dict[str, Any]]):
        """Insert CDC COVID data into BigQuery"""
        if not records:
            logger.warning("No CDC COVID data to insert")
            return
        
        table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{self.TABLE_NAME}"
        
        try:
            errors = bq_client.insert_rows_json(table_id, records)
            if errors:
                logger.error(f"Errors inserting CDC COVID data: {errors}")
            else:
                logger.info(f"Successfully inserted {len(records)} CDC COVID records")
        except Exception as e:
            logger.error(f"Error inserting to BigQuery: {e}")


def main():
    """Main function to fetch all external data and load into BigQuery"""
    logger.info("Starting external data ingestion...")
    
    # Fetch and insert wildfire data
    wildfire_fetcher = WildfireDataFetcher()
    wildfire_data = wildfire_fetcher.fetch_data()
    wildfire_fetcher.insert_to_bigquery(wildfire_data)
    
    # Fetch and insert earthquake data
    earthquake_fetcher = EarthquakeDataFetcher()
    earthquake_data = earthquake_fetcher.fetch_data()
    earthquake_fetcher.insert_to_bigquery(earthquake_data)
    
    # Fetch and insert storm reports
    storm_fetcher = StormReportsFetcher()
    storm_data = storm_fetcher.fetch_data()
    storm_fetcher.insert_to_bigquery(storm_data)
    
    # Fetch and insert drug availability data
    drug_fetcher = DrugAvailabilityFetcher()
    drug_data = drug_fetcher.fetch_data()
    drug_fetcher.insert_to_bigquery(drug_data)
    
    # Fetch and insert CDC COVID data
    cdc_covid_fetcher = CDCCovidDataFetcher()
    cdc_covid_data = cdc_covid_fetcher.fetch_data()
    cdc_covid_fetcher.insert_to_bigquery(cdc_covid_data)
    
    logger.info("External data ingestion complete!")
    
    logger.info("External data ingestion complete!")


if __name__ == "__main__":
    main()
