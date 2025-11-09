# 🚀 READY TO DEPLOY!

## ✅ All Pre-Deployment Checks Passed

```
✓ Pub/Sub topic exists
✓ Pub/Sub subscription exists
✓ Worker is running and healthy
✓ Code syntax is valid
✓ pubsub_services imports correctly
✓ google-cloud-pubsub in requirements.txt
✓ Current service exists and is accessible
```

---

## 🚀 Deploy Command

Run this command to deploy the updated application with Pub/Sub enabled:

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

- **Build**: 10-20 minutes (may timeout, retry if needed)
- **Deploy**: 1-2 minutes
- **Total**: ~15-25 minutes

---

## ⚠️ Important Notes

1. **Build May Timeout**: This is common with large codebases. If it times out, simply run the command again.

2. **Alternative Fast Deploy**: If the build keeps timing out, you can update just the environment variable on the existing image:
   ```powershell
   gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=true"
   ```
   This takes ~30 seconds but won't include new code changes.

3. **What Gets Deployed**:
   - ✅ All Pub/Sub code changes
   - ✅ `pubsub_services` package
   - ✅ Updated `app_local.py`
   - ✅ Updated `requirements.txt`
   - ✅ USE_PUBSUB=true environment variable

---

## ✅ After Deployment

### 1. Verify Service URL
```powershell
gcloud run services describe agent4good --region us-central1 --format="value(status.url)"
```

### 2. Test with Real Report
1. Visit the service URL
2. Submit a community report
3. Check response for `"message_id"` and `"processing": "async"`

### 3. Verify Worker Processed It
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bigquery-worker" --limit 10 --freshness=5m
```

### 4. Check BigQuery
Reports should appear in BigQuery within 15 seconds.

---

## 🔄 Rollback If Needed

```powershell
gcloud run services update agent4good --region us-central1 --update-env-vars="USE_PUBSUB=false"
```

---

## 🎉 You're Ready!

Copy and paste the deploy command above to start the deployment!

