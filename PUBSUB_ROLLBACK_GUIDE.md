# 🔄 Pub/Sub Integration - Rollback Guide

This guide provides step-by-step instructions for rolling back the Pub/Sub integration if needed.

---

## 📋 Rollback Scenarios

### Scenario 1: Disable Pub/Sub (Keep Worker Running)
**Use when**: You want to temporarily disable Pub/Sub but keep the worker available for future use.

### Scenario 2: Full Rollback (Stop Worker)
**Use when**: You want to completely disable Pub/Sub and save costs by stopping the worker.

### Scenario 3: Emergency Rollback
**Use when**: Critical issue detected, need immediate rollback.

---

## 🟡 Scenario 1: Disable Pub/Sub (Soft Rollback)

### Step 1: Disable Feature Flag
```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false"
```

**Result**: 
- Main app will use direct BigQuery insert (legacy mode)
- Worker continues running but won't receive new messages
- No code changes required
- Instant rollback (~10-30 seconds)

### Step 2: Verify Rollback
```powershell
# Check environment variable
gcloud run services describe agent4good --region us-central1 --format="value(spec.template.spec.containers[0].env)" | findstr USE_PUBSUB
```

**Expected output**: `'name': 'USE_PUBSUB', 'value': 'false'`

### Step 3: Check Application Logs
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent4good AND textPayload:PUBSUB" --limit 5 --freshness=5m
```

**Expected**: Should see logs indicating direct BigQuery insert (no Pub/Sub mentions)

### Impact:
- ✅ No data loss
- ✅ Users won't notice any difference
- ✅ Reports write directly to BigQuery
- ✅ Worker still running (costs ~$10-20/month)

---

## 🔴 Scenario 2: Full Rollback (Stop Worker)

### Step 1: Disable Feature Flag
```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false"
```

### Step 2: Scale Worker to Zero
```powershell
gcloud run services update bigquery-worker --region us-central1 --min-instances=0 --max-instances=0
```

**Result**: Worker stops, no instances running, minimal costs

### Step 3: (Optional) Delete Worker Completely
```powershell
gcloud run services delete bigquery-worker --region us-central1
```

⚠️ **Warning**: This deletes the worker service. You'll need to redeploy from code if you want to re-enable.

### Step 4: Verify Worker Stopped
```powershell
gcloud run services describe bigquery-worker --region us-central1 --format="value(spec.template.spec.containers[0].resources.limits)"
```

### Impact:
- ✅ No data loss
- ✅ Significant cost savings (worker stopped)
- ⚠️ Pub/Sub messages will queue if topic receives any messages
- ⚠️ Need to redeploy worker to re-enable

---

## 🚨 Scenario 3: Emergency Rollback

**Use when**: Critical issue detected, need immediate action.

### Quick Command (Copy/Paste):
```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false" ; gcloud run services update bigquery-worker --region us-central1 --min-instances=0 --max-instances=0
```

**This will**:
1. Disable Pub/Sub in main app (immediate effect)
2. Stop the worker (stop processing and costs)

### Verify:
```powershell
# Check main app
gcloud run services describe agent4good --region us-central1 --format="value(status.conditions[0].status)"

# Check worker stopped
gcloud run services describe bigquery-worker --region us-central1 --format="value(spec.template.spec.scaling)"
```

---

## 🔄 Re-Enable After Rollback

### From Soft Rollback (Scenario 1):
```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=true"
```

**Result**: Pub/Sub re-enabled immediately, worker already running.

### From Full Rollback (Scenario 2):

#### If Worker Still Exists (just scaled to 0):
```powershell
# Re-enable Pub/Sub
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=true"

# Restart worker
gcloud run services update bigquery-worker --region us-central1 --min-instances=1 --max-instances=10
```

#### If Worker Was Deleted:
```powershell
# Navigate to workers directory
cd C:\Users\asggm\Agents4Good\agent4good\workers

# Redeploy worker
gcloud run deploy bigquery-worker `
  --source . `
  --platform managed `
  --region us-central1 `
  --project qwiklabs-gcp-00-4a7d408c735c `
  --no-allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --min-instances 1 `
  --max-instances 10 `
  --timeout 300 `
  --set-env-vars="GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,SUBSCRIPTION_NAME=bigquery-writer-sub,BIGQUERY_DATASET=CrowdsourceData,BIGQUERY_TABLE_REPORTS=CrowdSourceData"

# Enable Pub/Sub
cd ..
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=true"
```

---

## 🧪 Test After Rollback

### Test Direct Insert (Pub/Sub Disabled):

1. Submit a test report through the web UI
2. Check logs for direct BigQuery insert:
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent4good AND textPayload:BigQuery" --limit 10 --freshness=5m
```

3. Verify data in BigQuery:
```sql
SELECT report_id, timestamp, description
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
ORDER BY timestamp DESC
LIMIT 5
```

**Expected**: Latest reports should appear immediately (no Pub/Sub processing delay)

---

## 📊 Monitoring During Rollback

### Check for Any Queued Messages:
```powershell
gcloud pubsub subscriptions describe bigquery-writer-sub --format="value(numUndeliveredMessages)"
```

**If messages are queued**: They will be processed when worker is restarted, or will expire based on retention policy.

### Check for Errors:
```powershell
# Main app errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent4good AND severity>=ERROR" --limit 10 --freshness=10m

# Worker errors (if still running)
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker AND severity>=ERROR" --limit 10 --freshness=10m
```

---

## 💰 Cost Implications

### With Pub/Sub Enabled:
- Main app: ~$50-100/month (unchanged)
- Worker (min 1 instance): ~$15-25/month
- Pub/Sub: ~$0.40/million messages (negligible)
- **Total added cost**: ~$15-25/month

### After Soft Rollback (USE_PUBSUB=false, worker running):
- Main app: ~$50-100/month
- Worker (idle but running): ~$15-25/month
- Pub/Sub: ~$0.10/million (minimal)
- **Savings**: None (worker still running)

### After Full Rollback (worker stopped):
- Main app: ~$50-100/month
- Worker: $0 (stopped)
- Pub/Sub: ~$0.10/million (storage only)
- **Savings**: ~$15-25/month

---

## 🔍 Troubleshooting Rollback Issues

### Issue: Main app still trying to use Pub/Sub after rollback

**Symptoms**: Logs show Pub/Sub errors even though USE_PUBSUB=false

**Solution**: 
1. Check environment variable was actually updated
2. Check if you're looking at old revision logs
3. Wait for new revision to receive traffic (can take 30-60 seconds)

```powershell
# Get current serving revision
gcloud run services describe agent4good --region us-central1 --format="value(status.traffic[0].revisionName)"

# Check that revision's env vars
gcloud run revisions describe REVISION_NAME --region us-central1 --format="value(spec.containers[0].env)"
```

### Issue: Reports not appearing in BigQuery after rollback

**Symptoms**: Users can submit but data doesn't appear

**Solution**:
1. Check if there are application errors
2. Verify BigQuery table exists
3. Check IAM permissions

```powershell
# Check for insert errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=agent4good AND (textPayload:BigQuery OR textPayload:insert)" --limit 20 --freshness=10m
```

### Issue: Worker won't stop

**Symptoms**: Worker continues running after scaling to 0

**Solution**:
```powershell
# Force delete all revisions
gcloud run revisions list --service=bigquery-worker --region=us-central1 --format="value(name)" | ForEach-Object { gcloud run revisions delete $_ --region=us-central1 --quiet }

# Then delete service
gcloud run services delete bigquery-worker --region us-central1 --quiet
```

---

## ✅ Rollback Checklist

Use this checklist when performing a rollback:

- [ ] **Before Rollback**:
  - [ ] Note current state (Pub/Sub enabled/disabled)
  - [ ] Check if any messages are queued
  - [ ] Document reason for rollback
  
- [ ] **During Rollback**:
  - [ ] Disable USE_PUBSUB flag
  - [ ] Verify environment variable changed
  - [ ] Check new revision is receiving traffic
  - [ ] (If full rollback) Stop or delete worker
  
- [ ] **After Rollback**:
  - [ ] Test report submission
  - [ ] Verify data in BigQuery
  - [ ] Check for errors in logs
  - [ ] Monitor for 15-30 minutes
  - [ ] Document completion and any issues

---

## 📞 Support Commands

### Get Current Configuration:
```powershell
# Main app status
gcloud run services describe agent4good --region us-central1 --format="value(status.url,status.conditions[0].status,spec.template.spec.containers[0].env)"

# Worker status
gcloud run services describe bigquery-worker --region us-central1 --format="value(status.url,status.conditions[0].status)" 2>$null
```

### Quick Health Check:
```powershell
# Main app responsive?
curl https://agent4good-776464277441.us-central1.run.app/

# Worker responsive? (if running)
curl https://bigquery-worker-776464277441.us-central1.run.app/health
```

---

## 📝 Rollback Decision Matrix

| Situation | Action | Command |
|-----------|--------|---------|
| Testing alternative approach | Soft rollback | `USE_PUBSUB=false` |
| Worker having issues | Soft rollback | `USE_PUBSUB=false` |
| Cost concerns | Full rollback | `USE_PUBSUB=false` + scale worker to 0 |
| Pub/Sub not needed anymore | Full rollback + delete | `USE_PUBSUB=false` + delete worker |
| Critical error | Emergency rollback | Both commands simultaneously |
| Temporary network issues | Wait 5-10 minutes | No action needed |

---

## 🎯 Summary

- **Soft Rollback**: Fast (30 seconds), reversible, worker keeps running
- **Full Rollback**: Saves costs, requires worker restart to re-enable
- **Emergency**: Immediate, disables everything
- **Re-enable**: Single command if worker exists, redeploy if deleted

**Remember**: With `USE_PUBSUB=false`, the system works exactly as before Pub/Sub integration - direct BigQuery inserts with no data loss or functional changes.

---

**Last Updated**: November 9, 2025  
**Status**: All rollback procedures tested and verified ✅

