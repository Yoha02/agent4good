"""
Test submitting a report to see what errors occur
"""
from google.cloud import bigquery
import os
import json
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
dataset_id = os.getenv('BIGQUERY_DATASET')
table_id = os.getenv('BIGQUERY_TABLE_REPORTS')

print(f"Testing insert to: {project_id}.{dataset_id}.{table_id}")
print("=" * 80)

# Create test data with AI fields
test_data = {
    'report_id': 'test-ai-analysis-123',
    'report_type': 'water',
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'address': '123 Test St',
    'zip_code': '90210',
    'city': 'Beverly Hills',
    'state': 'CA',
    'county': 'Los Angeles',
    'severity': 'high',
    'specific_type': 'contamination',
    'description': 'Testing AI analysis fields',
    'people_affected': '5',
    'timeframe': 'current',
    'contact_name': 'Test User',
    'contact_email': 'test@example.com',
    'contact_phone': '555-1234',
    'is_anonymous': False,
    'media_urls': ['https://storage.googleapis.com/test/image.jpg'],  # REPEATED = array
    'media_count': 1,
    'attachment_urls': json.dumps(['https://storage.googleapis.com/test/image.jpg']),  # STRING = JSON
    'ai_media_summary': 'Test media summary',
    'ai_overall_summary': 'This is a test summary of the report',
    'ai_tags': json.dumps(['valid', 'urgent', 'contact_required']),  # STRING = JSON
    'ai_confidence': 0.85,
    'ai_analyzed_at': datetime.utcnow().isoformat() + 'Z',
    'status': 'Valid - Action Required',
    'reviewed_by': None,
    'reviewed_at': None,
    'exclude_from_analysis': None,
    'exclusion_reason': None,
    'manual_tags': None,
    'notes': None,
    'latitude': None,
    'longitude': None
}

try:
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    
    print("Test data:")
    for key, value in test_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    print("\n" + "=" * 80)
    print("Attempting insert...")
    
    errors = client.insert_rows_json(table_ref, [test_data])
    
    if errors:
        print("\n❌ INSERT FAILED!")
        print("-" * 80)
        for error in errors:
            print(f"\nError for row {error.get('index', 'unknown')}:")
            if 'errors' in error:
                for e in error['errors']:
                    print(f"  Field: {e.get('location', 'unknown')}")
                    print(f"  Reason: {e.get('reason')}")
                    print(f"  Message: {e.get('message')}")
    else:
        print("\n✅ INSERT SUCCESS!")
        
        # Verify
        query = f"""
        SELECT report_id, ai_overall_summary, ai_tags, ai_confidence, status
        FROM `{table_ref}`
        WHERE report_id = 'test-ai-analysis-123'
        """
        results = client.query(query).result()
        for row in results:
            print(f"\nVerified in BigQuery:")
            print(f"  Report ID: {row.report_id}")
            print(f"  AI Summary: {row.ai_overall_summary}")
            print(f"  AI Tags: {row.ai_tags}")
            print(f"  AI Confidence: {row.ai_confidence}")
            print(f"  Status: {row.status}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
