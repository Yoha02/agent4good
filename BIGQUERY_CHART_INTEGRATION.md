# Infectious Disease Chart - BigQuery Integration Complete

## What Was Changed

The infectious disease tracking chart now queries BigQuery **directly** using the newly populated CDC tables instead of external APIs.

## BigQuery Tables Used

### 1. **respiratory_disease_rates**
- Source: FluSurv-NET surveillance (kvib-3txy)
- Data: RSV, COVID-19, and Influenza hospitalization rates
- Latest: October 4, 2025
- Records: 15,000

### 2. **nrevss_respiratory_data**
- Source: National Respiratory and Enteric Virus Surveillance System (3cxc-4k8q)
- Data: PCR test positivity rates for respiratory viruses
- Latest: October 18, 2025
- Records: 10,000

### 3. **cdc_covid_hospitalizations**
- Source: CDC COVID-19 hospitalizations by demographics (6jg4-xsqq)
- Data: Weekly and cumulative hospitalization rates
- Latest: September 27, 2025
- Records: 15,000

## New API Endpoint

### `/api/infectious-disease-dashboard`

**Purpose:** Combined endpoint that queries all three BigQuery tables directly

**Parameters:**
- `state` (optional): Filter by state name
- `days` (optional, default: 30): Number of days of historical data

**Response Structure:**
```json
{
  "status": "success",
  "state": "National",
  "period_days": 30,
  "respiratory_rates": [...],
  "nrevss_data": [...],
  "covid_hospitalizations": [...],
  "summary": {
    "total_data_points": 150,
    "latest_update": "2025-10-18"
  }
}
```

## Updated Chart Features

### Main Chart (`respiratory-chart.js`)
**What Changed:**
- Switched from `/api/respiratory-timeseries` to `/api/infectious-disease-dashboard`
- Combines data from all three BigQuery tables
- Displays RSV (from NREVSS PCR data)
- Displays COVID-19 (from hospitalization rates)
- Displays Influenza (from respiratory disease rates)
- Chart header now shows "BigQuery Data" indicator

### Disease Cards
**What Changed:**
- Now pull real-time data from BigQuery tables
- **RSV Card:** Uses NREVSS PCR positivity rates
- **COVID-19 Card:** Uses hospitalization rates from cdc_covid_hospitalizations
- **Influenza Card:** Uses FluSurv-NET hospitalization rates
- Trend calculation based on recent vs. older data periods
- Location indicator shows "(BigQuery)" to confirm data source

## How Data Flows

```
BigQuery Tables
    │
    ├─ respiratory_disease_rates
    ├─ nrevss_respiratory_data  
    └─ cdc_covid_hospitalizations
           │
           ↓
    /api/infectious-disease-dashboard
           │
           ↓
    respiratory-chart.js
           │
           ↓
    Visual Chart + Disease Cards
```

## Testing

To verify the BigQuery integration is working:

1. **Start the Flask app:**
   ```powershell
   python app_local.py
   ```

2. **Open the dashboard:**
   ```
   http://localhost:5000
   ```

3. **Check the Infectious Disease Section:**
   - Chart should load with data from BigQuery
   - Disease cards should show real rates
   - Console should log "BigQuery dashboard response: success"

4. **Test the API directly:**
   ```
   curl "http://localhost:5000/api/infectious-disease-dashboard?days=30"
   ```

## Console Output Indicators

When working correctly, you'll see:
```
[RESPIRATORY CHART] Loading data from BigQuery for state: National
[RESPIRATORY CHART] BigQuery dashboard response: success
[RESPIRATORY CHART] Processing 50 NREVSS records from BigQuery
[RESPIRATORY CHART] Processing 150 respiratory rate records from BigQuery
[RESPIRATORY CHART] Processing 50 COVID hospitalization records from BigQuery
[RESPIRATORY CHART] Combined 250 data points from BigQuery tables
```

And for disease cards:
```
[DISEASE CARDS] ========== UPDATING CARDS (BigQuery) ==========
[DISEASE CARDS] ✓ BigQuery data received
[DISEASE CARDS] RSV avg positivity from BigQuery: 2.3
[DISEASE CARDS] COVID avg rate from BigQuery: 1.2
[DISEASE CARDS] Flu avg rate from BigQuery: 3.4
[DISEASE CARDS] ✓ All cards updated with BigQuery data
```

## Files Modified

1. **app_local.py**
   - Added `/api/covid-hospitalizations` endpoint
   - Added `/api/infectious-disease-dashboard` endpoint (combines all 3 tables)

2. **static/js/respiratory-chart.js**
   - Updated `loadData()` function to use BigQuery dashboard endpoint
   - Updated `updateDiseaseCards()` function to process BigQuery data
   - Added `calculateTrend()` helper function

## Data Quality

All three tables contain recent data (within 30 days):
- ✅ respiratory_disease_rates: 23 days old (Oct 4, 2025)
- ✅ nrevss_respiratory_data: 9 days old (Oct 18, 2025)  
- ✅ cdc_covid_hospitalizations: 30 days old (Sep 27, 2025)

## Next Steps

To keep data fresh:
1. Schedule weekly updates using the fetch scripts:
   - `fetch_respiratory_rates.py`
   - `fetch_cdc_nrevss.py`
   - `fetch_cdc_covid_hospitalizations.py`

2. Set up automated scheduling with:
   ```powershell
   .\setup_weekly_respiratory_schedule.ps1
   ```

3. Monitor BigQuery table metadata for streaming buffer commits (30-90 minutes)
