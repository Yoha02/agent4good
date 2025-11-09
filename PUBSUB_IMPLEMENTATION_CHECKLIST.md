# 📋 Pub/Sub Implementation Checklist

## Quick Start Guide

### Prerequisites
- ✅ Cloud Run service deployed
- ✅ BigQuery dataset configured
- ✅ ADK agents working (11+ agents)
- ✅ GCP Project: `qwiklabs-gcp-00-4a7d408c735c`

---

## Phase 1: Infrastructure Setup (2 hours)

### Step 1.1: Create Pub/Sub Topics
```bash
cd deployment
./create_topics.sh
```

**Tasks:**
- [ ] Create `community-reports-submitted` topic
- [ ] Create `reports-ai-analysis` topic
- [ ] Create `reports-notification` topic
- [ ] Create `reports-analytics` topic
- [ ] Verify in Cloud Console

### Step 1.2: Create Subscriptions
```bash
./create_subscriptions.sh
```

**Tasks:**
- [ ] Create `bigquery-writer-sub` subscription
- [ ] Create `ai-enrichment-sub` subscription
- [ ] Create `notification-sub` subscription
- [ ] Create `analytics-sub` subscription
- [ ] Set appropriate ack deadlines
- [ ] Configure retry policies

### Step 1.3: Set IAM Permissions
```bash
./setup_iam.sh
```

**Tasks:**
- [ ] Grant `pubsub.publisher` to main service account
- [ ] Grant `pubsub.subscriber` to worker service accounts
- [ ] Grant `bigquery.dataEditor` to workers
- [ ] Verify permissions

### Step 1.4: Create Publisher Service
**Files to create:**
- [ ] `pubsub_services/__init__.py`
- [ ] `pubsub_services/publisher.py`
- [ ] `pubsub_services/message_schemas.py`
- [ ] `pubsub_services/subscriber_base.py`

**Test:**
```bash
python -m pytest tests/test_publisher.py
```

---

## Phase 2: BigQuery Worker (4 hours)

### Step 2.1: Create Worker Code
**Files to create:**
- [ ] `workers/__init__.py`
- [ ] `workers/bigquery_worker.py`
- [ ] `workers/base_worker.py`

### Step 2.2: Create Worker Dockerfile
- [ ] `Dockerfile.worker`
- [ ] `worker_requirements.txt`
- [ ] Test local build

### Step 2.3: Modify Main Service
**Update `app_local.py`:**
- [ ] Import publisher service
- [ ] Replace direct BigQuery insert with Pub/Sub publish
- [ ] Add `message_id` to response
- [ ] Keep CSV fallback for local testing
- [ ] Add feature flag: `USE_PUBSUB`

### Step 2.4: Deploy Worker
```bash
./deploy_workers.sh bigquery
```

**Tasks:**
- [ ] Build container image
- [ ] Push to Artifact Registry
- [ ] Deploy to Cloud Run
- [ ] Configure min/max instances
- [ ] Set environment variables
- [ ] Test with manual message

### Step 2.5: Test End-to-End
- [ ] Submit report via UI
- [ ] Check Pub/Sub topic for message
- [ ] Verify worker processes message
- [ ] Confirm BigQuery insert
- [ ] Check Cloud Logging for traces

---

## Phase 3: AI Enrichment Worker (4 hours)

### Step 3.1: Create Worker Code
**Files to create:**
- [ ] `workers/ai_enrichment_worker.py`
- [ ] Add Gemini integration
- [ ] Add BigQuery update logic

### Step 3.2: Deploy Worker
```bash
./deploy_workers.sh ai_enrichment
```

**Tasks:**
- [ ] Deploy to Cloud Run
- [ ] Set higher memory (2Gi)
- [ ] Configure Gemini API key
- [ ] Test with sample report

### Step 3.3: Update BigQuery Schema
**Add AI fields:**
- [ ] `ai_tags` (STRING)
- [ ] `ai_confidence` (FLOAT64)
- [ ] `ai_analyzed_at` (TIMESTAMP)
- [ ] `ai_severity_assessment` (STRING)

### Step 3.4: Test AI Pipeline
- [ ] Submit report
- [ ] Verify AI analysis runs
- [ ] Check BigQuery for updated fields
- [ ] Validate confidence scores

---

## Phase 4: Notification Worker (3 hours)

### Step 4.1: Create Worker Code
**Files to create:**
- [ ] `workers/notification_worker.py`
- [ ] Email template
- [ ] SMS integration (optional)

### Step 4.2: Integrate with Existing Systems
- [ ] PSA video generation trigger
- [ ] Twitter posting integration
- [ ] Dashboard alerts (Firebase)

### Step 4.3: Deploy Worker
```bash
./deploy_workers.sh notification
```

### Step 4.4: Test Notifications
- [ ] Submit critical report
- [ ] Verify email sent
- [ ] Check Twitter post
- [ ] Validate PSA video generation

---

## Phase 5: Multi-Agent Enhancement (4 hours)

### Step 5.1: Create New Agents
**Files to create:**
- [ ] `agents/pubsub_coordinator_agent.py`
- [ ] `agents/workflow_orchestrator_agent.py`

### Step 5.2: Add Agent Functions
- [ ] `publish_to_topic()`
- [ ] `check_queue_health()`
- [ ] `retry_failed_messages()`
- [ ] `start_workflow()`
- [ ] `check_workflow_status()`

### Step 5.3: Update Root Agent
**Update `agent.py`:**
- [ ] Import new agents
- [ ] Add to agent registry
- [ ] Update persona prompts
- [ ] Add event-driven context

### Step 5.4: Test Agent Communication
- [ ] Submit report
- [ ] Trace through all agents
- [ ] Verify messages between agents
- [ ] Check workflow completion

---

## Phase 6: Monitoring & Observability (2 hours)

### Step 6.1: Cloud Logging
- [ ] Add structured logging
- [ ] Log message IDs
- [ ] Log processing times
- [ ] Log errors with context

### Step 6.2: Cloud Monitoring
- [ ] Create Pub/Sub dashboard
- [ ] Create worker health dashboard
- [ ] Set up alerts (error rate > 5%)
- [ ] Set up alerts (queue depth > 1000)

### Step 6.3: Tracing
- [ ] Add correlation IDs
- [ ] Enable Cloud Trace
- [ ] Trace end-to-end workflows

---

## Phase 7: Testing & Validation (3 hours)

### Step 7.1: Unit Tests
- [ ] Test publisher
- [ ] Test message schemas
- [ ] Test worker processing logic
- [ ] Test agent functions

### Step 7.2: Integration Tests
- [ ] Test full pipeline
- [ ] Test error handling
- [ ] Test retry logic
- [ ] Test dead letter queue

### Step 7.3: Load Tests
- [ ] Submit 100 reports/sec
- [ ] Monitor worker scaling
- [ ] Check message latency
- [ ] Verify BigQuery throughput

### Step 7.4: Failure Tests
- [ ] Kill worker (test retry)
- [ ] Invalid message format
- [ ] BigQuery unavailable
- [ ] Gemini API timeout

---

## Phase 8: Documentation & Competition Submission (2 hours)

### Step 8.1: Update README
- [ ] Add Pub/Sub architecture diagram
- [ ] Document worker deployment
- [ ] Add monitoring guide

### Step 8.2: Create Demo Video
- [ ] Show report submission
- [ ] Show Pub/Sub messages
- [ ] Show worker processing
- [ ] Show agent communication
- [ ] Show scalability

### Step 8.3: Competition Submission
- [ ] Verify all requirements met
- [ ] Prepare architecture presentation
- [ ] Submit to competition
- [ ] Share deployment URL

---

## Rollback Plan

### If Issues Arise:
```bash
# 1. Switch back to direct BigQuery inserts
export USE_PUBSUB=false
gcloud run services update agent4good --set-env-vars USE_PUBSUB=false

# 2. Stop workers
gcloud run services delete bigquery-worker --region us-central1
gcloud run services delete ai-enrichment-worker --region us-central1
gcloud run services delete notification-worker --region us-central1

# 3. Keep Pub/Sub infrastructure (no cost for empty queues)
# Can re-enable later
```

---

## Timeline Summary

| Phase | Time | Cumulative |
|-------|------|------------|
| Phase 1: Infrastructure | 2 hours | 2 hours |
| Phase 2: BigQuery Worker | 4 hours | 6 hours |
| Phase 3: AI Enrichment | 4 hours | 10 hours |
| Phase 4: Notifications | 3 hours | 13 hours |
| Phase 5: Multi-Agent | 4 hours | 17 hours |
| Phase 6: Monitoring | 2 hours | 19 hours |
| Phase 7: Testing | 3 hours | 22 hours |
| Phase 8: Documentation | 2 hours | 24 hours |

**Total: 3 working days (8 hours/day)**

---

## Quick Commands Reference

### Check Pub/Sub Status
```bash
# List topics
gcloud pubsub topics list

# List subscriptions
gcloud pubsub subscriptions list

# Check message count
gcloud pubsub subscriptions describe bigquery-writer-sub

# Pull test message
gcloud pubsub subscriptions pull bigquery-writer-sub --limit=1
```

### Check Worker Status
```bash
# List services
gcloud run services list --region us-central1

# Get logs
gcloud run services logs read bigquery-worker --region us-central1

# Check metrics
gcloud run services describe bigquery-worker --region us-central1
```

### Publish Test Message
```bash
gcloud pubsub topics publish community-reports-submitted \
  --message='{"report_id": "test-123", "description": "Test report"}'
```

---

## Success Metrics

### Technical KPIs
- [ ] Report processing < 5 seconds (p95)
- [ ] Zero lost reports (100% reliability)
- [ ] 1000+ reports/sec throughput
- [ ] AI enrichment on 100% reports
- [ ] Critical alerts < 30 seconds

### Competition KPIs
- [ ] 13+ AI agents deployed
- [ ] Event-driven agent communication
- [ ] Cloud Run Service + Worker Pool
- [ ] 6+ Google Cloud services
- [ ] Production deployment live

---

## Next Steps

1. **Review this checklist** with the team
2. **Set up project tracking** (GitHub Issues, Jira, etc.)
3. **Assign tasks** to team members
4. **Start Phase 1** infrastructure setup
5. **Daily standups** to track progress

---

## Questions & Support

**Before starting:**
- Review `PUBSUB_INTEGRATION_PLAN.md` for detailed architecture
- Check GCP quotas for Pub/Sub and Cloud Run
- Ensure billing is enabled

**During implementation:**
- Use `#pubsub-integration` Slack channel
- Tag issues with `pubsub` label
- Refer to code samples in plan

**Deployment support:**
- Cloud Run docs: https://cloud.google.com/run/docs
- Pub/Sub docs: https://cloud.google.com/pubsub/docs
- ADK docs: https://github.com/google/adk

---

**Let's build this! 🚀**

