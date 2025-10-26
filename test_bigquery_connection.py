"""
Test BigQuery connection and verify current schema before migration
"""
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

# Get BigQuery configuration
project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')

print(f"Project ID: {project_id}")
print(f"Dataset ID: {dataset_id}")
print(f"Table ID: {table_id}")
print("-" * 80)

try:
    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)
    print("[OK] BigQuery client initialized")
    
    # Get table reference
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    table = client.get_table(table_ref)
    
    print(f"[OK] Connected to table: {table_ref}")
    print(f"Total rows: {table.num_rows}")
    print(f"Total columns: {len(table.schema)}")
    print("-" * 80)
    
    # Display current schema
    print("\nCURRENT SCHEMA:")
    print("-" * 80)
    existing_columns = set()
    for field in table.schema:
        existing_columns.add(field.name)
        print(f"  {field.name:30} {field.field_type:15} {'NULLABLE' if field.mode == 'NULLABLE' else 'REQUIRED'}")
    
    print("\n" + "=" * 80)
    print("COLUMNS TO BE ADDED:")
    print("=" * 80)
    
    # Check which columns need to be added
    new_columns = {
        'ai_tags': 'STRING',
        'ai_confidence': 'FLOAT64',
        'ai_analyzed_at': 'TIMESTAMP',
        'attachment_urls': 'STRING',
        'reviewed_by': 'STRING',
        'reviewed_at': 'TIMESTAMP',
        'exclude_from_analysis': 'BOOL',
        'exclusion_reason': 'STRING',
        'manual_tags': 'STRING'
    }
    
    columns_to_add = []
    columns_already_exist = []
    
    for col_name, col_type in new_columns.items():
        if col_name in existing_columns:
            columns_already_exist.append(col_name)
            print(f"  ⚠️  {col_name:30} {col_type:15} (ALREADY EXISTS)")
        else:
            columns_to_add.append(col_name)
            print(f"  ✓  {col_name:30} {col_type:15} (WILL BE ADDED)")
    
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY:")
    print("=" * 80)
    print(f"  Columns that already exist: {len(columns_already_exist)}")
    print(f"  Columns to be added: {len(columns_to_add)}")
    
    if columns_already_exist:
        print(f"\n  ⚠️  WARNING: These columns already exist and will be skipped:")
        for col in columns_already_exist:
            print(f"     - {col}")
    
    if columns_to_add:
        print(f"\n  ✓  These columns will be added:")
        for col in columns_to_add:
            print(f"     - {col}")
    else:
        print("\n  ℹ️  No columns need to be added. Schema is already up to date!")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    
    if len(columns_to_add) > 0:
        print(f"  ✓  Safe to proceed with migration ({len(columns_to_add)} columns will be added)")
        print(f"\n  Run: python execute_schema_migration.py")
    else:
        print(f"  ℹ️  No migration needed - all columns already exist")
    
except Exception as e:
    print(f"[ERROR] {e}")
    print("\nPlease verify:")
    print("  1. BigQuery credentials are set up")
    print("  2. Environment variables in .env are correct")
    print("  3. You have access to the project/dataset/table")
