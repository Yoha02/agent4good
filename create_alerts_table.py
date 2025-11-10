"""
Script to create the public_health_alerts table in BigQuery
Run this once to set up the alerts storage table
"""

from google.cloud import bigquery
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize BigQuery client
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = 'public_health_alerts'

client = bigquery.Client(project=project_id)

# Define table schema
schema = [
    bigquery.SchemaField("alert_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("message", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("level", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("issued_by", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("issued_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("duration_hours", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("expires_at", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("cancelled", "BOOLEAN", mode="NULLABLE"),
    bigquery.SchemaField("cancelled_by", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("cancelled_at", "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("location_city", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("location_state", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("location_county", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("active", "BOOLEAN", mode="NULLABLE"),
]

# Create table reference
table_ref = f"{project_id}.{dataset_id}.{table_id}"
table = bigquery.Table(table_ref, schema=schema)

# Create the table
try:
    table = client.create_table(table, exists_ok=True)
    print(f"✅ Table {table_ref} created successfully!")
    print(f"\nTable details:")
    print(f"  - Project: {project_id}")
    print(f"  - Dataset: {dataset_id}")
    print(f"  - Table: {table_id}")
    print(f"  - Full path: {table_ref}")
    print(f"\nYou can now issue public health alerts!")
except Exception as e:
    print(f"❌ Error creating table: {e}")
    import traceback
    traceback.print_exc()
