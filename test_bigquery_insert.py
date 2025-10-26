"""
Test BigQuery insertion to debug schema issues
"""
from google.cloud import bigquery
import os
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')

print(f"Testing insert to: {project_id}.{dataset_id}.{table_id}")
print("=" * 80)

try:
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    table = client.get_table(table_ref)
    
    print("CURRENT SCHEMA:")
    print("-" * 80)
    for field in table.schema:
        required = "REQUIRED" if field.mode == "REQUIRED" else "NULLABLE"
        print(f"  {field.name:30} {field.field_type:15} {required}")
    
    print("\n" + "=" * 80)
    print("TESTING INSERT:")
    print("=" * 80)
    
    # Create test data matching the schema
    test_data = {
        'report_id': 'test-12345',
        'report_type': 'water',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'address': '123 Test St',
        'zip_code': '90210',
        'city': 'Beverly Hills',
        'state': 'CA',
        'county': 'Los Angeles',
        'severity': 'medium',
        'specific_type': 'contamination',
        'description': 'Test report for debugging',
        'people_affected': '5',
        'timeframe': 'current',
        'contact_name': 'Test User',
        'contact_email': 'test@example.com',
        'contact_phone': '555-1234',
        'is_anonymous': False,
        'media_urls': '[]',  # STRING, not array
        'media_count': 0,
        'attachment_urls': None,
        'ai_media_summary': None,
        'ai_overall_summary': None,
        'ai_tags': None,
        'ai_confidence': None,
        'ai_analyzed_at': None,
        'status': 'pending',
        'reviewed_by': None,
        'reviewed_at': None,
        'exclude_from_analysis': None,
        'exclusion_reason': None,
        'manual_tags': None,
        'notes': None,
        'latitude': None,
        'longitude': None
    }
    
    print("Attempting to insert test row...")
    errors = client.insert_rows_json(table_ref, [test_data])
    
    if errors:
        print("\n❌ INSERT FAILED!")
        print("-" * 80)
        for error in errors:
            print(f"Error: {error}")
            if 'errors' in error:
                for e in error['errors']:
                    print(f"  - {e.get('reason')}: {e.get('message')}")
    else:
        print("\n✅ INSERT SUCCESS!")
        print(f"Test row inserted: {test_data['report_id']}")
        
        # Verify it's there
        print("\nVerifying...")
        query = f"""
        SELECT report_id, report_type, city, attachment_urls
        FROM `{table_ref}`
        WHERE report_id = 'test-12345'
        """
        results = client.query(query).result()
        for row in results:
            print(f"Found: {row.report_id} - {row.report_type} - {row.city}")
            print(f"Attachment URLs: {row.attachment_urls}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
