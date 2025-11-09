# 🚀 Pub/Sub Deployment Commands for PowerShell

## Prerequisites Check

Run these commands first to verify your setup:

```powershell
# Check gcloud version
gcloud version

# Update to latest version
gcloud components update

# Verify authentication
gcloud auth list

# Verify project
gcloud config get-value project
```

Expected project: `qwiklabs-gcp-00-4a7d408c735c`

---

## 📋 Deployment Options

We have **two architecture options**. I recommend **Option 2 (Pull Worker)** for your use case.

### Option 1: Push Subscription (Simpler, Event-Driven)
Pub/Sub pushes messages directly to a Cloud Run HTTP endpoint.

**Pros:** Simple, no worker needed  
**Cons:** Less control, each message = 1 HTTP request

### Option 2: Pull Subscription (Recommended, Batch Processing)
Dedicated Cloud Run worker pulls messages from subscription.

**Pros:** Better throughput, batch processing, more control  
**Cons:** Slightly more complex

---

## 🎯 Option 2: Pull Subscription (RECOMMENDED)

This is what the MVP plan implements. Follow these steps:

### Step 1: Enable Required APIs (1 minute)

```powershell
gcloud services enable pubsub.googleapis.com run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

**What this does:** Enables Pub/Sub, Cloud Run, Cloud Build, and Artifact Registry APIs.

---

### Step 2: Create Pub/Sub Topic (30 seconds)

```powershell
gcloud pubsub topics create community-reports-submitted --project=qwiklabs-gcp-00-4a7d408c735c --message-retention-duration=7d
```

**What this does:** Creates a topic that will receive report messages. Messages retained for 7 days.

**Verify:**
```powershell
gcloud pubsub topics describe community-reports-submitted --project=qwiklabs-gcp-00-4a7d408c735c
```

---

### Step 3: Create Pull Subscription (30 seconds)

```powershell
gcloud pubsub subscriptions create bigquery-writer-sub --topic=community-reports-submitted --project=qwiklabs-gcp-00-4a7d408c735c --ack-deadline=60 --message-retention-duration=7d --expiration-period=never
```

**What this does:** Creates a subscription for the worker to pull messages from.
- `--ack-deadline=60`: Worker has 60 seconds to process and acknowledge message
- `--expiration-period=never`: Subscription doesn't expire

**Verify:**
```powershell
gcloud pubsub subscriptions describe bigquery-writer-sub --project=qwiklabs-gcp-00-4a7d408c735c
```

---

### Step 4: Grant IAM Permissions (1 minute)

```powershell
# Get the default compute service account
$SERVICE_ACCOUNT = "776464277441-compute@developer.gserviceaccount.com"

# Grant Pub/Sub Subscriber role (for pulling messages)
gcloud projects add-iam-policy-binding qwiklabs-gcp-00-4a7d408c735c --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/pubsub.subscriber"

# Grant Pub/Sub Publisher role (for main service to publish)
gcloud projects add-iam-policy-binding qwiklabs-gcp-00-4a7d408c735c --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/pubsub.publisher"

# Grant BigQuery Data Editor role (for worker to insert)
gcloud projects add-iam-policy-binding qwiklabs-gcp-00-4a7d408c735c --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/bigquery.dataEditor"
```

**What this does:** Grants permissions for:
- Main service to publish messages
- Worker to pull messages
- Worker to insert into BigQuery

**Verify:**
```powershell
gcloud projects get-iam-policy qwiklabs-gcp-00-4a7d408c735c --flatten="bindings[].members" --filter="bindings.members:$SERVICE_ACCOUNT"
```

---

### Step 5: Test Pub/Sub Setup (Manual Test - Optional)

```powershell
# Publish a test message
gcloud pubsub topics publish community-reports-submitted --message='{\"report_id\":\"test-001\",\"report_type\":\"health\",\"timestamp\":\"2025-01-01T00:00:00Z\",\"description\":\"Test report\"}' --project=qwiklabs-gcp-00-4a7d408c735c

# Pull the message to verify
gcloud pubsub subscriptions pull bigquery-writer-sub --auto-ack --limit=1 --project=qwiklabs-gcp-00-4a7d408c735c
```

**What this does:** Publishes a test message and verifies you can pull it.

**Expected output:** You should see the test message data.

---

### Step 6: Deploy BigQuery Worker (3-5 minutes)

**First, navigate to the workers directory:**
```powershell
cd workers
```

**Deploy the worker:**
```powershell
gcloud run deploy bigquery-worker --source . --platform managed --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c --no-allow-unauthenticated --memory 1Gi --cpu 1 --min-instances 1 --max-instances 10 --timeout 300 --set-env-vars="GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,SUBSCRIPTION_NAME=bigquery-writer-sub,BIGQUERY_DATASET=CrowdsourceData,BIGQUERY_TABLE_REPORTS=CrowdSourceData"
```

**What this does:** 
- Builds container from `workers/` directory
- Deploys to Cloud Run
- Sets min=1 instance (always running to process messages)
- Max=10 instances (auto-scales under load)
- Private service (no public access)

**Return to project root:**
```powershell
cd ..
```

**Monitor deployment:**
```powershell
gcloud run services describe bigquery-worker --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c
```

**Check worker logs:**
```powershell
gcloud run services logs read bigquery-worker --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c --limit 50
```

**Expected output:** You should see `[WORKER] Starting BigQuery Worker` and `[WORKER] Listening for messages...`

---

### Step 7: Update Main Service with Pub/Sub Support (3-5 minutes)

**Deploy updated main service with USE_PUBSUB=true:**

```powershell
gcloud run deploy agent4good --source . --platform managed --region us-central1 --allow-unauthenticated --memory 2Gi --cpu 2 --timeout 300 --max-instances 8 --min-instances 0 --set-env-vars="GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c,GEMINI_API_KEY=AIzaSyD-NH9KzOLmSKJmdqszwILplZs3kGL64eA,GOOGLE_API_KEY=AIzaSyD-NH9KzOLmSKJmdqszwILplZs3kGL64eA,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=us-central1,BIGQUERY_TABLE=air_quality_data,BIGQUERY_DATASET=CrowdsourceData,BIGQUERY_TABLE_REPORTS=CrowdSourceData,GCS_VIDEO_BUCKET=qwiklabs-gcp-00-4a7d408c735c-psa-videos,FLASK_ENV=production,SECRET_KEY=your-secret-key-here,AIRNOW_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,EPA_API_KEY=9C499E45-D997-4DC2-9337-B20B1E2EC659,AQS_API_KEY=bolewren34,AQS_EMAIL=ai2communities@gmail.com,FIREBASE_API_KEY=AIzaSyDTK4NBTDymbXtuRpNhbU9gDH1yX60JGw0,FIREBASE_AUTH_DOMAIN=qwiklabs-gcp-00-4a7d408c735c.firebaseapp.com,FIREBASE_PROJECT_ID=qwiklabs-gcp-00-4a7d408c735c,FIREBASE_STORAGE_BUCKET=qwiklabs-gcp-00-4a7d408c735c.firebasestorage.app,FIREBASE_MESSAGING_SENDER_ID=776464277441,FIREBASE_APP_ID=1:776464277441:web:f4faf70781e429a4671940,FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase-service-account,TWITTER_API_KEY=j1GPTU3weLMzs3PvIvj4nJmel,TWITTER_API_SECRET=FEpSdSCgsTJTSKByeXA9acbKLy9ACpTkoC84sJDbMPEURiRfnv,TWITTER_ACCESS_TOKEN=1982143243111497728-1oboZufxqKFp9Usr24MzehlqNWwIs6,TWITTER_ACCESS_TOKEN_SECRET=j3M73CcJgGfeT6xsYbtLUiZyNvXYOHFnYuPFxz7PptXUi,TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAAsb5AEAAAAASSxf2Ih%2B5%2FNAnlj7HluY22iF9YM%3DglqoGZDXONwArW7TCKuYgtNJIcrl70n7a9kjF03X61j8ZkMqBJ,TWITTER_USERNAME=AI_mmunity,USE_PUBSUB=true" --update-secrets="/secrets/firebase-service-account=firebase-service-account:latest"
```

**Key addition:** `USE_PUBSUB=true` enables Pub/Sub publishing.

---

### Step 8: Test End-to-End (5 minutes)

**1. Submit a test report via UI:**
- Go to https://agent4good-776464277441.us-central1.run.app
- Submit a community report

**2. Check main service logs:**
```powershell
gcloud run services logs read agent4good --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c --limit 20
```

**Look for:** `[PUBSUB] Published report {report_id} -> {message_id}`

**3. Check worker logs:**
```powershell
gcloud run services logs read bigquery-worker --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c --limit 20
```

**Look for:** 
- `[WORKER] Processing report {report_id}`
- `[BIGQUERY] Successfully inserted report {report_id}`
- `[SUCCESS] Report {report_id} processed in X.XXs`

**4. Verify in BigQuery:**
```powershell
bq query --use_legacy_sql=false "SELECT report_id, timestamp, description FROM \`qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData\` ORDER BY timestamp DESC LIMIT 5"
```

**Expected:** Your test report should appear in results.

---

## 🔄 Rollback Commands (If Needed)

### Disable Pub/Sub (keep infrastructure, revert to direct insert)

```powershell
gcloud run services update agent4good --region us-central1 --set-env-vars USE_PUBSUB=false
```

### Stop Worker (keeps queued messages)

```powershell
gcloud run services update bigquery-worker --region us-central1 --min-instances 0 --max-instances 0
```

### Full Teardown (removes everything)

```powershell
# Delete worker
gcloud run services delete bigquery-worker --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c --quiet

# Delete subscription
gcloud pubsub subscriptions delete bigquery-writer-sub --project qwiklabs-gcp-00-4a7d408c735c --quiet

# Delete topic
gcloud pubsub topics delete community-reports-submitted --project qwiklabs-gcp-00-4a7d408c735c --quiet
```

---

## 📊 Monitoring Commands

### Check Pub/Sub Metrics

```powershell
# Topic details
gcloud pubsub topics describe community-reports-submitted --project qwiklabs-gcp-00-4a7d408c735c

# Subscription details (shows unacked message count)
gcloud pubsub subscriptions describe bigquery-writer-sub --project qwiklabs-gcp-00-4a7d408c735c
```

### Check Worker Status

```powershell
# Service details
gcloud run services describe bigquery-worker --region us-central1 --project qwiklabs-gcp-00-4a7d408c735c

# Recent logs
gcloud run services logs read bigquery-worker --region us-central1 --limit 50

# Real-time logs (streaming)
gcloud run services logs tail bigquery-worker --region us-central1
```

### Check Message Queue

```powershell
# See how many messages are waiting
gcloud pubsub subscriptions describe bigquery-writer-sub --project qwiklabs-gcp-00-4a7d408c735c --format="value(numUndeliveredMessages)"
```

---

## 🎯 Alternative: Option 1 - Push Subscription (Simpler)

If you want to try the push approach instead (simpler, no worker needed):

### Create Push Subscription

```powershell
# First get the main service URL
$SERVICE_URL = gcloud run services describe agent4good --region us-central1 --format="value(status.url)"

# Create push subscription
gcloud pubsub subscriptions create bigquery-writer-push-sub --topic=community-reports-submitted --push-endpoint="$SERVICE_URL/api/pubsub-handler" --push-auth-service-account=776464277441-compute@developer.gserviceaccount.com --project qwiklabs-gcp-00-4a7d408c735c
```

**Note:** This requires adding a `/api/pubsub-handler` endpoint to `app_local.py` to receive push messages. The pull worker approach (Option 2) is more robust for your use case.

---

## 🐛 Troubleshooting

### Worker not processing messages

**Check logs:**
```powershell
gcloud run services logs read bigquery-worker --region us-central1 --limit 100
```

**Common issues:**
- Worker not started: Check if `min-instances=1`
- Permissions issue: Verify IAM roles granted
- Subscription misconfigured: Check subscription name matches

### Messages stuck in queue

**Check queue depth:**
```powershell
gcloud pubsub subscriptions describe bigquery-writer-sub --format="value(numUndeliveredMessages)"
```

**If messages piling up:**
- Check worker logs for errors
- Increase worker instances (max-instances)
- Check BigQuery table exists and is writable

### Main service not publishing

**Check logs:**
```powershell
gcloud run services logs read agent4good --region us-central1 --limit 50 | grep PUBSUB
```

**Common issues:**
- `USE_PUBSUB=false`: Check environment variable
- Publisher not initialized: Check for initialization errors
- Permissions: Verify publisher role granted

---

## 📈 Performance Tuning

### Scale Worker Up

```powershell
gcloud run services update bigquery-worker --region us-central1 --min-instances 2 --max-instances 20
```

### Adjust Ack Deadline (if processing takes longer)

```powershell
gcloud pubsub subscriptions update bigquery-writer-sub --ack-deadline=120
```

### Enable Message Batching (for higher throughput)

```powershell
gcloud pubsub subscriptions update bigquery-writer-sub --enable-message-ordering
```

---

## ✅ Success Checklist

After deployment, verify:

- [ ] Topic created: `gcloud pubsub topics list`
- [ ] Subscription created: `gcloud pubsub subscriptions list`
- [ ] IAM roles granted: Check with `gcloud projects get-iam-policy`
- [ ] Worker deployed: `gcloud run services list`
- [ ] Worker running: Check logs show "Listening for messages"
- [ ] Main service updated: Check env var `USE_PUBSUB=true`
- [ ] End-to-end test: Submit report, verify in BigQuery
- [ ] Performance: Response time < 500ms
- [ ] Reliability: No lost messages

---

## 📞 Support

**If you encounter issues:**

1. Check logs first (commands above)
2. Verify IAM permissions
3. Test Pub/Sub manually (Step 5)
4. Try rollback commands
5. Share error logs for debugging

**Common Error Messages:**

| Error | Solution |
|-------|----------|
| "Permission denied" | Check IAM roles (Step 4) |
| "Topic not found" | Verify topic name matches |
| "Subscription not found" | Run Step 3 again |
| "Worker not starting" | Check Dockerfile and requirements.txt |
| "Messages not being processed" | Check worker logs and min-instances |

---

## 🎉 Next Steps After Successful Deployment

Once working, you can:

1. **Add monitoring dashboards** in Cloud Console
2. **Set up alerts** for queue depth > 1000
3. **Implement Phase 2** (AI enrichment worker)
4. **Add more topics** for notifications, analytics
5. **Optimize costs** by adjusting min/max instances

---

**Ready to deploy? Start with Step 1!** 🚀

