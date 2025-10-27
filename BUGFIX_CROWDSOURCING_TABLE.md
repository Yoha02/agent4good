# Bugfix: Crowdsourcing Table Reference Error

## 🐛 Issue Found

**Error:**
```
google.api_core.exceptions.NotFound: 404 POST https://bigquery.googleapis.com/bigquery/v2/projects/qwiklabs-gcp-00-4a7d408c735c/datasets/CrowdsourceData/tables/air_quality_data/insertAll
Not found: Table qwiklabs-gcp-00-4a7d408c735c:CrowdsourceData.air_quality_data
```

**Root Cause:**
The `crowdsourcing_tool.py` was reading the table name from the environment variable `BIGQUERY_TABLE`, which is set to `air_quality_data` in the `.env` file (used by other parts of the app). This caused it to try inserting community reports into the wrong table.

---

## ✅ Fix Applied

**File:** `multi_tool_agent_bquery_tools/tools/crowdsourcing_tool.py`

**Before (Lines 99-101):**
```python
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
dataset_id = os.getenv("BIGQUERY_DATASET", "CrowdsourceData")
table_id = os.getenv("BIGQUERY_TABLE", "CrowdSourceData")  # ❌ Wrong - reads from env
```

**After (Lines 99-101):**
```python
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
dataset_id = "CrowdsourceData"  # ✅ Hardcoded
table_id = "CrowdSourceData"     # ✅ Hardcoded
```

**Why:** The crowdsourcing feature needs its own dedicated table (`CrowdSourceData`), not the air quality table.

---

## ⚠️ Prerequisites

Before the crowdsourcing feature will work, you need to create the BigQuery tables:

### Table 1: `CrowdsourceData.CrowdSourceData`

This table stores community health reports.

**Schema:**
```sql
CREATE TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData` (
  report_id STRING,
  report_type STRING,
  timestamp TIMESTAMP,
  address STRING,
  zip_code STRING,
  city STRING,
  state STRING,
  county STRING,
  severity STRING,
  specific_type STRING,
  description STRING,
  people_affected STRING,
  timeframe STRING,
  contact_name STRING,
  contact_email STRING,
  contact_phone STRING,
  is_anonymous BOOLEAN,
  media_urls ARRAY<STRING>,
  media_count INT64,
  ai_media_summary STRING,
  ai_overall_summary STRING,
  status STRING,
  reviewed_by STRING,
  reviewed_at TIMESTAMP,
  notes STRING,
  latitude FLOAT64,
  longitude FLOAT64,
  ai_tags STRING,
  ai_confidence FLOAT64,
  ai_analyzed_at TIMESTAMP,
  attachment_urls STRING,
  exclude_from_analysis BOOLEAN,
  exclusion_reason STRING,
  manual_tags STRING
);
```

### Table 2: `CrowdsourceData.ReportEmbeddings`

This table stores vector embeddings for semantic search.

**Schema:**
```sql
CREATE TABLE `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.ReportEmbeddings` (
  report_id STRING,
  city STRING,
  state STRING,
  county STRING,
  description STRING,
  severity STRING,
  report_type STRING,
  timestamp TIMESTAMP,
  contact_name STRING,
  contact_email STRING,
  contact_phone STRING,
  is_anonymous BOOLEAN,
  description_embedding ARRAY<FLOAT64>  -- 768 dimensions for text-embedding-004
);
```

---

## 🔧 Quick Setup Commands

### Option 1: Create Tables via BigQuery Console
1. Go to: https://console.cloud.google.com/bigquery
2. Select project: `qwiklabs-gcp-00-4a7d408c735c`
3. Create dataset: `CrowdsourceData`
4. Run the CREATE TABLE commands above

### Option 2: Create Tables via Command Line
```bash
# Create dataset
bq mk --dataset qwiklabs-gcp-00-4a7d408c735c:CrowdsourceData

# Create CrowdSourceData table (save schema to file first)
bq mk --table qwiklabs-gcp-00-4a7d408c735c:CrowdsourceData.CrowdSourceData schema_crowdsource.json

# Create ReportEmbeddings table
bq mk --table qwiklabs-gcp-00-4a7d408c735c:CrowdsourceData.ReportEmbeddings schema_embeddings.json
```

---

## 🧪 Testing After Fix

Once the tables are created, test the crowdsourcing feature:

**Test Query:**
```
"I want to report a health issue - I have a fever and cough in San Francisco"
```

**Expected Behavior:**
1. Agent asks for details (location, severity, etc.)
2. Collects information
3. Inserts into BigQuery `CrowdSourceData` table
4. Confirms submission: "✅ Your report has been logged..."

---

## 📝 Status

- ✅ **Fix Applied:** `crowdsourcing_tool.py` updated
- ⚠️ **Action Needed:** Create BigQuery tables before using crowdsourcing feature
- ✅ **Other Features:** All other features work normally (don't require these tables)

---

## 🎯 Summary

**What was broken:** Crowdsourcing agent tried to insert into wrong table  
**What was fixed:** Hardcoded correct table names  
**What's needed:** Create the BigQuery tables  
**Impact:** Only affects new crowdsourcing feature; all existing features work fine  

