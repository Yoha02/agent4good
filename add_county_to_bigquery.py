"""
Add county column to BigQuery table
"""
import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

# Don't set GOOGLE_APPLICATION_CREDENTIALS if using Application Default Credentials
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    creds_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    if not os.path.exists(creds_path):
        print(f"⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {creds_path}")
        print("   Using Application Default Credentials instead...")
        del os.environ['GOOGLE_APPLICATION_CREDENTIALS']

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')

print(f"Adding county column to: {project_id}.{dataset_id}.{table_id}")

client = bigquery.Client(project=project_id)

# Add county column
query = f"""
ALTER TABLE `{project_id}.{dataset_id}.{table_id}`
ADD COLUMN IF NOT EXISTS county STRING OPTIONS(description="County name (auto-populated from ZIP)")
"""

try:
    job = client.query(query)
    job.result()  # Wait for completion
    print("✓ County column added successfully!")
    
    # Verify schema
    table = client.get_table(f"{project_id}.{dataset_id}.{table_id}")
    print(f"\nTable now has {len(table.schema)} columns:")
    for field in table.schema:
        if field.name in ['county', 'city', 'state', 'zip_code', 'address']:
            print(f"  - {field.name} ({field.field_type}, {field.mode})")
    
except Exception as e:
    print(f"✗ Error: {e}")
