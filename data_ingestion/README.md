# External Data Ingestion

This directory contains scripts to fetch data from external RSS, XML, and GeoJSON feeds and load them into BigQuery.

## Data Sources

### 1. Wildfire Incidents
- **Source**: InciWeb RSS Feed
- **Table**: `wildfire_incidents`
- **Update Frequency**: Real-time
- **Data**: Active wildfire incidents across the US

### 2. Earthquake Events
- **Source**: USGS GeoJSON Feed
- **Table**: `earthquake_events`
- **Update Frequency**: Real-time
- **Data**: Significant earthquakes (M4.5+ in past week)

### 3. Storm Reports
- **Source**: NOAA Storm Prediction Center
- **Table**: `storm_reports`
- **Update Frequency**: Real-time
- **Data**: Tornado, hail, and wind reports

### 4. Air Quality Data
- **Source**: EPA AirNow API
- **Table**: `air_quality_data`
- **Update Frequency**: Hourly
- **Data**: Air quality measurements for major US cities

## Setup

### 1. Install Dependencies
```bash
pip install feedparser xmltodict requests google-cloud-bigquery
```

### 2. Create BigQuery Tables
```bash
python data_ingestion/create_tables.py
```

This will create all necessary tables in your BigQuery dataset.

### 3. Fetch Data
```bash
python data_ingestion/fetch_external_feeds.py
```

This will fetch data from all sources and insert into BigQuery.

## Automation

To keep data fresh, schedule the fetch script to run periodically:

### Using Cloud Scheduler (Recommended for Production)
1. Deploy `fetch_external_feeds.py` as a Cloud Function
2. Create a Cloud Scheduler job to trigger it hourly

### Using Cron (Local/VM)
```bash
# Add to crontab to run every hour
0 * * * * cd /path/to/agent4good && /path/to/venv/bin/python data_ingestion/fetch_external_feeds.py
```

### Using Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., hourly)
4. Action: Start a program
5. Program: `C:\Users\semaa\agent4good\.venv\Scripts\python.exe`
6. Arguments: `C:\Users\semaa\agent4good\data_ingestion\fetch_external_feeds.py`

## Schema Files

All BigQuery table schemas are defined in `schemas/*.json`:

- `wildfire_incidents.json` - Wildfire data schema
- `earthquake_events.json` - Earthquake data schema  
- `storm_reports.json` - Storm report schema
- `air_quality_data.json` - Air quality measurement schema

## Querying the Data

Example BigQuery queries:

```sql
-- Recent earthquakes over magnitude 5.0
SELECT event_id, magnitude, location, event_time
FROM `CrowdsourceData.earthquake_events`
WHERE magnitude >= 5.0
ORDER BY event_time DESC
LIMIT 10;

-- Active wildfires by state
SELECT state, COUNT(*) as incident_count, SUM(acres_burned) as total_acres
FROM `CrowdsourceData.wildfire_incidents`
WHERE status = 'Active'
GROUP BY state
ORDER BY total_acres DESC;

-- Poor air quality areas
SELECT location, aqi, aqi_category, primary_pollutant
FROM `CrowdsourceData.air_quality_data`
WHERE aqi > 100
ORDER BY measurement_time DESC;
```

## Troubleshooting

### No data being fetched
- Check API keys in `.env` file
- Verify internet connection
- Check if feeds are currently active (wildfires may be empty in winter)

### BigQuery errors
- Verify `GOOGLE_CLOUD_PROJECT` and `BIGQUERY_DATASET` in `.env`
- Ensure tables exist (run `create_tables.py`)
- Check BigQuery quotas

### Rate limiting
- EPA API has rate limits
- USGS is generally unlimited
- Add delays between requests if needed
