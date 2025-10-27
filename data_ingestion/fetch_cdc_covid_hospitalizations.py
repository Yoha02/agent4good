"""
CDC COVID-19 Hospitalization Data Ingestion
Fetches hospitalization rates from CDC Socrata API dataset 6jg4-xsqq
"""

import os
import requests
import hashlib
from datetime import datetime, timezone
from google.cloud import bigquery
from dotenv import load_dotenv
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize BigQuery client
bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
DATASET = os.getenv('BIGQUERY_DATASET', 'CrowdsourceData')
TABLE_NAME = 'cdc_covid_hospitalizations'


def create_table_if_not_exists():
    """Create the table if it doesn't exist"""
    table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{TABLE_NAME}"
    
    try:
        bq_client.get_table(table_id)
        logger.info(f"Table {table_id} already exists")
    except:
        logger.info(f"Creating table {table_id}")
        
        # Load schema
        import json
        schema_path = os.path.join(os.path.dirname(__file__), 'schemas', 'cdc_covid_hospitalizations.json')
        with open(schema_path, 'r') as f:
            schema_json = json.load(f)
        
        schema = [
            bigquery.SchemaField(
                name=field['name'],
                field_type=field['type'],
                mode=field.get('mode', 'NULLABLE'),
                description=field.get('description', '')
            )
            for field in schema_json
        ]
        
        table = bigquery.Table(table_id, schema=schema)
        table.description = "CDC COVID-19 laboratory-confirmed hospitalization rates by state, age, sex, and race/ethnicity"
        
        table = bq_client.create_table(table)
        logger.info(f"Created table {table.table_id}")


def fetch_data() -> List[Dict[str, Any]]:
    """Fetch CDC COVID hospitalization data from Socrata API"""
    try:
        url = "https://data.cdc.gov/resource/6jg4-xsqq.json"
        
        logger.info(f"Fetching CDC COVID hospitalization data from {url}")
        
        # Query parameters to get recent data
        params = {
            '$limit': 15000,
            '$order': '_weekenddate DESC'
        }
        
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        # Parse JSON
        data = response.json()
        
        records = []
        
        for idx, row in enumerate(data):
            # Generate unique record ID
            record_id = hashlib.md5(
                f"{row.get('_weekenddate', '')}_{row.get('state', '')}_{row.get('season', '')}_{row.get('agecategory_legend', '')}_{row.get('sex_label', '')}_{row.get('race_label', '')}_{idx}".encode()
            ).hexdigest()
            
            # Convert numeric fields safely
            def safe_float(value):
                if value is None or value == '':
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            # Format date as YYYY-MM-DD
            weekenddate = row.get('_weekenddate')
            
            # Build record
            record = {
                'record_id': record_id,
                'weekenddate': weekenddate,
                'state': row.get('state'),
                'season': row.get('season'),
                'agecategory': row.get('agecategory_legend'),
                'sex': row.get('sex_label'),
                'race': row.get('race_label'),
                'type': row.get('type'),
                'weeklyrate': safe_float(row.get('weeklyrate')),
                'cumulativerate': safe_float(row.get('cumulativerate')),
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            records.append(record)
        
        logger.info(f"Fetched {len(records)} CDC COVID hospitalization records")
        if records:
            logger.info(f"Date range: {records[-1].get('weekenddate')} to {records[0].get('weekenddate')}")
        return records
        
    except Exception as e:
        logger.error(f"Error fetching CDC COVID hospitalization data: {e}")
        import traceback
        traceback.print_exc()
        return []


def insert_to_bigquery(records: List[Dict[str, Any]]):
    """Insert CDC COVID hospitalization data into BigQuery"""
    if not records:
        logger.warning("No CDC COVID hospitalization data to insert")
        return
    
    table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{TABLE_NAME}"
    
    try:
        errors = bq_client.insert_rows_json(table_id, records)
        if errors:
            logger.error(f"Errors inserting CDC COVID hospitalization data: {errors}")
            # Show first few errors for debugging
            for error in errors[:5]:
                logger.error(f"Error detail: {error}")
        else:
            logger.info(f"Successfully inserted {len(records)} CDC COVID hospitalization records")
    except Exception as e:
        logger.error(f"Error inserting to BigQuery: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to fetch and insert data"""
    logger.info("Starting CDC COVID hospitalization data ingestion...")
    
    # Create table if needed
    create_table_if_not_exists()
    
    # Fetch data
    records = fetch_data()
    
    # Insert to BigQuery
    if records:
        insert_to_bigquery(records)
    
    logger.info("CDC COVID hospitalization data ingestion complete!")


if __name__ == "__main__":
    main()
