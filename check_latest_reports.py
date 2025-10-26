"""
Check if the latest reports are in BigQuery
"""
from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')

client = bigquery.Client(project=project_id)
table_ref = f"{project_id}.{dataset_id}.{table_id}"

# Get latest 5 reports
query = f"""
SELECT 
    report_id,
    report_type,
    city,
    state,
    description,
    status,
    ai_overall_summary,
    ai_tags,
    ai_confidence,
    timestamp
FROM `{table_ref}`
ORDER BY timestamp DESC
LIMIT 5
"""

print("Latest 5 Reports in BigQuery:")
print("=" * 80)

results = client.query(query).result()

for i, row in enumerate(results, 1):
    print(f"\n{i}. Report ID: {row.report_id}")
    print(f"   Type: {row.report_type} | Status: {row.status}")
    print(f"   Location: {row.city}, {row.state}")
    print(f"   Description: {row.description[:100]}...")
    print(f"   AI Summary: {row.ai_overall_summary[:100] if row.ai_overall_summary else 'None'}...")
    print(f"   AI Tags: {row.ai_tags}")
    print(f"   AI Confidence: {row.ai_confidence}")
    print(f"   Timestamp: {row.timestamp}")

print("\n" + "=" * 80)
