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
RSV_API_URL = "https://data.cdc.gov/resource/52kb-ccu2.json"  # Correct NREVSS dataset
CDC_APP_TOKEN = os.getenv('CDC_APP_TOKEN', '14hp3llj2jh6n8rcwxegn80ud')  # App token for higher rate limits

def create_table_if_not_exists(client):
    """Create the NREVSS table in BigQuery if it doesn't exist"""
    
    table_ref = f"{GCP_PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("testtype", "STRING", mode="NULLABLE", description="Diagnostic Test Type"),
        bigquery.SchemaField("season", "STRING", mode="NULLABLE", description="Surveillance Year"),
        bigquery.SchemaField("repweekcode", "STRING", mode="NULLABLE", description="Week ending Code"),
        bigquery.SchemaField("repweekdate", "STRING", mode="NULLABLE", description="Week ending Date (raw from CDC)"),
        bigquery.SchemaField("date_string", "STRING", mode="NULLABLE", description="ISO formatted date (YYYY-MM-DD)"),
        bigquery.SchemaField("hhs_region", "INTEGER", mode="NULLABLE", description="HHS region (1-10)"),
        bigquery.SchemaField("rsvpos", "INTEGER", mode="NULLABLE", description="RSV Detections"),
        bigquery.SchemaField("rsvtest", "INTEGER", mode="NULLABLE", description="RSV Tests"),
        bigquery.SchemaField("outlier", "INTEGER", mode="NULLABLE", description="Outlier flag"),
        bigquery.SchemaField("positivity_rate", "FLOAT", mode="NULLABLE", description="RSV positivity rate (%)"),
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

def fetch_nrevss_data(limit=50000):
    """Fetch RSV surveillance data from CDC Socrata API
    
    Note: Socrata has a limit of 50,000 rows per request max.
    We order by repweekdate DESC to get the most recent data first.
    """
    
    print(f"[INFO] Fetching NREVSS data from CDC (limit={limit})...")
    
    # Query for most recent data - order by date descending
    params = {
        '$limit': limit,
        '$order': 'repweekdate DESC'  # Get newest data first
    }
    
    try:
        response = requests.get(RSV_API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"[SUCCESS] Retrieved {len(data)} records from CDC NREVSS")
        if data:
            first_date = data[0].get('repweekdate', 'Unknown')
            last_date = data[-1].get('repweekdate', 'Unknown')
            print(f"[INFO] Date range: {last_date} to {first_date}")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to fetch NREVSS data: {e}")
        return []

def transform_nrevss_data(raw_data):
    """Transform CDC data to match BigQuery schema"""
    from datetime import datetime
    
    transformed = []
    load_time = datetime.now().isoformat()
    
    for record in raw_data:
        # Calculate positivity rate
        rsvpos = int(record.get('rsvpos', 0)) if record.get('rsvpos') else 0
        rsvtest = int(record.get('rsvtest', 0)) if record.get('rsvtest') else 0
        positivity_rate = (rsvpos / rsvtest * 100) if rsvtest > 0 else 0.0
        
        # Parse and convert date from ddMONyyyy to YYYY-MM-DD
        repweekdate_raw = record.get('repweekdate', '')
        date_string = None
        
        if repweekdate_raw and len(repweekdate_raw) >= 9:
            try:
                # Parse "31OCT2015" format to YYYY-MM-DD
                dt = datetime.strptime(repweekdate_raw, '%d%b%Y')
                date_string = dt.strftime('%Y-%m-%d')
            except Exception as e:
                print(f"[WARNING] Could not parse date '{repweekdate_raw}': {e}")
                date_string = None
        
        transformed_record = {
            'testtype': record.get('testtype'),
            'season': record.get('season'),
            'repweekcode': record.get('repweekcode'),
            'repweekdate': repweekdate_raw if repweekdate_raw else None,
            'date_string': date_string,
            'hhs_region': int(record.get('hhs_region')) if record.get('hhs_region') else None,
            'rsvpos': rsvpos if rsvpos > 0 else None,
            'rsvtest': rsvtest if rsvtest > 0 else None,
            'outlier': int(record.get('outlier', 0)) if record.get('outlier') else None,
            'positivity_rate': round(positivity_rate, 2),
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
