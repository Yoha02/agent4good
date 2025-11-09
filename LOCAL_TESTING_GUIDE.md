# 🧪 Local Testing Guide - Pub/Sub Integration

This guide walks you through testing the Pub/Sub integration from your local development environment.

---

## 📋 Prerequisites

1. **Google Cloud SDK** installed and authenticated
2. **Python 3.10+** with required packages
3. **Project credentials** configured

### Verify Prerequisites:
```powershell
# Check gcloud is authenticated
gcloud auth list

# Check Python version
python --version

# Check you're in the project directory
cd C:\Users\asggm\Agents4Good\agent4good
```

---

## 🧪 Test 1: Direct Pub/Sub Test (Low-Level)

This test directly publishes to Pub/Sub and verifies the worker processes it.

### Run the test:
```powershell
python test_local_pubsub.py
```

### Expected Output:
```
================================================================================
🧪 LOCAL PUB/SUB END-TO-END TEST
================================================================================

📝 Step 1: Creating test report...
✅ Created test report: local-test-1762690000

📤 Step 2: Publishing to Pub/Sub topic 'community-reports-submitted'...
✅ Message published successfully!
   Message ID: 16853352999999999

⏳ Step 3: Waiting for worker to process (15 seconds)...
   Done waiting!

🔍 Step 4: Checking if message is still in queue...
✅ Message not in queue (likely processed by worker)

🔍 Step 5: Querying BigQuery to verify data...
✅ Data found in BigQuery!
   Report ID: local-test-1762690000
   Timestamp: 2025-11-09 12:45:00+00:00
   Location: San Francisco, CA
   Severity: High

================================================================================
🎉 END-TO-END TEST: SUCCESS!
================================================================================
```

### What it tests:
- ✅ Pub/Sub topic is accessible
- ✅ Message can be published
- ✅ Worker receives and processes message
- ✅ Data is written to BigQuery
- ✅ Data is queryable

---

## 🧪 Test 2: Application Publisher Test (High-Level)

This test uses the actual `pubsub_services` package from `app_local.py`.

### Run the test:
```powershell
python test_local_app_pubsub.py
```

### Expected Output:
```
================================================================================
🧪 LOCAL APPLICATION PUB/SUB PUBLISHER TEST
================================================================================

✅ Successfully imported pubsub_services
   USE_PUBSUB flag: True
   ✅ Pub/Sub is ENABLED

📝 Creating test report...
✅ Test report created:
   Report ID: app-local-test-1762690100

📤 Testing publish_community_report()...
✅ Message published successfully!
   Message ID: 16853353111111111
   Report ID: app-local-test-1762690100

================================================================================
✅ PUBLISHER TEST: SUCCESS!
================================================================================
```

### What it tests:
- ✅ `pubsub_services` package is importable
- ✅ `USE_PUBSUB` feature flag works
- ✅ Publisher initialization works
- ✅ `publish_community_report()` function works
- ✅ Pydantic schema validation works

---

## 🧪 Test 3: Local Flask App Test (Full Stack)

Test submitting a report through the local Flask application.

### Step 1: Start the local app
```powershell
# Set environment variables
$env:USE_PUBSUB = "true"
$env:GOOGLE_CLOUD_PROJECT = "qwiklabs-gcp-00-4a7d408c735c"
$env:FLASK_ENV = "development"

# Start Flask
python app_local.py
```

### Step 2: Submit a test report

Open your browser to `http://localhost:8080` and:
1. Navigate to the "Report an Issue" page
2. Fill out the form
3. Submit the report

### Step 3: Check the Flask console output

Look for:
```
[PUBSUB] Report REPORT_ID queued: MESSAGE_ID
```

### Step 4: Verify in BigQuery

Wait 10-15 seconds, then run:
```sql
SELECT report_id, timestamp, description, status
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
WHERE report_id = 'YOUR_REPORT_ID'
```

---

## 🔧 Test 4: Feature Flag Test

Test that the feature flag properly enables/disables Pub/Sub.

### Test with Pub/Sub ENABLED:
```powershell
$env:USE_PUBSUB = "true"
python test_local_app_pubsub.py
```
**Expected**: Should publish to Pub/Sub

### Test with Pub/Sub DISABLED:
```powershell
$env:USE_PUBSUB = "false"
python test_local_app_pubsub.py
```
**Expected**: Should show "USE_PUBSUB is False" warning

---

## 🐛 Troubleshooting

### Issue 1: "Failed to import pubsub_services"

**Solution**: Make sure you're in the project root:
```powershell
cd C:\Users\asggm\Agents4Good\agent4good
python test_local_app_pubsub.py
```

### Issue 2: "google.cloud.pubsub module not found"

**Solution**: Install the required package:
```powershell
pip install google-cloud-pubsub==2.28.0
```

### Issue 3: "Permission denied" or "403 Forbidden"

**Solution**: Authenticate with gcloud:
```powershell
gcloud auth application-default login
```

### Issue 4: "Topic not found"

**Solution**: Verify the topic exists:
```powershell
gcloud pubsub topics describe community-reports-submitted
```

If it doesn't exist, create it:
```powershell
gcloud pubsub topics create community-reports-submitted
```

### Issue 5: "Data not appearing in BigQuery"

**Possible causes**:
1. Worker is not running
2. Worker has errors
3. IAM permissions issue

**Check worker status**:
```powershell
gcloud run services describe bigquery-worker --region us-central1
```

**Check worker logs**:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 20 --freshness=5m
```

### Issue 6: "Message stays in queue"

This means the worker isn't processing messages.

**Check subscription**:
```powershell
gcloud pubsub subscriptions describe bigquery-writer-sub
```

**Check worker logs for errors**:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND severity>=ERROR" --limit 10
```

---

## 📊 Verify Everything is Working

Run all tests in sequence:

```powershell
# Test 1: Direct Pub/Sub
python test_local_pubsub.py

# Wait 5 seconds
Start-Sleep -Seconds 5

# Test 2: Application publisher
python test_local_app_pubsub.py

# Check results in BigQuery
```

If all tests pass, your local environment is correctly configured! ✅

---

## 🧹 Cleanup Test Data

After testing, you may want to clean up test reports:

```sql
DELETE FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
WHERE report_id LIKE 'local-test-%'
   OR report_id LIKE 'app-local-test-%'
   OR report_id LIKE 'test-pubsub-%'
```

⚠️ **Warning**: This deletes data permanently!

---

## 📈 Performance Testing

Want to test how many messages the system can handle?

```python
# test_load.py
from google.cloud import pubsub_v1
import json
import time

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("qwiklabs-gcp-00-4a7d408c735c", "community-reports-submitted")

# Publish 100 messages
for i in range(100):
    data = {
        "report_id": f"load-test-{i}",
        "report_type": "Test",
        # ... other fields ...
    }
    future = publisher.publish(topic_path, json.dumps(data).encode('utf-8'))
    print(f"Published message {i+1}/100")

print("All messages published!")
```

Then monitor the worker to see how it handles the load.

---

## ✅ Success Criteria

All tests should:
- [ ] ✅ Publish messages successfully
- [ ] ✅ Worker processes messages within 5-15 seconds
- [ ] ✅ Data appears in BigQuery
- [ ] ✅ No errors in logs
- [ ] ✅ Feature flag works correctly
- [ ] ✅ Messages are removed from queue after processing

**If all criteria pass, your Pub/Sub integration is working correctly!** 🎉

---

## 📞 Quick Reference Commands

```powershell
# Run direct test
python test_local_pubsub.py

# Run app publisher test
python test_local_app_pubsub.py

# Check worker logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 10 --freshness=2m

# Query BigQuery for test data
# (Use Cloud Console or bq command)

# Check Pub/Sub queue
gcloud pubsub subscriptions pull bigquery-writer-sub --limit=5
```

---

**Happy Testing!** 🚀

