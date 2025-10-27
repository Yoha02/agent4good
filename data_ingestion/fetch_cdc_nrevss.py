"""
Fetch CDC NREVSS (National Respiratory and Enteric Virus Surveillance System) data
and load it into BigQuery

This script should be run on a schedule (e.g., daily or weekly) to keep the data fresh.
"""

import os
import requests
from google.cloud import bigquery
from datetime import datetime, timedelta
import json

# Configuration
GCP_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')
DATASET_ID = 'CrowdsourceData'
TABLE_ID = 'nrevss_respiratory_data'

# CDC NREVSS Socrata API endpoints and credentials
RSV_API_URL = "https://data.cdc.gov/resource/3cxc-4k8q.csv"  # Updated NREVSS dataset
CDC_APP_TOKEN = os.getenv('CDC_APP_TOKEN', '14hp3llj2jh6n8rcwxegn80ud')  # App token for higher rate limits

def create_table_if_not_exists(client):
    """Create the NREVSS table in BigQuery if it doesn't exist"""
    
    table_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("level", "STRING", mode="NULLABLE", description="Geographic level (National, Regional, etc)"),
        bigquery.SchemaField("perc_diff", "FLOAT", mode="NULLABLE", description="Percent difference"),
        bigquery.SchemaField("pcr_percent_positive", "FLOAT", mode="NULLABLE", description="PCR percent positive"),
        bigquery.SchemaField("percent_pos_2_week", "FLOAT", mode="NULLABLE", description="2-week percent positive"),
        bigquery.SchemaField("percent_pos_4_week", "FLOAT", mode="NULLABLE", description="4-week percent positive"),
        bigquery.SchemaField("pcr_detections", "INTEGER", mode="NULLABLE", description="PCR detections"),
        bigquery.SchemaField("detections_2_week", "INTEGER", mode="NULLABLE", description="2-week detections"),
        bigquery.SchemaField("detections_4_week", "INTEGER", mode="NULLABLE", description="4-week detections"),
        bigquery.SchemaField("pcr_tests", "INTEGER", mode="NULLABLE", description="PCR tests conducted"),
        bigquery.SchemaField("posted", "TIMESTAMP", mode="NULLABLE", description="When data was posted"),
        bigquery.SchemaField("mmwrweek_end", "DATE", mode="NULLABLE", description="MMWR week ending date"),
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

def fetch_nrevss_data(limit=5000):
    """Fetch RSV surveillance data from CDC JSON endpoint
    
    Fetches the most recent NREVSS data from CDC.
    """
    
    print(f"[INFO] Fetching NREVSS data from CDC (limit={limit})...")
    
    try:
        # Use JSON endpoint with ordering to get most recent data
        url = "https://data.cdc.gov/resource/3cxc-4k8q.json"
        params = {
            '$limit': limit,
            '$order': 'mmwrweek_end DESC'
        }
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        print(f"[SUCCESS] Retrieved {len(data)} records from CDC NREVSS")
        if data:
            first_date = data[0].get('mmwrweek_end', 'Unknown')
            last_date = data[-1].get('mmwrweek_end', 'Unknown') if len(data) > 1 else first_date
            print(f"[INFO] Date range: {last_date} to {first_date}")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch NREVSS data: {e}")
        import traceback
        traceback.print_exc()
        return []

def transform_nrevss_data(raw_data):
    """Transform CDC JSON data to match BigQuery schema"""
    from datetime import datetime
    
    transformed = []
    load_time = datetime.now().isoformat()
    
    for record in raw_data:
        # Parse dates safely
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                # Parse ISO format date
                dt = datetime.fromisoformat(date_str.replace('T00:00:00.000', ''))
                return dt.strftime('%Y-%m-%d')
            except:
                return None
        
        def parse_timestamp(ts_str):
            if not ts_str:
                return None
            try:
                # Parse ISO format timestamp
                return datetime.fromisoformat(ts_str.replace('T', ' ').replace('.000', '')).isoformat()
            except:
                return None
        
        # Convert numeric fields safely
        def safe_float(value):
            if value is None or value == '':
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_int(value):
            if value is None or value == '':
                return None
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None
        
        transformed_record = {
            'level': record.get('level'),
            'perc_diff': safe_float(record.get('perc_diff')),
            'pcr_percent_positive': safe_float(record.get('pcr_percent_positive')),
            'percent_pos_2_week': safe_float(record.get('percent_pos_2_week')),
            'percent_pos_4_week': safe_float(record.get('percent_pos_4_week')),
            'pcr_detections': safe_int(record.get('pcr_detections')),
            'detections_2_week': safe_int(record.get('detections_2_week')),
            'detections_4_week': safe_int(record.get('detections_4_week')),
            'pcr_tests': safe_int(record.get('pcr_tests')),
            'posted': parse_timestamp(record.get('posted')),
            'mmwrweek_end': parse_date(record.get('mmwrweek_end')),
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
    print("CDC NREVSS Data Ingestion to BigQuery")
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
    raw_data = fetch_nrevss_data(limit=10000)
    
    if not raw_data:
        print("[ERROR] No data retrieved from CDC")
        return
    
    # Transform data
    transformed_data = transform_nrevss_data(raw_data)
    
    # Load to BigQuery
    load_to_bigquery(client, transformed_data)
    
    print("=" * 80)
    print("Data ingestion complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
