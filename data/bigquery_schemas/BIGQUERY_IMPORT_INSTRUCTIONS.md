# BigQuery Community Reports Table Setup

## Step 1: Create the Table in BigQuery

1. Go to your BigQuery console
2. Select your dataset
3. Click "Create Table"
4. Use the schema defined in `table_community_reports_schema.csv`

### SQL for Creating the Table

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
  media_urls ARRAY<STRING>,
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

## Step 2: Import Schema

You can also import the schema using the CSV file:
1. Click "Create Table"
2. Select "Upload" as source
3. Choose `table_community_reports_schema.csv`
4. Select "Schema" tab and use "Auto-detect" or paste the schema

## Step 3: Grant Permissions

Make sure your service account has these permissions:
- `bigquery.tables.create`
- `bigquery.tables.updateData`
- `bigquery.tables.getData`

## Step 4: Test with Sample Data

Use the sample data in `sample_community_reports.csv` to test your table.

## Data Dictionary

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| report_id | STRING | Yes | Unique UUID for each report |
| report_type | STRING | Yes | health, environmental, weather, emergency |
| timestamp | TIMESTAMP | Yes | When the report was submitted |
| address | STRING | Yes | Location of the incident |
| zip_code | STRING | Yes | 5-digit ZIP code |
| city | STRING | Yes | City name |
| state | STRING | Yes | 2-letter state code |
| severity | STRING | Yes | low, moderate, high, critical |
| specific_type | STRING | No | Detailed issue category |
| description | STRING | Yes | User's description of the issue |
| people_affected | STRING | No | Estimated number: 1, 2-5, 6-10, etc. |
| timeframe | STRING | Yes | now, 1hour, today, yesterday, week, ongoing |
| contact_name | STRING | No | Submitter's name (if provided) |
| contact_email | STRING | No | Submitter's email (if provided) |
| contact_phone | STRING | No | Submitter's phone (if provided) |
| is_anonymous | BOOL | Yes | Whether submitted anonymously |
| media_urls | ARRAY<STRING> | No | URLs to uploaded media files (max 10) |
| media_count | INT64 | No | Number of media files attached |
| status | STRING | Yes | pending, reviewed, resolved, closed |
| reviewed_by | STRING | No | Official's ID who reviewed |
| reviewed_at | TIMESTAMP | No | When it was reviewed |
| notes | STRING | No | Internal notes from officials |
| latitude | FLOAT64 | No | Geocoded latitude |
| longitude | FLOAT64 | No | Geocoded longitude |
