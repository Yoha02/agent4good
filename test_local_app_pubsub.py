"""
Test the main application's Pub/Sub publishing logic locally
Simulates what happens when a user submits a report through the UI
"""
import os
import sys
import json
import time
from datetime import datetime

# Set environment variable to enable Pub/Sub
os.environ['USE_PUBSUB'] = 'true'
os.environ['GOOGLE_CLOUD_PROJECT'] = 'qwiklabs-gcp-00-4a7d408c735c'

print("=" * 80)
print("LOCAL APPLICATION PUB/SUB PUBLISHER TEST")
print("=" * 80)

# Import the pubsub_services package
try:
    from pubsub_services import USE_PUBSUB, publish_community_report
    print(f"\n[OK] Successfully imported pubsub_services")
    print(f"   USE_PUBSUB flag: {USE_PUBSUB}")
except ImportError as e:
    print(f"\n[ERROR] Failed to import pubsub_services: {e}")
    print(f"\nMake sure you're running from the project root directory:")
    print(f"  cd C:\\Users\\asggm\\Agents4Good\\agent4good")
    print(f"  python test_local_app_pubsub.py")
    sys.exit(1)

if not USE_PUBSUB:
    print(f"\n[WARNING] USE_PUBSUB is False!")
    print(f"   The code will work but won't actually publish to Pub/Sub")
    print(f"   Set environment variable: USE_PUBSUB=true")
else:
    print(f"   [OK] Pub/Sub is ENABLED")

# Create test report (same structure as app_local.py)
print(f"\n[INFO] Creating test report...")
test_report_id = f"app-local-test-{int(time.time())}"
report_data = {
    "report_id": test_report_id,
    "report_type": "Environmental",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "address": "100 Main Street",
    "zip_code": "94105",
    "city": "San Francisco",
    "state": "CA",
    "county": "San Francisco",
    "severity": "Medium",
    "specific_type": "Water Quality",
    "description": f"Testing app_local.py publisher - {test_report_id}",
    "people_affected": "50-100",
    "timeframe": "Last week",
    "contact_name": "App Test",
    "contact_email": "apptest@example.com",
    "contact_phone": "555-1111",
    "is_anonymous": False,
    "media_urls": [],
    "media_count": 0,
    "attachment_urls": "[]",
    "ai_media_summary": None,
    "ai_overall_summary": f"App local test {test_report_id}",
    "ai_tags": '["test", "app_local", "water"]',
    "ai_confidence": 0.95,
    "ai_analyzed_at": datetime.utcnow().isoformat() + "Z",
    "status": "pending",
    "reviewed_by": None,
    "reviewed_at": None,
    "exclude_from_analysis": False,
    "exclusion_reason": None,
    "manual_tags": None,
    "notes": "Local app test",
    "latitude": 37.7900,
    "longitude": -122.4000
}

print(f"[OK] Test report created:")
print(f"   Report ID: {test_report_id}")
print(f"   Type: {report_data['report_type']}")
print(f"   Description: {report_data['description']}")

# Test the publisher
print(f"\n[INFO] Testing publish_community_report()...")
try:
    message_id = publish_community_report(report_data)
    
    if message_id:
        print(f"[SUCCESS] Message published successfully!")
        print(f"   Message ID: {message_id}")
        print(f"   Report ID: {test_report_id}")
        
        print(f"\n{'='*80}")
        print(f"[SUCCESS] PUBLISHER TEST: SUCCESS!")
        print(f"{'='*80}")
        print(f"\nThe app_local.py publisher code is working correctly!")
        print(f"\nNext steps:")
        print(f"  1. Wait 10-15 seconds for worker to process")
        print(f"  2. Check worker logs:")
        print(f"     gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND textPayload:{test_report_id}\" --limit 10")
        print(f"  3. Query BigQuery to verify data:")
        print(f"     SELECT * FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData` WHERE report_id = '{test_report_id}'")
        
    else:
        print(f"[ERROR] Publishing failed - returned None")
        print(f"\nThis usually means:")
        print(f"  1. Pub/Sub client initialization failed")
        print(f"  2. Topic doesn't exist")
        print(f"  3. Permissions issue")
        print(f"\nCheck the error messages above for details.")
        
except Exception as e:
    print(f"[ERROR] Exception during publish: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print(f"Test completed at {datetime.utcnow().isoformat()}Z")
print(f"{'='*80}\n")

# Additional validation
print(f"[INFO] Validation Info:")
print(f"   Python version: {sys.version}")
print(f"   Working directory: {os.getcwd()}")
print(f"   USE_PUBSUB env var: {os.getenv('USE_PUBSUB', 'not set')}")
print(f"   GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'not set')}")

