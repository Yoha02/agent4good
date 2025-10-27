# BigQuery Data Updates - Quick Summary

## ✅ What Was Done

### 1. Updated CDC COVID Data Source
- **Old:** XML endpoint (outdated)
- **New:** https://data.cdc.gov/api/v3/views/6jg4-xsqq/query.csv ✨
- **File:** `data_ingestion/fetch_external_feeds.py`
- **Table:** `cdc_covid_data`

### 2. Updated NREVSS Data Source  
- **Old:** JSON endpoint (52kb-ccu2)
- **New:** https://data.cdc.gov/resource/3cxc-4k8q.csv ✨
- **File:** `data_ingestion/fetch_cdc_nrevss.py`
- **Table:** `nrevss_respiratory_data`

### 3. Created NEW Respiratory Disease Rates Table
- **Source:** https://data.cdc.gov/resource/kvib-3txy.json ✨
- **File:** `data_ingestion/fetch_respiratory_rates.py`
- **Table:** `respiratory_disease_rates` (NEW!)
- **Contains:** RSV, COVID-19, and Influenza rates per 100k population
- **Features:** 
  - ✅ Real date column (`week_end_date`) parsed from `weekendingdate`
  - ✅ Weekly ingestion scheduled
  - ✅ Rates per 100,000 population
  - ✅ Confidence intervals included

### 4. Added New API Endpoint
- **Endpoint:** `/api/respiratory-disease-rates`
- **File:** `app_local.py`
- **Features:** Filter by geography, disease, date range

### 5. Created Interactive Chart
- **File:** `static/js/respiratory-disease-rates-chart.js`
- **Features:**
  - Interactive time series for RSV, COVID-19, Flu
  - Disease filtering (toggle on/off)
  - Date range slider
  - Professional CDC-style visualization

---

## 🚀 Quick Start

### Run Initial Data Load:
```powershell
cd data_ingestion
.\run_initial_data_load.ps1
```

This will:
1. ✅ Load CDC COVID data (updated source)
2. ✅ Load NREVSS data (updated source)  
3. ✅ Load NEW respiratory rates data
4. ✅ Setup weekly schedule for automatic updates

### Or Run Individually:
```powershell
# Load all external feeds (includes COVID)
python fetch_external_feeds.py

# Load NREVSS data
python fetch_cdc_nrevss.py

# Load respiratory rates data (NEW)
python fetch_respiratory_rates.py
```

---

## 📊 Using the New Chart

### In HTML Template:
```html
<!-- Include Chart.js -->
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<!-- Include the new chart -->
<script src="{{ url_for('static', filename='js/respiratory-disease-rates-chart.js') }}"></script>

<!-- Add container -->
<div id="respiratoryDiseaseRatesChartContainer"></div>
```

The chart will automatically:
- Load RSV, COVID-19, and Influenza rates
- Display last 6 months of data
- Allow interactive filtering
- Update based on location selection

---

## 🗓️ Weekly Schedule

The new respiratory rates data is configured to update automatically:
- **Frequency:** Weekly (every Monday at 3:00 AM)
- **Task Name:** `CDC_Respiratory_Rates_Weekly_Ingestion`
- **Setup:** Run `setup_weekly_respiratory_schedule.ps1`

To verify:
```powershell
Get-ScheduledTask -TaskName "CDC_Respiratory_Rates_Weekly_Ingestion"
```

To run manually:
```powershell
Start-ScheduledTask -TaskName "CDC_Respiratory_Rates_Weekly_Ingestion"
```

---

## ✅ Data Verification

### Check BigQuery Tables:
```sql
-- Check COVID data (updated source)
SELECT COUNT(*) as records, MAX(created_at) as last_update
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`;

-- Check NREVSS data (updated source)
SELECT COUNT(*) as records, MAX(load_timestamp) as last_update
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`;

-- Check respiratory rates (NEW!)
SELECT COUNT(*) as records, MAX(load_timestamp) as last_update
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.respiratory_disease_rates`;

-- View sample respiratory rates data
SELECT disease, week_end_date, rate, geography
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.respiratory_disease_rates`
WHERE age_category = 'Overall'
ORDER BY week_end_date DESC
LIMIT 10;
```

### Test API Endpoint:
```
http://localhost:5000/api/respiratory-disease-rates?geography=United%20States&disease=all&limit=52
```

---

## 📁 Files Created/Modified

### ✨ New Files:
- `data_ingestion/fetch_respiratory_rates.py` - NEW data fetcher
- `data_ingestion/setup_weekly_respiratory_schedule.ps1` - Weekly scheduler
- `data_ingestion/run_initial_data_load.ps1` - Quick start script
- `static/js/respiratory-disease-rates-chart.js` - Interactive chart
- `data_ingestion/BQ_UPDATES_README.md` - Full documentation
- `data_ingestion/QUICK_SUMMARY.md` - This file

### 🔄 Modified Files:
- `data_ingestion/fetch_external_feeds.py` - Updated COVID source
- `data_ingestion/fetch_cdc_nrevss.py` - Updated NREVSS source
- `app_local.py` - Added new API endpoint

---

## 🎯 Key Features

### The New Respiratory Rates Chart Provides:

1. **Multiple Diseases in One View**
   - RSV, COVID-19, and Influenza
   - Toggle diseases on/off individually

2. **Standardized Rates**
   - Per 100,000 population
   - Comparable across diseases and regions

3. **Interactive Features**
   - Date range slider
   - Hover tooltips with detailed info
   - Smooth animations

4. **Real Date Column**
   - Proper `DATE` type in BigQuery (`week_end_date`)
   - Parsed from `weekendingdate` field
   - Enables accurate time-series analysis

5. **Weekly Updates**
   - Automatic ingestion every Monday
   - Always shows recent data (within 1 month)

---

## 💡 Recommendation

**Use the NEW respiratory disease rates chart for your main infectious disease tracking because:**

✅ Shows RSV, COVID-19, AND Flu in one view  
✅ Uses standardized rates (per 100k population)  
✅ More comprehensive and recent data  
✅ Better filtering and interactivity  
✅ Professional CDC-style visualization  

The old NREVSS chart can remain as a supplementary view for detailed RSV test positivity rates.

---

## 📖 Documentation

For complete details, see:
- **Full Documentation:** `data_ingestion/BQ_UPDATES_README.md`
- **Data Sources:**
  - COVID: https://data.cdc.gov/api/v3/views/6jg4-xsqq
  - NREVSS: https://data.cdc.gov/resource/3cxc-4k8q
  - Respiratory Rates: https://data.cdc.gov/resource/kvib-3txy

---

## 🆘 Need Help?

1. **Check logs** in Task Scheduler for scheduled jobs
2. **Verify** BigQuery table schemas
3. **Test** API endpoints directly in browser
4. **Review** CDC data documentation for API changes

---

**Status:** ✅ All data sources updated to use current CDC endpoints (within 1 month)  
**Date:** October 27, 2025
