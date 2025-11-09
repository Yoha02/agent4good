# 📋 Pub/Sub Integration Verification Checklist

Use these commands to verify everything is working correctly:

## ✅ 1. Check Service Status

### Main Application:
```powershell
gcloud run services describe agent4good --region us-central1 --format="value(status.url,status.conditions)"
```
**Expected**: Service URL and status "Ready"

### Worker:
```powershell
gcloud run services describe bigquery-worker --region us-central1 --format="value(status.url,status.conditions)"
```
**Expected**: Service URL and status "Ready"

---

## ✅ 2. Verify Environment Variables

### Check USE_PUBSUB is enabled:
```powershell
gcloud run services describe agent4good --region us-central1 --format="value(spec.template.spec.containers[0].env)" | findstr USE_PUBSUB
```
**Expected**: `'name': 'USE_PUBSUB', 'value': 'true'`

### Check Worker Config:
```powershell
gcloud run services describe bigquery-worker --region us-central1 --format="value(spec.template.spec.containers[0].env)"
```
**Expected**: GOOGLE_CLOUD_PROJECT, SUBSCRIPTION_NAME, BIGQUERY_DATASET, BIGQUERY_TABLE_REPORTS

---

## ✅ 3. Test Worker Health

```powershell
curl https://bigquery-worker-776464277441.us-central1.run.app/health
```
**Expected**: `{"status":"healthy","messages_processed":N}`

---

## ✅ 4. Check Recent Worker Activity

```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 10 --format="table(timestamp,textPayload)"
```
**Expected**: Logs showing worker is listening and processing messages

---

## ✅ 5. Verify Pub/Sub Infrastructure

### Topic:
```powershell
gcloud pubsub topics describe community-reports-submitted
```
**Expected**: Topic details without errors

### Subscription:
```powershell
gcloud pubsub subscriptions describe bigquery-writer-sub
```
**Expected**: Subscription details, connected to topic

---

## ✅ 6. Check IAM Permissions

```powershell
gcloud projects get-iam-policy qwiklabs-gcp-00-4a7d408c735c --flatten="bindings[].members" --filter="bindings.members:776464277441-compute@developer.gserviceaccount.com" --format="table(bindings.role)"
```
**Expected**: Should include:
- `roles/pubsub.publisher`
- `roles/pubsub.subscriber`
- `roles/bigquery.dataEditor`

---

## ✅ 7. Test End-to-End (Optional)

Create a test script:
```python
# test_e2e.py
from google.cloud import pubsub_v1
import json

PROJECT_ID = "qwiklabs-gcp-00-4a7d408c735c"
TOPIC_NAME = "community-reports-submitted"

test_data = {
    "report_id": f"verify-{int(time.time())}",
    "report_type": "Air Quality",
    "timestamp": "2025-11-09T12:00:00Z",
    "city": "San Francisco",
    "state": "CA",
    "severity": "Low",
    "description": "Verification test",
    "is_anonymous": False,
    "media_count": 0,
    "status": "pending"
}

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_NAME)
future = publisher.publish(topic_path, json.dumps(test_data).encode('utf-8'))
print(f"Published: {future.result()}")
```

Then check logs:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND textPayload:verify-" --limit 5
```

---

## ✅ 8. Verify BigQuery Data

In Cloud Console:
1. Go to BigQuery
2. Navigate to `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
3. Run query:
```sql
SELECT report_id, timestamp, city, state, description
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
WHERE report_id LIKE 'test-pubsub%'
ORDER BY timestamp DESC
LIMIT 5
```
**Expected**: Should see test-pubsub-002 (and test-pubsub-001 if retried)

---

## 🔄 Rollback Commands (If Needed)

### Disable Pub/Sub:
```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false"
```

### Stop Worker (scale to 0):
```powershell
gcloud run services update bigquery-worker --region us-central1 --min-instances=0 --max-instances=0
```

### Re-enable Worker:
```powershell
gcloud run services update bigquery-worker --region us-central1 --min-instances=1 --max-instances=10
```

---

## 📊 Monitoring Dashboard URLs

- **Cloud Run Services**: https://console.cloud.google.com/run?project=qwiklabs-gcp-00-4a7d408c735c
- **Pub/Sub Topics**: https://console.cloud.google.com/cloudpubsub/topic/list?project=qwiklabs-gcp-00-4a7d408c735c
- **BigQuery**: https://console.cloud.google.com/bigquery?project=qwiklabs-gcp-00-4a7d408c735c
- **Logs Explorer**: https://console.cloud.google.com/logs/query?project=qwiklabs-gcp-00-4a7d408c735c

---

## ✅ Success Criteria

All checks should pass:
- [ ] Main service is running with USE_PUBSUB=true
- [ ] Worker is healthy and listening
- [ ] Pub/Sub topic and subscription exist
- [ ] IAM permissions are correct
- [ ] Test message was processed successfully
- [ ] Data appears in BigQuery
- [ ] No errors in logs

**If all criteria pass, the integration is working correctly!** ✅

