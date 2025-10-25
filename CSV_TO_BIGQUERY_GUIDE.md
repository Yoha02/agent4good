# Community Reports CSV to BigQuery Guide

## Overview
When users submit a report through the `/report` page, the data is saved to `data/community_reports.csv`. You can then manually upload this CSV to BigQuery.

## Files Created

1. **`data/community_reports.csv`** - Contains all submitted reports (auto-generated when first report is submitted)
2. **`data/bigquery_schemas/table_community_reports_schema.csv`** - Schema definition for BigQuery table
3. **`data/bigquery_schemas/sample_community_reports.csv`** - Sample data for testing
4. **`data/bigquery_schemas/BIGQUERY_IMPORT_INSTRUCTIONS.md`** - Detailed setup instructions
5. **`data/report_uploads/{report_id}/`** - Uploaded media files organized by report ID

## Quick Start

### Step 1: Create BigQuery Table

```sql
CREATE TABLE `your-project-id.your-dataset.community_reports` (
  report_id STRING NOT NULL,
  report_type STRING NOT NULL,
  timestamp TIMESTAMP NOT NULL,
  address STRING NOT NULL,
  zip_code STRING NOT NULL,
  city STRING NOT NULL,
  state STRING NOT NULL,
  severity STRING NOT NULL,
  specific_type STRING,
  description STRING NOT NULL,
  people_affected STRING,
  timeframe STRING NOT NULL,
  contact_name STRING,
  contact_email STRING,
  contact_phone STRING,
  is_anonymous BOOL NOT NULL,
  media_urls STRING,
  media_count INT64,
  status STRING NOT NULL DEFAULT 'pending',
  reviewed_by STRING,
  reviewed_at TIMESTAMP,
  notes STRING,
  latitude FLOAT64,
  longitude FLOAT64
)
PARTITION BY DATE(timestamp)
CLUSTER BY state, severity, status;
```

### Step 2: Upload CSV to BigQuery

#### Option A: Using BigQuery Console
1. Go to BigQuery Console
2. Select your dataset
3. Click "Create Table"
4. Choose "Upload" as source
5. Select `data/community_reports.csv`
6. Select the destination table: `community_reports`
7. Schema: Auto-detect or use schema file
8. Click "Create Table"

#### Option B: Using bq CLI
```bash
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  your-dataset.community_reports \
  data/community_reports.csv
```

#### Option C: Using Python (Automated)
```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client()
table_id = "your-project-id.your-dataset.community_reports"

# Read CSV
df = pd.read_csv('data/community_reports.csv')

# Upload to BigQuery
job = client.load_table_from_dataframe(df, table_id)
job.result()  # Wait for completion

print(f"Loaded {job.output_rows} rows into {table_id}")
```

### Step 3: Query Your Data

```sql
-- Get all pending reports
SELECT * FROM `your-project-id.your-dataset.community_reports`
WHERE status = 'pending'
ORDER BY timestamp DESC;

-- Reports by severity
SELECT 
  severity,
  COUNT(*) as count,
  COUNT(DISTINCT state) as states_affected
FROM `your-project-id.your-dataset.community_reports`
GROUP BY severity
ORDER BY 
  CASE severity
    WHEN 'critical' THEN 1
    WHEN 'high' THEN 2
    WHEN 'moderate' THEN 3
    WHEN 'low' THEN 4
  END;

-- Recent reports with media
SELECT 
  report_id,
  report_type,
  severity,
  city,
  state,
  media_count,
  timestamp
FROM `your-project-id.your-dataset.community_reports`
WHERE media_count > 0
ORDER BY timestamp DESC
LIMIT 10;
```

## CSV Column Mapping

| CSV Column | BigQuery Column | Type | Description |
|------------|----------------|------|-------------|
| report_id | report_id | STRING | UUID generated for each report |
| report_type | report_type | STRING | health, environmental, weather, emergency |
| timestamp | timestamp | TIMESTAMP | ISO 8601 format with 'Z' suffix |
| address | address | STRING | Street address or landmark |
| zip_code | zip_code | STRING | 5-digit ZIP code |
| city | city | STRING | City name |
| state | state | STRING | 2-letter state code |
| severity | severity | STRING | low, moderate, high, critical |
| specific_type | specific_type | STRING | Detailed issue category |
| description | description | STRING | User's description |
| people_affected | people_affected | STRING | 1, 2-5, 6-10, 11-25, 26-50, 50+ |
| timeframe | timeframe | STRING | now, 1hour, today, yesterday, week, ongoing |
| contact_name | contact_name | STRING | Optional contact name |
| contact_email | contact_email | STRING | Optional email |
| contact_phone | contact_phone | STRING | Optional phone |
| is_anonymous | is_anonymous | BOOL | true/false |
| media_urls | media_urls | STRING | JSON array as string |
| media_count | media_count | INT64 | Number of files |
| status | status | STRING | pending, reviewed, resolved, closed |
| reviewed_by | reviewed_by | STRING | Official's ID |
| reviewed_at | reviewed_at | TIMESTAMP | Review timestamp |
| notes | notes | STRING | Internal notes |
| latitude | latitude | FLOAT64 | Geocoded latitude |
| longitude | longitude | FLOAT64 | Geocoded longitude |

## Automated Upload (Future Enhancement)

To automatically sync CSV to BigQuery, you can:

1. **Use Cloud Functions**: Trigger on CSV file changes
2. **Scheduled Jobs**: Run bq load command via cron
3. **Direct BigQuery Insert**: Modify backend to write directly to BigQuery instead of CSV

Example direct insert:
```python
from google.cloud import bigquery

def insert_report_to_bigquery(report_data):
    client = bigquery.Client()
    table_id = "your-project-id.your-dataset.community_reports"
    
    rows_to_insert = [report_data]
    errors = client.insert_rows_json(table_id, rows_to_insert)
    
    if errors:
        print(f"Errors: {errors}")
    else:
        print("Report inserted successfully")
```

## Media File Storage

Uploaded media files are saved to:
```
data/report_uploads/{report_id}/
  - photo1.jpg
  - photo2.jpg
  - video1.mp4
```

For production, upload these to:
- **Google Cloud Storage**: `gs://your-bucket/reports/{report_id}/`
- **AWS S3**: `s3://your-bucket/reports/{report_id}/`
- Then update `media_urls` column with cloud storage URLs

## Monitoring & Alerts

Set up BigQuery scheduled queries to:
- Alert on critical reports
- Generate daily summaries
- Track response times
- Monitor trends by location

Example scheduled query:
```sql
-- Daily critical reports summary
SELECT 
  DATE(timestamp) as report_date,
  state,
  COUNT(*) as critical_reports
FROM `your-project-id.your-dataset.community_reports`
WHERE severity = 'critical'
  AND status = 'pending'
  AND timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
GROUP BY report_date, state
ORDER BY critical_reports DESC;
```

## Next Steps

1. Create the BigQuery table using the SQL above
2. Test with sample data from `sample_community_reports.csv`
3. Submit a test report through the web form
4. Upload `data/community_reports.csv` to BigQuery
5. Set up automated uploads or direct BigQuery integration
6. Configure alerts for high-severity reports
