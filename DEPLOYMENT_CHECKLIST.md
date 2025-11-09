# 🚀 Deployment Checklist - Pub/Sub Enabled Build

## ✅ Pre-Deployment Checklist

Before deploying the updated build, verify:

### 1. Infrastructure Ready
- [ ] Pub/Sub topic exists: `community-reports-submitted`
- [ ] Pub/Sub subscription exists: `bigquery-writer-sub`
- [ ] Worker is deployed and healthy: `bigquery-worker`
- [ ] IAM permissions are configured

**Verify:**
```powershell
# Check topic
gcloud pubsub topics describe community-reports-submitted

# Check subscription
gcloud pubsub subscriptions describe bigquery-writer-sub

# Check worker
gcloud run services describe bigquery-worker --region us-central1
```

### 2. Worker Status
- [ ] Worker is running (min 1 instance)
- [ ] Worker is healthy (health check passing)
- [ ] Worker has processed test messages successfully

**Verify:**
```powershell
# Check worker health
curl https://bigquery-worker-776464277441.us-central1.run.app/health

# Check recent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 5 --freshness=5m
```

### 3. Local Testing Complete
- [ ] Local Pub/Sub test passed (`test_local_app_pubsub.py`)
- [ ] Message was published successfully
- [ ] Worker processed test message
- [ ] Data appeared in BigQuery

**Verify:**
```powershell
python test_local_app_pubsub.py
# Should show: [SUCCESS] PUBLISHER TEST: SUCCESS!
```

### 4. Code Changes Ready
- [ ] `pubsub_services/` package is complete
- [ ] `workers/` directory is complete (already deployed)
- [ ] `app_local.py` has Pub/Sub integration
- [ ] `requirements.txt` includes `google-cloud-pubsub`
- [ ] No syntax errors or import issues

**Verify:**
```powershell
# Check for syntax errors
python -m py_compile app_local.py

# Check pubsub_services imports
python -c "from pubsub_services import USE_PUBSUB, publish_community_report; print('OK')"
```

### 5. Environment Configuration
- [ ] Know the project ID: `qwiklabs-gcp-00-4a7d408c735c`
- [ ] Know the region: `us-central1`
- [ ] Know the service name: `agent4good`
- [ ] Have necessary secrets configured

---

## 🚀 Deployment Process

### Option 1: Automated Deployment Script (Recommended)

```powershell
.\deploy_pubsub_enabled.ps1
```

This script will:
1. Show deployment configuration
2. Ask for confirmation
3. Deploy updated code with Pub/Sub enabled
4. Show success message with verification steps

### Option 2: Manual Deployment

```powershell
gcloud run deploy agent4good `
  --source . `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 4Gi `
  --cpu 2 `
  --timeout 300 `
  --min-instances 0 `
  --max-instances 10 `
  --set-env-vars="USE_PUBSUB=true,GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,BIGQUERY_PROJECT_ID=qwiklabs-gcp-00-4a7d408c735c,BIGQUERY_DATASET_ID=CrowdsourceData,BIGQUERY_TABLE_NAME_COMMUNITY_REPORTS=CrowdSourceData,FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase-service-account" `
  --update-secrets="/secrets/firebase-service-account=firebase-service-account:latest"
```

---

## ⏱️ Expected Timeline

- **Build Time**: 5-15 minutes (may timeout on first try, retry if needed)
- **Deployment**: 1-2 minutes
- **Total**: ~10-20 minutes

---

## ✅ Post-Deployment Verification

### 1. Check Service Status

```powershell
# Get service URL
gcloud run services describe agent4good --region us-central1 --format="value(status.url)"

# Check service is ready
gcloud run services describe agent4good --region us-central1 --format="value(status.conditions)"
```

**Expected**: Service URL and status "Ready"

### 2. Verify Environment Variables

```powershell
gcloud run services describe agent4good --region us-central1 --format="value(spec.template.spec.containers[0].env)" | findstr USE_PUBSUB
```

**Expected**: `'name': 'USE_PUBSUB', 'value': 'true'`

### 3. Test with Real Report Submission

1. Visit the service URL
2. Navigate to "Report an Issue"
3. Fill out and submit a test report
4. Check the response for `"processing": "async"` and `"message_id": "..."`

### 4. Verify Worker Processed It

Wait 10-15 seconds, then:

```powershell
# Check recent worker activity
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 10 --freshness=5m --format="table(timestamp,textPayload)"
```

**Expected**: Should see logs showing report processing and BigQuery insert

### 5. Check BigQuery

In Cloud Console, run:
```sql
SELECT report_id, timestamp, description, status
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
ORDER BY timestamp DESC
LIMIT 5
```

**Expected**: Latest reports should appear

---

## 🐛 Troubleshooting

### Issue: Build Timeout

**Symptoms**: 
```
ERROR: gcloud crashed (WaitException)
```

**Solution**:
1. This is common with large codebases
2. Simply retry the deployment command
3. Cloud Build often succeeds on second attempt
4. Consider using existing image and just updating env vars:
   ```powershell
   gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=true"
   ```

### Issue: Service Unhealthy

**Symptoms**: Service shows "Not Ready" or errors in logs

**Solution**:
1. Check logs for errors:
   ```powershell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent4good AND severity>=ERROR" --limit 20
   ```
2. Check if `pubsub_services` package is importable
3. Verify `google-cloud-pubsub` is in `requirements.txt`

### Issue: Reports Not Being Published

**Symptoms**: Reports submitted but no Pub/Sub messages

**Solution**:
1. Verify `USE_PUBSUB=true` in service:
   ```powershell
   gcloud run services describe agent4good --region us-central1 --format="value(spec.template.spec.containers[0].env)"
   ```
2. Check application logs for Pub/Sub errors
3. Verify IAM permissions (publisher role)

### Issue: Worker Not Processing

**Symptoms**: Messages published but not processed

**Solution**:
1. Check worker is running:
   ```powershell
   gcloud run services describe bigquery-worker --region us-central1
   ```
2. Check worker logs for errors:
   ```powershell
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND severity>=ERROR" --limit 10
   ```
3. Verify subscription has no backlog:
   ```powershell
   gcloud pubsub subscriptions describe bigquery-writer-sub
   ```

---

## 🔄 Rollback Plan

If anything goes wrong, you can instantly rollback:

### Quick Rollback (Disable Pub/Sub):
```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false"
```

### Full Rollback (Previous Revision):
```powershell
# List revisions
gcloud run revisions list --service=agent4good --region=us-central1

# Rollback to previous revision
gcloud run services update-traffic agent4good --region=us-central1 --to-revisions=PREVIOUS_REVISION_NAME=100
```

**Impact**: System immediately reverts to direct BigQuery insert, no data loss

---

## 📊 Success Criteria

Deployment is successful when:

- [ ] Service deploys without errors
- [ ] Service URL is accessible
- [ ] `USE_PUBSUB=true` is set
- [ ] Test report can be submitted through UI
- [ ] Response includes `"message_id"` and `"processing": "async"`
- [ ] Worker logs show message processing
- [ ] Data appears in BigQuery within 15 seconds
- [ ] No errors in application or worker logs

---

## 📞 Quick Reference

```powershell
# Deploy
.\deploy_pubsub_enabled.ps1

# Check status
gcloud run services describe agent4good --region us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent4good" --limit 20 --freshness=5m

# Rollback
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false"

# Check worker
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 10 --freshness=5m
```

---

## 🎉 Ready to Deploy?

If all pre-deployment checks pass, run:

```powershell
.\deploy_pubsub_enabled.ps1
```

**Good luck!** 🚀

