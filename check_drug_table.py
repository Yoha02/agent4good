#!/usr/bin/env python3
"""Check drug availability table schema and data"""

from google.cloud import bigquery

# Initialize BigQuery client
client = bigquery.Client(project='qwiklabs-gcp-00-4a7d408c735c')
dataset_id = 'CrowdsourceData'
table_id = 'drug_availability'

print("="*80)
print("🔍 DRUG AVAILABILITY TABLE CHECK")
print("="*80)

# Get table metadata
full_table_id = f'{client.project}.{dataset_id}.{table_id}'
table = client.get_table(full_table_id)

print(f"\n📊 Table: {table_id}")
print(f"Total Rows: {table.num_rows}")
print(f"Created: {table.created}")
print(f"Modified: {table.modified}")

# Print schema
print("\n📋 SCHEMA:")
print("-" * 80)
for field in table.schema:
    print(f"  {field.name:30} {field.field_type:15} {'NULLABLE' if field.is_nullable else 'REQUIRED'}")

# Get sample data
query = f"""
SELECT *
FROM `{full_table_id}`
ORDER BY created_at DESC
LIMIT 5
"""

print("\n📊 SAMPLE DATA (5 most recent records):")
print("-" * 80)
results = list(client.query(query).result())
print(f"Found {len(results)} records\n")

for i, row in enumerate(results, 1):
    print(f"\nRecord {i}:")
    for key, value in dict(row).items():
        print(f"  {key}: {value}")

# Get date range
date_query = f"""
SELECT 
    MIN(created_at) as earliest_date,
    MAX(created_at) as latest_date,
    COUNT(*) as total_records
FROM `{full_table_id}`
"""

print("\n\n📅 DATE RANGE:")
print("-" * 80)
date_results = list(client.query(date_query).result())
for row in date_results:
    print(f"Earliest Date: {row['earliest_date']}")
    print(f"Latest Date: {row['latest_date']}")
    print(f"Total Records: {row['total_records']}")

print("\n" + "="*80)
print("✅ Check Complete")
print("="*80)
