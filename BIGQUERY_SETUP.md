# Multi-Source Health & Environmental Data - BigQuery Setup

## 📊 Overview

This system ingests data from 7 different sources into Google BigQuery:

1. **Wildfire Incidents** - InciWeb RSS feed
2. **Earthquakes** - USGS real-time Atom feed  
3. **Severe Weather** - NOAA Storm Prediction Center RSS
4. **NY State Health Data** - New York health metrics XML
5. **CDC COVID-19 Data** - CDC test positivity XML
6. **Drug Availability** - HealthData.gov GeoJSON
7. **Colorado Respiratory Infections** - ArcGIS Feature Server GeoJSON

## 🗄️ Database Schema

### Tables Created
- `data_sources` - Metadata about feed sources
- `data_items` - Main table with all fetched items
- `map_markers` - Map visualization data
- `health_metrics_timeseries` - Time-series health data
- `drug_availability` - Drug/medication availability

## 🚀 Setup Instructions

### Step 1: Install Dependencies

```bash
pip install -r requirements_bigquery.txt
```

### Step 2: Set up Google Cloud Project

1. Create a Google Cloud Project
2. Enable BigQuery API
3. Create a service account with BigQuery Admin role
4. Download service account JSON key
5. Set environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Step 3: Create BigQuery Dataset & Tables

```bash
# Using bq command-line tool
bq mk --dataset your-project-id:health_environmental_data

# Run the SQL DDL
bq query --use_legacy_sql=false < data/bigquery_schemas/create_tables.sql
```

Or use the BigQuery console to run `create_tables.sql` directly.

### Step 4: Load Initial Data Sources

```bash
# Load data sources metadata
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  your-project-id:health_environmental_data.data_sources \
  data/bigquery_schemas/data_sources.csv
```

### Step 5: Run Data Ingestion

```python
from multi_source_data_service import MultiSourceDataService

# Initialize service
service = MultiSourceDataService(
    project_id="your-project-id",
    dataset_id="health_environmental_data"
)

# Fetch all data sources
items = service.fetch_all_sources()

# Upload to BigQuery
service.upload_to_bigquery(items)
```

### Step 6: Set up Automated Refresh

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Refresh every 15 minutes
scheduler.add_job(
    func=service.fetch_all_sources,
    trigger="interval",
    minutes=15
)

scheduler.start()
```

## 📁 Files Created

```
data/bigquery_schemas/
├── data_sources.csv              # Feed sources metadata (for initial load)
├── data_items_schema.csv         # Schema definition for data_items table
├── map_markers_schema.csv        # Schema definition for map_markers table
└── create_tables.sql             # Complete DDL for all tables & views

multi_source_data_service.py      # Main ingestion service
requirements_bigquery.txt         # Additional Python dependencies
```

## 🔍 Sample Queries

### Get Recent Alerts

```sql
SELECT 
  title,
  event_type,
  severity,
  location_name,
  state_code,
  published_date
FROM `health_environmental_data.data_items`
WHERE is_active = TRUE
  AND severity IN ('critical', 'high')
  AND published_date >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY published_date DESC;
```

### Get Map Markers for California

```sql
SELECT 
  m.marker_type,
  m.latitude,
  m.longitude,
  m.marker_color,
  d.title,
  d.severity,
  d.published_date
FROM `health_environmental_data.map_markers` m
JOIN `health_environmental_data.data_items` d
  ON m.item_id = d.item_id
WHERE d.state_code = 'CA'
  AND d.is_active = TRUE;
```

### Get COVID Positivity Trends

```sql
SELECT 
  state_code,
  DATE(published_date) as date,
  AVG(health_value) as avg_positivity
FROM `health_environmental_data.data_items`
WHERE event_type = 'covid_metric'
  AND published_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY state_code, date
ORDER BY state_code, date;
```

### Get Drug Shortages

```sql
SELECT 
  drug_name,
  state_code,
  COUNT(*) as affected_facilities
FROM `health_environmental_data.data_items`
WHERE event_type = 'drug_availability'
  AND availability_status = 'unavailable'
GROUP BY drug_name, state_code
HAVING affected_facilities > 5
ORDER BY affected_facilities DESC;
```

## 🗺️ Integration with Flask App

Add to `app_local.py`:

```python
from multi_source_data_service import MultiSourceDataService

# Initialize BigQuery service
bq_service = MultiSourceDataService(
    project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
    dataset_id='health_environmental_data'
)

@app.route('/api/bigquery/alerts', methods=['GET'])
def get_bigquery_alerts():
    """Get alerts from BigQuery"""
    state = request.args.get('state')
    
    query = f"""
    SELECT * FROM `health_environmental_data.active_alerts`
    WHERE state_code = '{state}' OR state_code IS NULL
    LIMIT 100
    """
    
    results = bq_service.client.query(query).to_dataframe()
    return jsonify(results.to_dict('records'))

@app.route('/api/bigquery/map-data', methods=['GET'])
def get_bigquery_map_data():
    """Get map markers from BigQuery"""
    state = request.args.get('state', 'CA')
    
    query = f"""
    SELECT 
      m.marker_type,
      m.latitude,
      m.longitude,
      m.marker_color,
      m.marker_icon,
      d.title,
      d.severity,
      d.event_type
    FROM `health_environmental_data.map_markers` m
    JOIN `health_environmental_data.data_items` d
      ON m.item_id = d.item_id
    WHERE d.state_code = '{state}'
      AND d.is_active = TRUE
    """
    
    results = bq_service.client.query(query).to_dataframe()
    return jsonify(results.to_dict('records'))
```

## 📊 Data Flow

```
RSS/XML/GeoJSON Sources
         ↓
   Parser Functions
         ↓
  Standardized Items
         ↓
    BigQuery Tables
         ↓
   Flask API Endpoints
         ↓
  Frontend Map & Cards
```

## 🔧 Maintenance

### Update Data Sources

Modify `data/bigquery_schemas/data_sources.csv` and reload:

```bash
bq load --replace \
  --source_format=CSV \
  --skip_leading_rows=1 \
  your-project-id:health_environmental_data.data_sources \
  data/bigquery_schemas/data_sources.csv
```

### Archive Old Data

```sql
UPDATE `health_environmental_data.data_items`
SET is_archived = TRUE
WHERE published_date < DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
```

## 📈 Cost Optimization

- Data is partitioned by `published_date` for efficient queries
- Tables are clustered by frequently queried fields
- Expired data is automatically archived after 30 days
- Query only necessary columns to reduce costs

## 🆘 Troubleshooting

**Error: Permission denied**
- Ensure service account has BigQuery Data Editor role

**Error: Table not found**
- Run `create_tables.sql` to create schema

**Error: Feed parsing failed**
- Check feed URL is accessible
- Verify XML/JSON structure matches parser expectations

## 📝 Notes

- All timestamps are in UTC
- Coordinates are in WGS84 (latitude/longitude)
- GeoJSON data uses BigQuery GEOGRAPHY type for spatial queries
- Auto-refresh runs every 15 minutes (configurable)
