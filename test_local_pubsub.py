"""
Local End-to-End Test for Pub/Sub Integration
Tests the full flow: Publish -> Worker -> BigQuery
"""
import os
import sys
import json
import time
from datetime import datetime
from google.cloud import pubsub_v1, bigquery

# Configuration
PROJECT_ID = "qwiklabs-gcp-00-4a7d408c735c"
TOPIC_NAME = "community-reports-submitted"
SUBSCRIPTION_NAME = "bigquery-writer-sub"
BIGQUERY_TABLE = f"{PROJECT_ID}.CrowdsourceData.CrowdSourceData"

print("=" * 80)
print("🧪 LOCAL PUB/SUB END-TO-END TEST")
print("=" * 80)

# Step 1: Create test report data
print("\n📝 Step 1: Creating test report...")
test_report_id = f"local-test-{int(time.time())}"
test_report = {
    "report_id": test_report_id,
    "report_type": "Air Quality",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "address": "789 Mission Street",
    "zip_code": "94103",
    "city": "San Francisco",
    "state": "CA",
    "county": "San Francisco",
    "severity": "High",
    "specific_type": "Smoke",
    "description": f"Local end-to-end test - {test_report_id}",
    "people_affected": "100+",
    "timeframe": "Current",
    "contact_name": "Local Test",
    "contact_email": "localtest@example.com",
    "contact_phone": "555-0000",
    "is_anonymous": False,
    "media_urls": [],
    "media_count": 0,
    "attachment_urls": "[]",
    "ai_media_summary": None,
    "ai_overall_summary": f"Local test report {test_report_id}",
    "ai_tags": '["test", "local", "air_quality"]',
    "ai_confidence": 0.99,
    "ai_analyzed_at": datetime.utcnow().isoformat() + "Z",
    "status": "pending",
    "reviewed_by": None,
    "reviewed_at": None,
    "exclude_from_analysis": False,
    "exclusion_reason": None,
    "manual_tags": None,
    "notes": "Local test",
    "latitude": 37.7790,
    "longitude": -122.4190
}

print(f"✅ Created test report: {test_report_id}")
print(f"   Type: {test_report['report_type']}")
print(f"   Severity: {test_report['severity']}")
print(f"   Location: {test_report['city']}, {test_report['state']}")

# Step 2: Publish to Pub/Sub
print(f"\n📤 Step 2: Publishing to Pub/Sub topic '{TOPIC_NAME}'...")
try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
    
    message_json = json.dumps(test_report)
    message_bytes = message_json.encode('utf-8')
    
    future = publisher.publish(topic_path, message_bytes)
    message_id = future.result(timeout=10)
    
    print(f"✅ Message published successfully!")
    print(f"   Message ID: {message_id}")
    print(f"   Topic: {topic_path}")
    
except Exception as e:
    print(f"❌ Failed to publish message: {e}")
    sys.exit(1)

# Step 3: Wait for worker to process
print(f"\n⏳ Step 3: Waiting for worker to process (15 seconds)...")
for i in range(15, 0, -1):
    print(f"   Waiting... {i}s", end="\r")
    time.sleep(1)
print(f"   Done waiting!              ")

# Step 4: Check if message was processed
print(f"\n🔍 Step 4: Checking if message is still in queue...")
try:
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_NAME)
    
    # Try to pull (without ack) to see if message is still there
    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": 10,
        },
        timeout=5
    )
    
    found_our_message = False
    for msg in response.received_messages:
        data = json.loads(msg.message.data.decode('utf-8'))
        if data.get('report_id') == test_report_id:
            found_our_message = True
            # Don't ack - let worker handle it
            print(f"⚠️  Message still in queue (worker may be processing)")
            break
    
    if not found_our_message and len(response.received_messages) == 0:
        print(f"✅ Message not in queue (likely processed by worker)")
    elif not found_our_message:
        print(f"✅ Our message not in queue ({len(response.received_messages)} other messages present)")
    
except Exception as e:
    print(f"⚠️  Could not check queue: {e}")

# Step 5: Query BigQuery to verify data
print(f"\n🔍 Step 5: Querying BigQuery to verify data...")
try:
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
        report_id,
        timestamp,
        city,
        state,
        severity,
        description
    FROM `{BIGQUERY_TABLE}`
    WHERE report_id = '{test_report_id}'
    LIMIT 1
    """
    
    query_job = bq_client.query(query)
    results = list(query_job.result())
    
    if len(results) > 0:
        row = results[0]
        print(f"✅ Data found in BigQuery!")
        print(f"   Report ID: {row.report_id}")
        print(f"   Timestamp: {row.timestamp}")
        print(f"   Location: {row.city}, {row.state}")
        print(f"   Severity: {row.severity}")
        print(f"   Description: {row.description}")
        
        print(f"\n{'='*80}")
        print(f"🎉 END-TO-END TEST: SUCCESS!")
        print(f"{'='*80}")
        print(f"\nFlow verified:")
        print(f"  1. ✅ Published to Pub/Sub")
        print(f"  2. ✅ Worker received message")
        print(f"  3. ✅ Data inserted into BigQuery")
        print(f"  4. ✅ Data queryable in BigQuery")
        print(f"\nThe Pub/Sub integration is working correctly! 🚀")
        
    else:
        print(f"❌ Data NOT found in BigQuery!")
        print(f"\n🔍 Troubleshooting steps:")
        print(f"  1. Check worker logs:")
        print(f"     gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND textPayload:{test_report_id}\" --limit 10")
        print(f"\n  2. Check for errors:")
        print(f"     gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND severity>=ERROR\" --limit 10 --freshness=5m")
        print(f"\n  3. Wait longer and re-query BigQuery (worker might be slow)")
        print(f"\n  4. Check if worker is running:")
        print(f"     gcloud run services describe bigquery-worker --region us-central1")
        
except Exception as e:
    print(f"❌ BigQuery query failed: {e}")
    print(f"\nThis might be a permissions issue or the table doesn't exist.")

print(f"\n{'='*80}")
print(f"Test completed at {datetime.utcnow().isoformat()}Z")
print(f"{'='*80}\n")

