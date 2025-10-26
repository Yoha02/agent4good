"""
Test BigQuery Authentication
Run this to check if your Google Cloud credentials are properly configured.
"""
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("BIGQUERY AUTHENTICATION TEST")
print("=" * 60)

# Check environment variables
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

print("\n1. Environment Variables:")
print(f"   GOOGLE_CLOUD_PROJECT: {project_id}")
print(f"   BIGQUERY_DATASET: {dataset_id}")
print(f"   BIGQUERY_TABLE_REPORTS: {table_id}")
print(f"   GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")

print("\n2. Checking credentials file:")
if credentials_path:
    if os.path.exists(credentials_path):
        print(f"   ✓ Credentials file found at: {credentials_path}")
    else:
        print(f"   ✗ Credentials file NOT found at: {credentials_path}")
else:
    print("   ℹ GOOGLE_APPLICATION_CREDENTIALS not set")
    print("   Will try Application Default Credentials...")

print("\n3. Testing BigQuery connection:")
try:
    from google.cloud import bigquery
    
    # Try to create client
    client = bigquery.Client(project=project_id)
    print(f"   ✓ BigQuery client created successfully")
    print(f"   Project: {client.project}")
    
    # Try to access the table
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    print(f"\n4. Testing table access: {table_ref}")
    
    try:
        table = client.get_table(table_ref)
        print(f"   ✓ Table exists!")
        print(f"   Table ID: {table.table_id}")
        print(f"   Num rows: {table.num_rows}")
        print(f"   Schema fields: {len(table.schema)}")
        
        # List first few field names
        print(f"\n5. Schema preview (first 10 fields):")
        for i, field in enumerate(table.schema[:10]):
            print(f"   - {field.name} ({field.field_type})")
        
    except Exception as e:
        print(f"   ✗ Cannot access table: {e}")
        print("\nPossible issues:")
        print("   1. Table doesn't exist yet")
        print("   2. Service account lacks permissions")
        print("   3. Table name mismatch")
        
except Exception as e:
    print(f"   ✗ Failed to create BigQuery client")
    print(f"   Error: {e}")
    print("\n" + "=" * 60)
    print("AUTHENTICATION SETUP NEEDED")
    print("=" * 60)
    print("\nOption 1: Use gcloud CLI (Recommended for development)")
    print("   Run: gcloud auth application-default login")
    print("\nOption 2: Use Service Account JSON Key")
    print("   1. Go to: https://console.cloud.google.com/iam-admin/serviceaccounts")
    print(f"   2. Select project: {project_id}")
    print("   3. Create a service account (or use existing)")
    print("   4. Grant role: BigQuery Data Editor")
    print("   5. Create JSON key and download it")
    print("   6. Save it to this folder (e.g., 'bigquery-key.json')")
    print("   7. Add to .env file:")
    print("      GOOGLE_APPLICATION_CREDENTIALS=C:\\Users\\semaa\\agent4good\\bigquery-key.json")
    print("\n" + "=" * 60)

print("\n✓ Test complete!\n")
