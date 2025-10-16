# Data Format Reference

## PM2.5 FRM Daily Summary Dataset

### File Structure
- **Format**: CSV
- **Delimiter**: Comma (,)
- **Headers**: Row 1
- **Date Format**: YYYY-MM-DD

### Key Columns

| Column Position | Field Name | Data Type | Description | Example |
|----------------|------------|-----------|-------------|---------|
| 1 | State Code | String | FIPS state code | "01" |
| 2 | County Code | String | FIPS county code | "003" |
| 3 | Site Num | String | Unique site identifier | "0010" |
| 4 | Parameter Code | String | Pollutant code | "88101" |
| 5 | POC | Integer | Parameter Occurrence Code | 3 |
| 6 | Latitude | Float | Site latitude (decimal degrees) | 30.497478 |
| 7 | Longitude | Float | Site longitude (decimal degrees) | -87.880258 |
| 8 | Datum | String | Coordinate datum | "NAD83" |
| 9 | Parameter Name | String | Pollutant description | "PM2.5 - Local Conditions" |
| 10 | Sample Duration | String | Measurement period | "1 HOUR" |
| 11 | Pollutant Standard | String | Regulatory standard | "" (blank) |
| 12 | Date Local | Date | Measurement date | "2025-01-01" |
| 13 | Units of Measure | String | Measurement units | "Micrograms/cubic meter (LC)" |
| 14 | Event Type | String | Special event indicator | "None" |
| 15 | Observation Count | Integer | Number of observations | 24 |
| 16 | Observation Percent | Float | Data completeness | 100.0 |
| 17 | **Arithmetic Mean** | **Float** | **Average PM2.5 (µg/m³)** | **3.625** |
| 18 | **1st Max Value** | **Float** | **Peak PM2.5 reading** | **19.0** |
| 19 | 1st Max Hour | Integer | Hour of peak reading | 21 |
| 20 | **AQI** | Integer | **Air Quality Index** | null (calculated) |
| 21 | Method Code | String | Measurement method ID | "209" |
| 22 | Method Name | String | Measurement method description | "Met One BAM-1022..." |
| 23 | **Local Site Name** | String | **Site common name** | "FAIRHOPE, Alabama" |
| 24 | Address | String | Site street address | "FAIRHOPE HIGH SCHOOL..." |
| 25 | **State Name** | **String** | **State name** | **"Alabama"** |
| 26 | **County Name** | **String** | **County name** | **"Baldwin"** |
| 27 | City Name | String | City name | "Fairhope" |
| 28 | CBSA Name | String | Metro area name | "Daphne-Fairhope-Foley, AL" |
| 29 | Date of Last Change | Date | Last data update | "2025-06-13" |

### Critical Fields for Analysis
- **Date Local**: Time dimension
- **State Name** & **County Name**: Geographic filters
- **Arithmetic Mean**: Primary PM2.5 metric
- **1st Max Value**: Peak exposure
- **AQI**: Health risk indicator

---

## CDC BEAM Dashboard Report Data

### File Structure
- **Format**: CSV
- **Delimiter**: Comma (,)
- **Headers**: Row 1
- **Date Format**: Year (Integer), Month (Integer)

### Key Columns

| Column Position | Field Name | Data Type | Description | Example |
|----------------|------------|-----------|-------------|---------|
| 1 | **Year** | **Integer** | **Report year** | **2025** |
| 2 | **Month** | **Integer** | **Report month (1-12)** | **1** |
| 3 | **State** | **String** | **State abbreviation (2 letters)** | **"AL"** |
| 4 | Source Type | String | Isolate origin | "Animal", "Food", "Human" |
| 5 | Source Site | String | Collection site | "Stool", "Other" |
| 6 | **Pathogen** | **String** | **Disease agent** | **"Campylobacter jejuni"** |
| 7 | Serotype_Species | String | Specific strain | "Campylobacter jejuni" |
| 8 | **Number of isolates** | **Integer** | **Confirmed cases** | **3** |
| 9 | Outbreak associated isolates | Integer/null | Cases in known outbreaks | null |
| 10 | New multistate outbreaks | Integer/null | New multi-state outbreaks | null |
| 11 | New multistate outbreaks - US | Integer/null | New US-wide outbreaks | null |
| 12 | % Isolates with... resistance | Float/null | Antibiotic resistance rate | null |
| 13 | Number of sequenced isolates... | Integer/null | NARMS analyzed samples | null |

### Critical Fields for Analysis
- **Year** & **Month**: Time dimension
- **State**: Geographic filter
- **Pathogen**: Disease categorization
- **Number of isolates**: Primary health metric
- **Source Type**: Transmission pathway

---

## Data Integration Strategy

### Temporal Alignment
- **Air Quality**: Daily granularity → Aggregate to monthly
- **Disease Data**: Monthly granularity → Native format
- **Join Key**: `YYYY-MM` (Year-Month string)

### Geographic Alignment
- **Air Quality**: County-level → Available
- **Disease Data**: State-level only → Limitation
- **Join Key**: State name (requires abbreviation conversion)

### State Name Mapping

| Full Name | Abbreviation | FIPS Code |
|-----------|--------------|-----------|
| Alabama | AL | 01 |
| Alaska | AK | 02 |
| Arizona | AZ | 04 |
| Arkansas | AR | 05 |
| California | CA | 06 |
| ... | ... | ... |

### Sample SQL-Like Join Logic

```sql
-- Aggregate air quality to monthly
SELECT 
  YEAR(Date_Local) AS year,
  MONTH(Date_Local) AS month,
  State_Name,
  County_Name,
  AVG(Arithmetic_Mean) AS avg_pm25,
  AVG(AQI) AS avg_aqi
FROM pm25_data
WHERE Date_Local >= '2025-01-01'
GROUP BY YEAR(Date_Local), MONTH(Date_Local), State_Name, County_Name

-- Join with disease data
JOIN disease_data ON
  air.year = disease.Year AND
  air.month = disease.Month AND
  LEFT(air.State_Name, 2) = disease.State  -- Convert to abbreviation
```

---

## AQI Calculation from PM2.5

EPA formula for converting PM2.5 concentration to AQI:

| PM2.5 Range (µg/m³) | AQI Range | Category |
|---------------------|-----------|----------|
| 0.0 - 12.0 | 0 - 50 | Good |
| 12.1 - 35.4 | 51 - 100 | Moderate |
| 35.5 - 55.4 | 101 - 150 | Unhealthy for Sensitive Groups |
| 55.5 - 150.4 | 151 - 200 | Unhealthy |
| 150.5 - 250.4 | 201 - 300 | Very Unhealthy |
| 250.5 - 500.4 | 301 - 500 | Hazardous |

**Formula**:
```
AQI = ((AQI_high - AQI_low) / (PM_high - PM_low)) * (PM - PM_low) + AQI_low
```

Where:
- `PM` = Measured PM2.5 concentration
- `PM_low`, `PM_high` = Range boundaries for measured value
- `AQI_low`, `AQI_high` = Corresponding AQI range boundaries

---

## Sample Data Records

### PM2.5 Record Example
```csv
1,3,10,88101,3,30.497478,-87.880258,NAD83,PM2.5 - Local Conditions,1 HOUR,,2025-01-01,Micrograms/cubic meter (LC),None,24,100.0,3.625,19.0,21,,209,Met One BAM-1022 Mass Monitor w/ VSCC or TE-PM2.5C - Beta Attenuation,FAIRHOPE Alabama,FAIRHOPE HIGH SCHOOL 1 PIRATE DRIVE FAIRHOPE ALABAMA,Alabama,Baldwin,Fairhope,Daphne-Fairhope-Foley AL,2025-06-13
```

**Parsed**:
- Date: 2025-01-01
- Location: Baldwin County, Alabama
- PM2.5 Mean: 3.625 µg/m³ (Good)
- PM2.5 Max: 19.0 µg/m³
- Site: Fairhope High School

### Disease Record Example
```csv
2025,1,AL,Animal,Other,Campylobacter coli,Campylobacter coli,3,,,,,
```

**Parsed**:
- Date: January 2025
- Location: Alabama (AL)
- Pathogen: Campylobacter coli
- Source: Animal
- Isolates: 3 cases

---

## Data Quality Checks

### Air Quality
- ✅ Check for null values in `Arithmetic Mean`
- ✅ Validate date range (should be recent)
- ✅ Ensure PM2.5 values are positive
- ✅ Verify observation percent > 75% for reliability
- ✅ Confirm geographic names match standard lists

### Disease Data
- ✅ Check for null values in `Number of isolates`
- ✅ Validate month range (1-12)
- ✅ Ensure state abbreviations are 2 characters
- ✅ Verify pathogen names are standardized
- ✅ Confirm isolate counts are positive integers

---

## API Response Formats

### Air Quality Response
```json
{
  "county": "Baldwin",
  "state": "Alabama",
  "daily_data": [
    {
      "date": "2025-01-01",
      "pm25_mean": 3.63,
      "pm25_min": 2.5,
      "pm25_max": 19.0,
      "aqi": 15,
      "observations": 24
    }
  ],
  "statistics": {
    "avg_pm25": 5.2,
    "max_pm25": 25.0,
    "min_pm25": 1.5,
    "avg_aqi": 22,
    "max_aqi": 78,
    "days_good": 85,
    "days_moderate": 5,
    "days_unhealthy": 0,
    "total_days": 90
  },
  "monitoring_sites": 3
}
```

### Disease Response
```json
{
  "state": "AL",
  "pathogens": [
    {
      "pathogen": "Campylobacter jejuni",
      "total_isolates": 45,
      "sources": {
        "Human": 20,
        "Animal": 15,
        "Food": 10
      }
    }
  ],
  "monthly_trend": [
    {"year": 2025, "month": 1, "total_isolates": 45},
    {"year": 2025, "month": 2, "total_isolates": 38}
  ],
  "total_isolates": 285,
  "unique_pathogens": 4
}
```

### Correlation Response
```json
{
  "county": "Baldwin",
  "state": "Alabama",
  "monthly_comparison": [
    {"month": "2025-01", "pm25": 5.2, "isolates": 45},
    {"month": "2025-02", "pm25": 6.8, "isolates": 38}
  ],
  "correlation": 0.342,
  "air_quality_summary": { /* see above */ },
  "disease_summary": {
    "total_isolates": 285,
    "unique_pathogens": 4
  }
}
```

---

## Performance Optimization

### Large Dataset Handling
- **Air Quality CSV**: 241,153 rows, ~88 MB
  - Use `low_memory=False` in pandas
  - Specify dtypes for faster parsing
  - Parse dates during load (not after)
  - Filter early in processing pipeline

- **Disease CSV**: Variable size
  - Aggregate during load when possible
  - Index by state for faster filtering
  - Cache results for repeated queries

### Query Optimization
```python
# Good: Filter before aggregation
filtered = df[df['State Name'] == 'Alabama']
result = filtered.groupby('Date Local').mean()

# Bad: Aggregate then filter
result = df.groupby(['State Name', 'Date Local']).mean()
filtered = result[result.index.get_level_values(0) == 'Alabama']
```

---

**Document Version**: 1.0  
**Last Updated**: October 16, 2025  
**Compatibility**: app_integrated.py v2.0
