"""
Fetch CDC Respiratory Disease Rates data
Rates of Laboratory-Confirmed RSV, COVID-19, and Flu
Dataset: https://data.cdc.gov/Public-Health-Surveillance/Rates-of-Laboratory-Confirmed-RSV-COVID-19-and-Flu/kvib-3txy

This script should be run weekly to keep the data fresh.
"""

import os
import requests
from google.cloud import bigquery
from datetime import datetime, timezone
import json
from typing import List, Dict, Any

# Configuration
GCP_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')
DATASET_ID = 'CrowdsourceData'
TABLE_ID = 'respiratory_disease_rates'

# CDC API endpoint
API_URL = "https://data.cdc.gov/resource/kvib-3txy.json"
CDC_APP_TOKEN = os.getenv('CDC_APP_TOKEN', '14hp3llj2jh6n8rcwxegn80ud')

def create_table_if_not_exists(client):
    """Create the respiratory disease rates table in BigQuery if it doesn't exist"""
    
    table_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("record_id", "STRING", mode="REQUIRED", description="Unique record identifier"),
        bigquery.SchemaField("surveillance_network", "STRING", mode="NULLABLE", description="Surveillance network"),
        bigquery.SchemaField("season", "STRING", mode="NULLABLE", description="Surveillance season"),
        bigquery.SchemaField("mmwr_year", "FLOAT", mode="NULLABLE", description="MMWR Year"),
        bigquery.SchemaField("mmwr_week", "FLOAT", mode="NULLABLE", description="MMWR Week"),
        bigquery.SchemaField("weekenddate", "STRING", mode="NULLABLE", description="Week ending date (original format)"),
        bigquery.SchemaField("week_end_date", "DATE", mode="NULLABLE", description="Week ending date (parsed)"),
        bigquery.SchemaField("age_group", "STRING", mode="NULLABLE", description="Age group"),
        bigquery.SchemaField("sex", "STRING", mode="NULLABLE", description="Sex category"),
        bigquery.SchemaField("race_ethnicity", "STRING", mode="NULLABLE", description="Race/ethnicity"),
        bigquery.SchemaField("site", "STRING", mode="NULLABLE", description="Geographic site"),
        bigquery.SchemaField("disease_type", "STRING", mode="NULLABLE", description="Type of disease data"),
        bigquery.SchemaField("weekly_rate", "FLOAT", mode="NULLABLE", description="Weekly rate per 100,000 population"),
        bigquery.SchemaField("cumulative_rate", "FLOAT", mode="NULLABLE", description="Cumulative rate"),
        bigquery.SchemaField("load_timestamp", "TIMESTAMP", mode="REQUIRED", description="When this record was loaded"),
    ]
    
    try:
        client.get_table(table_ref)
        print(f"[INFO] Table {table_ref} already exists")
    except Exception as e:
        print(f"[INFO] Creating table {table_ref}")
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        print(f"[SUCCESS] Created table {table.project}.{table.dataset_id}.{table.table_id}")

def fetch_respiratory_rates_data(limit=15000):
    """Fetch respiratory disease rates from CDC Socrata API
    
    Gets the most recent data by ordering descending.
    """
    
    print(f"[INFO] Fetching respiratory disease rates from CDC (limit={limit})...")
    
    # Query with ordering to get most recent data first
    params = {
        '$limit': limit,
        '$order': '_weekenddate DESC'
    }
    
    try:
        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"[SUCCESS] Retrieved {len(data)} records from CDC")
        if data:
            first_date = data[0].get('_weekenddate', 'Unknown')
            last_date = data[-1].get('_weekenddate', 'Unknown') if len(data) > 1 else first_date
            print(f"[INFO] Date range: {last_date} to {first_date}")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch respiratory rates data: {e}")
        import traceback
        traceback.print_exc()
        return []

def transform_respiratory_rates_data(raw_data):
    """Transform CDC data to match BigQuery schema"""
    import hashlib
    
    transformed = []
    load_time = datetime.now(timezone.utc).isoformat()
    
    for record in raw_data:
        # Generate unique record ID
        record_str = f"{record.get('surveillance_network', '')}_{record.get('season', '')}_{record.get('mmwr_year', '')}_{record.get('mmwr_week', '')}_{record.get('age_group', '')}_{record.get('site', '')}"
        record_id = hashlib.md5(record_str.encode()).hexdigest()
        
        # Parse week ending date from format like "2022-06-11 00:00:00"
        weekenddate_raw = record.get('_weekenddate', '')
        week_end_date = None
        
        if weekenddate_raw:
            try:
                # Parse ISO format date and extract just the date part
                dt = datetime.fromisoformat(weekenddate_raw.replace(' 00:00:00', ''))
                week_end_date = dt.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"[WARNING] Could not parse date '{weekenddate_raw}': {e}")
        
        # Convert numeric fields safely
        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        transformed_record = {
            'record_id': record_id,
            'surveillance_network': record.get('surveillance_network'),
            'season': record.get('season'),
            'mmwr_year': safe_float(record.get('mmwr_year')),
            'mmwr_week': safe_float(record.get('mmwr_week')),
            'weekenddate': weekenddate_raw,
            'week_end_date': week_end_date,
            'age_group': record.get('age_group'),
            'sex': record.get('sex'),
            'race_ethnicity': record.get('race_ethnicity'),
            'site': record.get('site'),
            'disease_type': record.get('type'),
            'weekly_rate': safe_float(record.get('weekly_rate')),
            'cumulative_rate': safe_float(record.get('cumulative_rate')),
            'load_timestamp': load_time
        }
        
        transformed.append(transformed_record)
    
    print(f"[INFO] Transformed {len(transformed)} records")
    return transformed

def load_to_bigquery(client, data):
    """Load data into BigQuery table"""
    
    if not data:
        print("[WARNING] No data to load")
        return
    
    table_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Configure load job to replace existing data
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace table
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    
    print(f"[INFO] Loading {len(data)} records to {table_ref}...")
    
    try:
        load_job = client.load_table_from_json(
            data,
            table_ref,
            job_config=job_config
        )
        
        load_job.result()  # Wait for job to complete
        
        print(f"[SUCCESS] Loaded {load_job.output_rows} rows to {table_ref}")
        
    except Exception as e:
        print(f"[ERROR] Failed to load data to BigQuery: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("CDC Respiratory Disease Rates Data Ingestion to BigQuery")
    print("Dataset: Rates of Laboratory-Confirmed RSV, COVID-19, and Flu")
    print("=" * 80)
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=GCP_PROJECT_ID)
        print(f"[SUCCESS] Connected to BigQuery project: {GCP_PROJECT_ID}")
    except Exception as e:
        print(f"[ERROR] Failed to connect to BigQuery: {e}")
        return
    
    # Create table if needed
    create_table_if_not_exists(client)
    
    # Fetch data from CDC
    raw_data = fetch_respiratory_rates_data(limit=15000)
    
    if not raw_data:
        print("[ERROR] No data retrieved from CDC")
        return
    
    # Transform data
    transformed_data = transform_respiratory_rates_data(raw_data)
    
    # Load to BigQuery
    load_to_bigquery(client, transformed_data)
    
    print("=" * 80)
    print("Data ingestion complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
