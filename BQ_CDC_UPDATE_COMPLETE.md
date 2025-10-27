# BigQuery CDC Data Update Summary

## Objective
Update BigQuery tables with recent CDC data (within one month old) for disease tracking dashboard.

## Completed Updates

### 1. ✅ respiratory_disease_rates
- **Data Source**: https://data.cdc.gov/resource/kvib-3txy.json
- **Description**: Laboratory-confirmed RSV, COVID-19, and Influenza hospitalization rates
- **Table Created**: ✅ New table
- **Records Loaded**: 15,000
- **Date Range**: January 2024 to **October 4, 2025**
- **Latest Data**: Within past 30 days ✓
- **Script**: `data_ingestion/fetch_respiratory_rates.py`

### 2. ✅ nrevss_respiratory_data  
- **Data Source**: https://data.cdc.gov/resource/3cxc-4k8q.csv
- **Description**: National Respiratory and Enteric Virus Surveillance System data (PCR test results)
- **Table Updated**: ✅ Schema revised and data refreshed
- **Records Loaded**: 10,000
- **Date Range**: December 2024 to **October 18, 2025**
- **Latest Data**: Within past 30 days ✓
- **Script**: `data_ingestion/fetch_cdc_nrevss.py`

### 3. ✅ cdc_covid_hospitalizations (NEW TABLE)
- **Data Source**: https://data.cdc.gov/resource/6jg4-xsqq.json
- **Description**: CDC COVID-19 laboratory-confirmed hospitalization rates by state, age, sex, and race/ethnicity
- **Table Created**: ✅ New table (previous cdc_covid_data was for testing data)
- **Records Loaded**: 15,000
- **Date Range**: April 12, 2025 to **September 27, 2025**
- **Latest Data**: Within past 30 days ✓
- **Script**: `data_ingestion/fetch_cdc_covid_hospitalizations.py`

## Key Findings

### Why New Table for COVID Data?
The original request specified using https://data.cdc.gov/resource/6jg4-xsqq.json for CDC COVID data. However, the existing `cdc_covid_data` table had a different schema designed for testing data (fields like `percent_pos`, `number_tested`, `mmwr_week_end`), not hospitalization rates (fields like `weeklyrate`, `cumulativerate`, `state`, `agecategory`, `sex`, `race`).

Solution: Created a new table `cdc_covid_hospitalizations` with the correct schema for the hospitalization rates dataset.

## Schema Updates

### respiratory_disease_rates Schema
- record_id (STRING, REQUIRED)
- surveillance_network (STRING)
- season (STRING)
- mmwr_year (INTEGER)
- mmwr_week (INTEGER)
- weekenddate (DATE) ← Real date column as requested
- state (STRING)
- rate (FLOAT)
- created_at (TIMESTAMP)

### nrevss_respiratory_data Schema
- record_id (STRING, REQUIRED)
- surveillance_area (STRING)
- surveillance_network (STRING)
- region (STRING)
- mmwrweek (STRING)
- mmwrweek_end (DATE) ← Real date column
- pcr_percent_positive (FLOAT)
- pcr_detections (INTEGER)
- created_at (TIMESTAMP)

### cdc_covid_hospitalizations Schema
- record_id (STRING, REQUIRED)
- weekenddate (DATE) ← Real date column
- state (STRING)
- season (STRING)
- agecategory (STRING)
- sex (STRING)
- race (STRING)
- type (STRING)
- weeklyrate (FLOAT)
- cumulativerate (FLOAT)
- created_at (TIMESTAMP)

## API Endpoints Summary

All three data sources use the CDC Socrata API (open data platform):
1. **Respiratory Disease Rates**: kvib-3txy (No auth required)
2. **NREVSS Data**: 3cxc-4k8q (No auth required)
3. **COVID Hospitalizations**: 6jg4-xsqq (No auth required)

All endpoints accept standard Socrata query parameters:
- `$limit`: Number of records to fetch
- `$order`: Sort order (we use `DESC` by date field to get most recent first)

## Verification Commands

To verify the data in BigQuery, run these queries:

```sql
-- Check respiratory_disease_rates
SELECT 
    COUNT(*) as total_records,
    MIN(weekenddate) as earliest_date,
    MAX(weekenddate) as latest_date
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.respiratory_disease_rates`;

-- Check nrevss_respiratory_data
SELECT 
    COUNT(*) as total_records,
    MIN(mmwrweek_end) as earliest_date,
    MAX(mmwrweek_end) as latest_date
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`;

-- Check cdc_covid_hospitalizations
SELECT 
    COUNT(*) as total_records,
    MIN(weekenddate) as earliest_date,
    MAX(weekenddate) as latest_date
FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_hospitalizations`;
```

## Scheduling

For weekly updates, use the provided PowerShell scheduling scripts:
- `setup_weekly_respiratory_schedule.ps1` - For respiratory disease rates
- Similar scripts can be created for NREVSS and COVID hospitalizations

## Next Steps

1. **Update Dashboard**: Integrate new tables into `app_local.py` endpoints
2. **Visualization**: Add `cdc_covid_hospitalizations` to the interactive disease tracking charts
3. **Documentation**: Update API documentation with new endpoints
4. **Testing**: Verify all charts and data visualizations work with new data

## Files Created/Modified

### New Files:
- `data_ingestion/fetch_respiratory_rates.py`
- `data_ingestion/fetch_cdc_covid_hospitalizations.py`
- `data_ingestion/schemas/cdc_covid_hospitalizations.json`

### Modified Files:
- `data_ingestion/fetch_cdc_nrevss.py` (complete rewrite)
- `app_local.py` (added /api/respiratory-disease-rates endpoint)

### Supporting Files:
- `static/js/respiratory-disease-rates-chart.js` (interactive chart)
- `setup_weekly_respiratory_schedule.ps1` (scheduling script)
- Various test and verification scripts

## Success Metrics

✅ All three tables have data within the past 30 days
✅ Real date columns created as requested
✅ Proper data schemas matching API structure
✅ Documented code with error handling
✅ Verification scripts and documentation provided

