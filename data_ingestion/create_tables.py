"""
Create BigQuery tables for external data sources
"""

import os
import json
from google.cloud import bigquery
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize BigQuery client
bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
DATASET = os.getenv('BIGQUERY_DATASET', 'CrowdsourceData')


def load_schema(schema_file: str) -> list:
    """Load BigQuery schema from JSON file"""
    schema_path = os.path.join(os.path.dirname(__file__), 'schemas', schema_file)
    with open(schema_path, 'r') as f:
        schema_json = json.load(f)
    
    # Convert JSON schema to BigQuery SchemaField objects
    schema_fields = []
    for field in schema_json:
        schema_fields.append(
            bigquery.SchemaField(
                name=field['name'],
                field_type=field['type'],
                mode=field.get('mode', 'NULLABLE'),
                description=field.get('description', '')
            )
        )
    return schema_fields


def create_table(table_name: str, schema_file: str, description: str):
    """Create a BigQuery table with the given schema"""
    table_id = f"{os.getenv('GOOGLE_CLOUD_PROJECT')}.{DATASET}.{table_name}"
    
    try:
        # Check if table already exists
        try:
            existing_table = bq_client.get_table(table_id)
            logger.info(f"Table {table_name} already exists")
            return existing_table
        except Exception:
            pass  # Table doesn't exist, create it
        
        # Load schema
        schema = load_schema(schema_file)
        
        # Create table
        table = bigquery.Table(table_id, schema=schema)
        table.description = description
        
        # Create the table
        table = bq_client.create_table(table)
        logger.info(f"Created table {table_name}")
        return table
        
    except Exception as e:
        logger.error(f"Error creating table {table_name}: {e}")
        raise


def main():
    """Create all external data tables"""
    logger.info("Creating BigQuery tables for external data sources...")
    
    tables = [
        {
            'name': 'wildfire_incidents',
            'schema_file': 'wildfire_incidents.json',
            'description': 'Active wildfire incidents from InciWeb RSS feed'
        },
        {
            'name': 'earthquake_events',
            'schema_file': 'earthquake_events.json',
            'description': 'Earthquake events from USGS Atom feed'
        },
        {
            'name': 'storm_reports',
            'schema_file': 'storm_reports.json',
            'description': 'Severe weather reports from NOAA Storm Prediction Center RSS'
        },
        {
            'name': 'drug_availability',
            'schema_file': 'drug_availability.json',
            'description': 'Drug availability data from HealthData.gov GeoJSON'
        },
        {
            'name': 'cdc_covid_data',
            'schema_file': 'cdc_covid_data.json',
            'description': 'CDC COVID-19 testing data with proper column structure'
        }
    ]
    
    for table_info in tables:
        try:
            create_table(
                table_info['name'],
                table_info['schema_file'],
                table_info['description']
            )
        except Exception as e:
            logger.error(f"Failed to create table {table_info['name']}: {e}")
    
    logger.info("Table creation complete!")


if __name__ == "__main__":
    main()
