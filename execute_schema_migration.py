"""
Execute BigQuery schema migration safely
Only adds columns that don't already exist
"""
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

# Get BigQuery configuration
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')

print(f"Starting schema migration for {project_id}.{dataset_id}.{table_id}")
print("=" * 80)

try:
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)
    
    # Get current table schema
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    table = client.get_table(table_ref)
    
    existing_columns = {field.name for field in table.schema}
    print(f"Current schema has {len(existing_columns)} columns")
    
    # Define new columns to add
    new_columns = [
        ('ai_tags', 'STRING', 'AI-generated tags (JSON array)'),
        ('ai_confidence', 'FLOAT64', 'AI confidence score (0-1)'),
        ('ai_analyzed_at', 'TIMESTAMP', 'When AI analysis was performed'),
        ('attachment_urls', 'STRING', 'GCS URLs for attachments (JSON array)'),
        ('reviewed_by', 'STRING', 'Name of official who reviewed'),
        ('reviewed_at', 'TIMESTAMP', 'When review was completed'),
        ('exclude_from_analysis', 'BOOL', 'Whether to exclude from analysis'),
        ('exclusion_reason', 'STRING', 'Reason for exclusion'),
        ('manual_tags', 'STRING', 'Manually added tags (JSON array)')
    ]
    
    # Filter out columns that already exist
    columns_to_add = [(name, dtype, desc) for name, dtype, desc in new_columns if name not in existing_columns]
    
    if not columns_to_add:
        print("\n✓  All columns already exist. No migration needed!")
        exit(0)
    
    print(f"\nAdding {len(columns_to_add)} new columns:")
    for name, dtype, desc in columns_to_add:
        print(f"  - {name} ({dtype}): {desc}")
    
    # Execute ALTER TABLE for each column
    print("\n" + "=" * 80)
    print("EXECUTING MIGRATION:")
    print("=" * 80)
    
    for col_name, col_type, col_desc in columns_to_add:
        query = f"""
        ALTER TABLE `{project_id}.{dataset_id}.{table_id}`
        ADD COLUMN IF NOT EXISTS {col_name} {col_type}
        """
        
        print(f"\nAdding column: {col_name}...")
        try:
            query_job = client.query(query)
            query_job.result()  # Wait for completion
            print(f"  ✓  Successfully added {col_name}")
        except Exception as e:
            print(f"  ⚠️  Error adding {col_name}: {e}")
    
    # Verify final schema
    print("\n" + "=" * 80)
    print("VERIFYING MIGRATION:")
    print("=" * 80)
    
    table = client.get_table(table_ref)  # Refresh table metadata
    final_columns = {field.name for field in table.schema}
    
    success_count = 0
    for col_name, _, _ in columns_to_add:
        if col_name in final_columns:
            print(f"  ✓  {col_name} exists")
            success_count += 1
        else:
            print(f"  ✗  {col_name} NOT FOUND")
    
    print("\n" + "=" * 80)
    print("MIGRATION COMPLETE:")
    print("=" * 80)
    print(f"  Successfully added: {success_count}/{len(columns_to_add)} columns")
    print(f"  Final schema has: {len(final_columns)} columns")
    
    if success_count == len(columns_to_add):
        print("\n  ✓  All columns added successfully!")
    else:
        print(f"\n  ⚠️  Some columns may have failed. Please review the output above.")
    
except Exception as e:
    print(f"\n[ERROR] Migration failed: {e}")
    print("\nPlease verify:")
    print("  1. You have BigQuery Data Editor role")
    print("  2. The table exists and is accessible")
    print("  3. Environment variables are correct")
    exit(1)
