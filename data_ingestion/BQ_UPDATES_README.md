# BigQuery Data Ingestion Updates

## Summary
Updated all CDC data sources to use the most recent datasets and created a new table for respiratory disease rates tracking.

## Changes Made

### 1. CDC COVID Data Source Update ✅
**File:** `fetch_external_feeds.py`

**Old Source:** XML endpoint (outdated)
- `https://data.cdc.gov/api/views/gvsb-yw6g/rows.xml?accessType=DOWNLOAD`

**New Source:** CSV endpoint (current, within 1 month)
- `https://data.cdc.gov/api/v3/views/6jg4-xsqq/query.csv`

**Changes:**
- Switched from XML parsing to CSV parsing
- Updated data schema to match new endpoint
- Improved date handling with proper ISO format conversion
- Limited to 1000 most recent records for efficiency

**BigQuery Table:** `cdc_covid_data`

---

### 2. NREVSS Data Source Update ✅
**File:** `fetch_cdc_nrevss.py`

**Old Source:** JSON endpoint
- `https://data.cdc.gov/resource/52kb-ccu2.json`

**New Source:** CSV endpoint (current, within 1 month)
- `https://data.cdc.gov/resource/3cxc-4k8q.csv`

**Changes:**
- Switched from JSON to CSV parsing
- Updated field mappings for new data structure:
  - `rsv_detections` → `rsvpos`
  - `total_specimens` → `rsvtest`
  - `week_ending_date` → `date_string`
  - `virus_type` → `testtype`
- Maintains weekly schedule (already configured)

**BigQuery Table:** `nrevss_respiratory_data`

---

### 3. New Respiratory Disease Rates Table ✅
**New File:** `fetch_respiratory_rates.py`

**Data Source:**
- Dataset: Rates of Laboratory-Confirmed RSV, COVID-19, and Flu
- API: `https://data.cdc.gov/resource/kvib-3txy.json`
- CDC Page: https://data.cdc.gov/Public-Health-Surveillance/Rates-of-Laboratory-Confirmed-RSV-COVID-19-and-Flu/kvib-3txy

**Features:**
- Tracks RSV, COVID-19, and Influenza rates per 100,000 population
- Includes confidence intervals (upper/lower CI)
- Geographic breakdown available
- Age category stratification
- Cumulative rates tracking

**BigQuery Schema:**
```sql
CREATE TABLE respiratory_disease_rates (
  record_id STRING NOT NULL,
  season STRING,
  mmwryear INTEGER,
  mmwrweek INTEGER,
  weekendingdate STRING,
  week_end_date DATE,        -- Parsed date column from weekendingdate
  geography STRING,
  geography_type STRING,
  disease STRING,             -- 'RSV', 'COVID-19', or 'Influenza'
  age_category STRING,
  rate FLOAT,                 -- Rate per 100,000 population
  lower_ci FLOAT,
  upper_ci FLOAT,
  cumulative_rate FLOAT,
  load_timestamp TIMESTAMP NOT NULL
)
```

**Weekly Ingestion:**
- Scheduler: `setup_weekly_respiratory_schedule.ps1`
- Schedule: Every Monday at 3:00 AM
- Task Name: `CDC_Respiratory_Rates_Weekly_Ingestion`

**To Run Manually:**
```powershell
cd data_ingestion
python fetch_respiratory_rates.py
```

**To Setup Weekly Schedule:**
```powershell
cd data_ingestion
.\setup_weekly_respiratory_schedule.ps1
```

---

### 4. New API Endpoint ✅
**File:** `app_local.py`

**New Endpoint:** `/api/respiratory-disease-rates`

**Parameters:**
- `geography` (default: 'United States')
- `disease` ('RSV', 'COVID-19', 'Influenza', or 'all')
- `limit` (default: 52 weeks)

**Response:**
```json
{
  "data": [
    {
      "date": "2024-10-05",
      "disease": "RSV",
      "age_category": "Overall",
      "rate": 2.3,
      "lower_ci": 2.1,
      "upper_ci": 2.5,
      "cumulative_rate": 45.6,
      "year": 2024,
      "week": 40,
      "geography": "United States"
    }
  ],
  "geography": "United States",
  "disease": "all",
  "status": "success",
  "count": 156
}
```

---

### 5. New Interactive Chart ✅
**File:** `static/js/respiratory-disease-rates-chart.js`

**Features:**
- Interactive time series visualization for RSV, COVID-19, and Influenza
- Disease filtering (toggle diseases on/off)
- Date range slider (default: last 6 months)
- Rates displayed per 100,000 population
- Hover tooltips with detailed information
- Responsive design with smooth animations

**Usage in HTML:**
```html
<!-- Include Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Include the new chart script -->
<script src="{{ url_for('static', filename='js/respiratory-disease-rates-chart.js') }}"></script>

<!-- Add container -->
<div id="respiratoryDiseaseRatesChartContainer"></div>
```

**JavaScript API:**
```javascript
// Chart initializes automatically on page load

// Update geography programmatically
window.respiratoryDiseaseRatesChart.updateLocation('California');
```

---

## Data Freshness

All data sources are now configured to pull from datasets that are:
- ✅ Updated weekly by CDC
- ✅ Within the last month
- ✅ Using official CDC Socrata API endpoints

### Update Schedule

1. **NREVSS Data:** Already scheduled (existing schedule)
2. **Respiratory Rates:** Weekly (Mondays at 3 AM) - NEW
3. **COVID Data:** Runs with external feeds ingestion - UPDATED SOURCE

---

## Testing

### Test Individual Fetchers

```powershell
# Test COVID data fetcher
cd data_ingestion
python -c "from fetch_external_feeds import CDCCovidDataFetcher; f = CDCCovidDataFetcher(); data = f.fetch_data(); print(f'Fetched {len(data)} records')"

# Test NREVSS data fetcher
python fetch_cdc_nrevss.py

# Test respiratory rates fetcher
python fetch_respiratory_rates.py
```

### Test API Endpoint

```powershell
# Test in browser or with curl
curl "http://localhost:5000/api/respiratory-disease-rates?geography=United%20States&disease=all&limit=52"
```

### Verify BigQuery Tables

```sql
-- Check CDC COVID data
SELECT COUNT(*), MAX(created_at) as last_update
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`;

-- Check NREVSS data
SELECT COUNT(*), MAX(load_timestamp) as last_update
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`;

-- Check respiratory rates data
SELECT COUNT(*), MAX(load_timestamp) as last_update
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.respiratory_disease_rates`;
```

---

## Integration with Existing Dashboard

The new respiratory disease rates chart can be used alongside or replace the existing NREVSS chart:

### Current Chart (NREVSS)
- **Endpoint:** `/api/respiratory-timeseries`
- **Container:** `respiratoryChartContainer`
- **Script:** `respiratory-chart.js`
- **Shows:** RSV test positivity rates

### New Chart (Disease Rates)
- **Endpoint:** `/api/respiratory-disease-rates`
- **Container:** `respiratoryDiseaseRatesChartContainer`
- **Script:** `respiratory-disease-rates-chart.js`
- **Shows:** RSV, COVID-19, and Flu rates per 100k population

**Recommendation:** Use the new chart for the main infectious disease tracking as it provides:
1. Multiple diseases in one view
2. Standardized rates (per 100k population)
3. More recent, comprehensive data
4. Better filtering and interactivity

---

## Files Created/Modified

### New Files
- ✅ `data_ingestion/fetch_respiratory_rates.py` - Fetcher for new dataset
- ✅ `data_ingestion/setup_weekly_respiratory_schedule.ps1` - Weekly scheduler
- ✅ `static/js/respiratory-disease-rates-chart.js` - Interactive chart
- ✅ `data_ingestion/BQ_UPDATES_README.md` - This documentation

### Modified Files
- ✅ `data_ingestion/fetch_external_feeds.py` - Updated CDC COVID data source
- ✅ `data_ingestion/fetch_cdc_nrevss.py` - Updated NREVSS data source
- ✅ `app_local.py` - Added new API endpoint

---

## Next Steps

1. **Run Initial Data Load:**
   ```powershell
   cd data_ingestion
   python fetch_respiratory_rates.py
   ```

2. **Setup Weekly Schedule:**
   ```powershell
   .\setup_weekly_respiratory_schedule.ps1
   ```

3. **Verify Data in BigQuery:**
   - Check that the `respiratory_disease_rates` table exists
   - Verify data is populated with recent records

4. **Add Chart to Dashboard:**
   - Include the new JavaScript file in your HTML template
   - Add the container div where you want the chart
   - Test the interactive features

5. **Monitor Data Quality:**
   - Check logs for any errors
   - Verify weekly updates are running
   - Monitor data freshness in BigQuery

---

## Support

For issues or questions:
1. Check logs in the scheduled task (Task Scheduler on Windows)
2. Verify BigQuery table schemas match expectations
3. Test API endpoints directly in browser
4. Review CDC data source documentation for any API changes

## Data Sources Documentation

- **CDC COVID Data:** https://data.cdc.gov/Public-Health-Surveillance/United-States-COVID-19-Cases-and-Deaths-by-State-o/9mfq-cb36
- **NREVSS Data:** https://data.cdc.gov/Laboratory-Surveillance/Weekly-National-Respiratory-and-Enteric-Virus-Surv/3cxc-4k8q
- **Respiratory Rates:** https://data.cdc.gov/Public-Health-Surveillance/Rates-of-Laboratory-Confirmed-RSV-COVID-19-and-Flu/kvib-3txy
