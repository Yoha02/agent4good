# Integrated Health & Environmental Platform - User Guide

## 🌍 Overview

The Integrated Health & Environmental Platform provides county-level analysis of air quality (PM2.5) and infectious disease data, enabling users to:

- **Compare air quality metrics** across different counties and time periods
- **Track infectious disease patterns** at the state level
- **Analyze correlations** between environmental factors and disease outbreaks
- **Get AI-powered insights** on public health implications

---

## 📊 Data Sources

### 1. EPA Air Quality Data: `pm25_frm_daily_summary`

**241,153 rows** of real PM2.5 measurements covering:
- **52 states**
- **512 counties**
- **Date range**: January 1 - July 3, 2025

**Key Fields:**
- `State Name`, `County Name`, `City Name`
- `Date Local` - Measurement date
- `Arithmetic Mean` - Average PM2.5 concentration (µg/m³)
- `1st Max Value` - Peak PM2.5 reading
- `AQI` - Air Quality Index
- `Latitude`, `Longitude` - Monitoring site coordinates
- `Local Site Name`, `Address` - Site identification

### 2. CDC Infectious Disease Data: `BEAM_Dashboard_Report_Data`

Monthly reports of pathogen isolates by state:

**Key Fields:**
- `Year`, `Month` - Reporting period
- `State` - State abbreviation (AL, CA, TX, etc.)
- `Pathogen` - Disease agent (Campylobacter, Salmonella, E. coli, etc.)
- `Source Type` - Human, Animal, or Food
- `Number of isolates` - Count of confirmed cases
- `Outbreak associated isolates` - Cases linked to outbreaks

---

## 🚀 How to Use

### Step 1: Select Location

1. **Choose a State** from the dropdown (e.g., "Alabama", "California")
2. **Select a County** - Counties show average PM2.5 levels for quick reference
3. **Pick Time Period** - 30, 60, 90, or 180 days of air quality data
4. Click **"Load Data"**

### Step 2: View Air Quality Analysis

**Summary Metrics:**
- **Average PM2.5** - Mean particulate matter concentration
- **Average AQI** - Overall air quality index with category (Good, Moderate, etc.)
- **Good/Moderate/Unhealthy Days** - Distribution of air quality days

**Visualizations:**
- **Time series chart** showing daily PM2.5 trends
- **Color-coded AQI badge** indicating current status
- **Monitoring sites count** for data reliability

### Step 3: Review Disease Data

**State-Level Metrics:**
- **Total Disease Isolates** - Sum over past 6 months
- **Unique Pathogens** - Number of different disease agents detected

**Pathogen Breakdown:**
- List of top 5 pathogens with isolate counts
- Source distribution (Human/Animal/Food)
- **Monthly trend chart** showing disease activity over time

### Step 4: Analyze Correlations

**Correlation Analysis:**
- **Scatter plot** comparing PM2.5 levels vs disease isolates by month
- **Correlation coefficient** (-1 to +1):
  - **-1.0 to -0.7**: Strong negative correlation
  - **-0.7 to -0.3**: Moderate negative correlation
  - **-0.3 to +0.3**: Weak or no correlation
  - **+0.3 to +0.7**: Moderate positive correlation
  - **+0.7 to +1.0**: Strong positive correlation

**Interpretation:**
- **Positive correlation**: Higher PM2.5 → More disease cases
- **Negative correlation**: Higher PM2.5 → Fewer disease cases
- **Weak correlation**: Little to no relationship

### Step 5: Get AI Insights

Click **"Get AI Analysis"** to receive:
1. Interpretation of air quality levels
2. Assessment of disease activity
3. Potential relationships between environmental and health factors
4. Recommendations for public health interventions

---

## 📈 Use Cases

### 1. Public Health Monitoring

**Scenario:** Track if poor air quality correlates with increased respiratory infections

**Steps:**
1. Select urban county with industrial activity
2. Set time period to 180 days for comprehensive analysis
3. Review correlation coefficient
4. Get AI analysis for intervention recommendations

### 2. Environmental Justice

**Scenario:** Compare air quality between affluent and underserved counties

**Steps:**
1. Load data for County A (affluent)
2. Note PM2.5 levels and disease patterns
3. Switch to County B (underserved)
4. Compare summary metrics side-by-side
5. Document disparities for policy advocacy

### 3. Outbreak Investigation

**Scenario:** Investigate spike in foodborne illness cases

**Steps:**
1. Select state experiencing outbreak
2. Review disease trend chart for anomalies
3. Check if air quality events coincide with outbreak timing
4. Use pathogen breakdown to identify specific agents
5. Generate AI analysis for hypothesis generation

### 4. Seasonal Pattern Analysis

**Scenario:** Understand how seasons affect air quality and disease

**Steps:**
1. Select county and 180-day period spanning multiple seasons
2. Observe PM2.5 fluctuations in time series
3. Compare with disease monthly trends
4. Identify seasonal peaks in both datasets

---

## 🎯 Key Metrics Explained

### Air Quality Index (AQI)

| AQI Range | Category | Color | Health Impact |
|-----------|----------|-------|---------------|
| 0-50 | Good | Green | Air quality is satisfactory |
| 51-100 | Moderate | Yellow | Acceptable; some concern for sensitive individuals |
| 101-150 | Unhealthy for Sensitive Groups | Orange | Sensitive groups may experience health effects |
| 151-200 | Unhealthy | Red | Everyone may begin to experience health effects |
| 201-300 | Very Unhealthy | Purple | Health alert; everyone may experience serious effects |
| 301-500 | Hazardous | Maroon | Health warnings of emergency conditions |

### PM2.5 Concentration

Fine particulate matter ≤2.5 micrometers in diameter:
- **0-12 µg/m³**: Good air quality
- **12-35 µg/m³**: Moderate air quality
- **35-55 µg/m³**: Unhealthy for sensitive groups
- **55+ µg/m³**: Unhealthy for everyone

**Health Effects:**
- Respiratory irritation
- Aggravated asthma
- Decreased lung function
- Cardiovascular problems
- Premature death in severe cases

---

## 🔧 Technical Details

### API Endpoints

```
GET /api/counties?state={state}
  Returns list of counties with air quality data

GET /api/county/air-quality?state={state}&county={county}&days={days}
  Returns detailed air quality metrics for specific county

GET /api/state/disease?state={state}&months={months}
  Returns infectious disease data for state

GET /api/correlation?state={state}&county={county}
  Returns correlation analysis between air quality and disease

POST /api/analyze-correlation
  Body: {state, county}
  Returns AI-powered analysis of correlation data

GET /api/stats
  Returns overall platform statistics
```

### Data Processing

**Air Quality Aggregation:**
- Daily data aggregated by county
- PM2.5 values averaged across all monitoring sites
- AQI calculated from PM2.5 using EPA formula
- Statistics computed over selected time period

**Disease Data Aggregation:**
- Monthly data summed by pathogen
- Source types tracked separately
- Trend analysis over 6-month window
- State-level aggregation only (no county data available)

**Correlation Calculation:**
- Air quality aggregated to monthly averages
- Matched with disease data by year-month
- Pearson correlation coefficient computed
- Scatter plot generated for visual inspection

---

## 📝 Data Limitations

1. **Disease data is state-level only** - County-level disease data not available
2. **Time lag in reporting** - Disease data may have 1-2 month delay
3. **Correlation ≠ Causation** - Statistical relationships don't prove direct cause
4. **Missing values** - Some counties/dates may have incomplete data
5. **Weather factors not included** - Temperature, humidity affect both air quality and disease
6. **Population differences** - Raw counts don't account for county population size

---

## 🎨 UI Features

### Interactive Elements

- **Responsive design** - Works on desktop, tablet, and mobile
- **Real-time updates** - Charts refresh when new location selected
- **Animated transitions** - Smooth visual feedback
- **Loading indicators** - Clear status during data fetching
- **Color-coded metrics** - Quick visual interpretation of health risks

### Visualizations

1. **PM2.5 Time Series** (Line Chart)
   - Daily trends over selected period
   - Green gradient fill for quick status assessment

2. **Disease Monthly Trend** (Bar Chart)
   - Total isolates by month
   - Emerald green bars for consistency

3. **Correlation Scatter Plot**
   - Each point = one month of data
   - X-axis: PM2.5, Y-axis: Disease isolates
   - Visual pattern indicates relationship strength

### Three.js Background

- Animated particle system
- 1000 emerald green particles
- Creates immersive, modern feel
- Low performance impact

---

## 🚀 Getting Started

### Option 1: Run Locally

```powershell
# Navigate to project
cd "path\to\agent4good"

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run integrated application
python app_integrated.py

# Open browser
http://localhost:8080
```

### Option 2: With CDC Data File

If you have the BEAM Dashboard CSV:

1. Update `.env` file:
   ```
   LOCAL_CDC_CSV=C:\path\to\BEAM_Dashboard_Report_Data.csv
   ```

2. Run application - it will automatically load real CDC data

3. Demo data is generated automatically if file not found

### Option 3: Enable AI Analysis

1. Get Gemini API key: https://makersuite.google.com/app/apikey

2. Update `.env` file:
   ```
   GEMINI_API_KEY=your-actual-key-here
   ```

3. Restart application - AI analysis button will work

---

## 📚 Example Queries

### Baldwin County, Alabama
- **State**: Alabama
- **County**: Baldwin
- **Time Period**: 90 days
- **Expected Results**: Coastal county, moderate PM2.5, seafood-related pathogens

### Los Angeles County, California
- **State**: California
- **County**: Los Angeles
- **Time Period**: 180 days
- **Expected Results**: Urban air quality issues, diverse pathogen sources

### Harris County, Texas
- **State**: Texas
- **County**: Harris (Houston area)
- **Time Period**: 90 days
- **Expected Results**: Industrial emissions, food/animal disease sources

---

## 🔍 Troubleshooting

**Issue**: "No data found for this county"
- **Solution**: Try different county or check spelling

**Issue**: "Insufficient data for correlation analysis"
- **Solution**: Select longer time period (180 days) or different location

**Issue**: AI analysis shows "not available"
- **Solution**: Configure GEMINI_API_KEY in .env file

**Issue**: Disease data seems generic
- **Solution**: Real CDC file not loaded - update LOCAL_CDC_CSV path

**Issue**: Charts not rendering
- **Solution**: Check browser console for JavaScript errors, refresh page

---

## 📊 Data Update Schedule

- **Air Quality Data**: Updated daily (EPA)
- **Disease Data**: Updated monthly (CDC)
- **Platform**: Restart application to load latest data

---

## 🤝 Contributing

See `CONTRIBUTING.md` for guidelines on:
- Adding new data sources
- Implementing additional visualizations
- Enhancing correlation algorithms
- Improving AI analysis prompts

---

## 📄 License

See LICENSE file for details.

---

## 🆘 Support

For issues or questions:
1. Check this guide first
2. Review console output for error messages
3. Open GitHub issue with detailed description
4. Include sample data and steps to reproduce

---

**Version**: 2.0.0  
**Last Updated**: October 16, 2025  
**Maintainer**: Community Health Platform Team
