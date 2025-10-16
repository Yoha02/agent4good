import os
import sys
import json
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from google.cloud import bigquery
from google.api_core import exceptions as google_exceptions
import google.generativeai as genai
from dotenv import load_dotenv
import numpy as np

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class IntegratedHealthAgent:
    """Integrated agent for Air Quality and Infectious Disease data analysis"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-86088b6278cb')
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'BQ_EPA_Air_Data')
        self.local_csv_path = os.getenv('LOCAL_EPA_CSV', r'c:\Users\semaa\OneDrive\Documents\Google\Agents4Impact10162025\AIr Quality\daily_88101_2025\daily_88101_2025.csv')
        self.disease_csv_path = os.getenv('LOCAL_CDC_CSV', r'c:\Users\semaa\OneDrive\Documents\Google\Agents4Impact10162025\AIr Quality\BEAM_Dashboard_Report_Data.csv')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Data sources
        self.bq_client = None
        self.use_bigquery = False
        self.air_quality_df = None
        self.disease_df = None
        
        # Column mappings for PM2.5 FRM Daily Summary
        self.air_columns = {
            'state_code': 'State Code',
            'county_code': 'County Code',
            'site_num': 'Site Num',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'parameter': 'Parameter Name',
            'date': 'Date Local',
            'units': 'Units of Measure',
            'observation_count': 'Observation Count',
            'observation_percent': 'Observation Percent',
            'arithmetic_mean': 'Arithmetic Mean',
            'max_value': '1st Max Value',
            'max_hour': '1st Max Hour',
            'aqi': 'AQI',
            'method_name': 'Method Name',
            'local_site_name': 'Local Site Name',
            'address': 'Address',
            'state_name': 'State Name',
            'county_name': 'County Name',
            'city_name': 'City Name',
            'cbsa_name': 'CBSA Name'
        }
        
        # Column mappings for CDC BEAM Dashboard Report Data
        self.disease_columns = {
            'year': 'Year',
            'month': 'Month',
            'state': 'State',
            'source_type': 'Source Type',
            'source_site': 'Source Site',
            'pathogen': 'Pathogen',
            'serotype': 'Serotype_Species',
            'isolates': 'Number of isolates',
            'outbreak_isolates': 'Outbreak associated isolates',
            'new_outbreaks': 'New multistate outbreaks',
            'new_outbreaks_us': 'New multistate outbreaks - US',
            'resistance_percent': '% Isolates with clinically important antimicrobial resistance',
            'sequenced_isolates': 'Number of sequenced isolates analyzed by NARMS'
        }
        
        self._initialize_data_sources()
        self._initialize_ai()
        
    def _initialize_data_sources(self):
        """Initialize all data sources"""
        print("\n" + "="*80)
        print("🌍 Integrated Health Data Platform Initialization")
        print("="*80)
        
        # Try BigQuery
        try:
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                self.bq_client = bigquery.Client(project=self.project_id)
                query = f"SELECT table_id FROM `{self.project_id}.{self.dataset_id}.__TABLES__` LIMIT 1"
                self.bq_client.query(query).result()
                self.use_bigquery = True
                print("✅ BigQuery Connection: SUCCESS")
        except Exception as e:
            print(f"⚠️  BigQuery Connection: FAILED - {str(e)}")
        
        # Load Air Quality Data
        if os.path.exists(self.local_csv_path):
            try:
                print(f"\n📂 Loading Air Quality CSV...")
                print(f"   Path: {self.local_csv_path}")
                
                dtype_dict = {
                    'State Code': str,
                    'County Code': str,
                    'Site Num': str,
                    'AQI': 'Int64'
                }
                
                self.air_quality_df = pd.read_csv(
                    self.local_csv_path,
                    dtype=dtype_dict,
                    parse_dates=['Date Local'],
                    low_memory=False
                )
                
                print(f"✅ Air Quality Data Loaded: {len(self.air_quality_df):,} rows")
                print(f"   Date Range: {self.air_quality_df['Date Local'].min()} to {self.air_quality_df['Date Local'].max()}")
                print(f"   States: {self.air_quality_df['State Name'].nunique()}")
                print(f"   Counties: {self.air_quality_df['County Name'].nunique()}")
                
            except Exception as e:
                print(f"⚠️  Air Quality CSV Loading: FAILED - {str(e)}")
        else:
            print(f"⚠️  Air Quality CSV not found at: {self.local_csv_path}")
        
        # Load Disease Data
        if os.path.exists(self.disease_csv_path):
            try:
                print(f"\n📂 Loading Disease Data CSV...")
                print(f"   Path: {self.disease_csv_path}")
                
                self.disease_df = pd.read_csv(self.disease_csv_path)
                
                print(f"✅ Disease Data Loaded: {len(self.disease_df):,} rows")
                print(f"   States: {self.disease_df['State'].nunique()}")
                print(f"   Pathogens: {self.disease_df['Pathogen'].nunique()}")
                print(f"   Date Range: {self.disease_df['Year'].min()}/{self.disease_df['Month'].min()} to {self.disease_df['Year'].max()}/{self.disease_df['Month'].max()}")
                
            except Exception as e:
                print(f"⚠️  Disease CSV Loading: FAILED - {str(e)}")
                # Generate demo disease data if file doesn't exist
                self.disease_df = self._generate_demo_disease_data()
        else:
            print(f"⚠️  Disease CSV not found - generating demo data")
            self.disease_df = self._generate_demo_disease_data()
        
        print("="*80 + "\n")
    
    def _initialize_ai(self):
        """Initialize Gemini AI"""
        if self.gemini_api_key and self.gemini_api_key != 'your-gemini-api-key':
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                print("✅ Gemini AI initialized")
            except Exception as e:
                print(f"⚠️  Gemini AI initialization failed: {str(e)}")
                self.model = None
        else:
            print("ℹ️  Gemini API key not configured - AI features disabled")
            self.model = None
    
    def _generate_demo_disease_data(self):
        """Generate demo disease data"""
        import random
        
        states = ['AL', 'CA', 'TX', 'NY', 'FL']
        pathogens = ['Campylobacter jejuni', 'Campylobacter coli', 'Salmonella', 'E. coli']
        source_types = ['Human', 'Animal', 'Food']
        source_sites = ['Stool', 'Other']
        
        data = []
        for year in [2025]:
            for month in range(1, 11):
                for state in states:
                    for pathogen in pathogens:
                        for source_type in source_types:
                            data.append({
                                'Year': year,
                                'Month': month,
                                'State': state,
                                'Source Type': source_type,
                                'Source Site': random.choice(source_sites),
                                'Pathogen': pathogen,
                                'Serotype_Species': pathogen,
                                'Number of isolates': random.randint(1, 20),
                                'Outbreak associated isolates': None,
                                'New multistate outbreaks': None,
                                'New multistate outbreaks - US': None,
                                '% Isolates with clinically important antimicrobial resistance': None,
                                'Number of sequenced isolates analyzed by NARMS': None
                            })
        
        return pd.DataFrame(data)
    
    def get_county_list(self, state=None):
        """Get list of counties, optionally filtered by state"""
        if self.air_quality_df is None:
            return []
        
        df = self.air_quality_df
        if state:
            df = df[df['State Name'].str.upper() == state.upper()]
        
        counties = df.groupby(['State Name', 'County Name']).agg({
            'Date Local': ['min', 'max'],
            'Arithmetic Mean': 'mean',
            'Site Num': 'nunique'
        }).reset_index()
        
        result = []
        for _, row in counties.iterrows():
            result.append({
                'state': row['State Name'],
                'county': row['County Name'],
                'avg_pm25': round(row[('Arithmetic Mean', 'mean')], 2),
                'monitoring_sites': int(row[('Site Num', 'nunique')]),
                'date_range': f"{row[('Date Local', 'min')].strftime('%Y-%m-%d')} to {row[('Date Local', 'max')].strftime('%Y-%m-%d')}"
            })
        
        return result
    
    def get_county_air_quality(self, state, county, days=30):
        """Get detailed air quality data for a specific county"""
        if self.air_quality_df is None:
            return None
        
        # Filter data
        end_date = self.air_quality_df['Date Local'].max()
        start_date = end_date - timedelta(days=days)
        
        filtered_df = self.air_quality_df[
            (self.air_quality_df['State Name'].str.upper() == state.upper()) &
            (self.air_quality_df['County Name'].str.upper() == county.upper()) &
            (self.air_quality_df['Date Local'] >= start_date)
        ].copy()
        
        if filtered_df.empty:
            return None
        
        # Daily aggregations
        daily_data = filtered_df.groupby('Date Local').agg({
            'Arithmetic Mean': ['mean', 'min', 'max'],
            '1st Max Value': 'max',
            'AQI': 'mean',
            'Observation Count': 'sum'
        }).reset_index()
        
        results = []
        for _, row in daily_data.iterrows():
            pm25_mean = row[('Arithmetic Mean', 'mean')]
            aqi = row[('AQI', 'mean')]
            
            # Calculate AQI from PM2.5 if AQI is not available
            if pd.isna(aqi) and not pd.isna(pm25_mean):
                aqi = self._calculate_aqi_from_pm25(pm25_mean)
            
            results.append({
                'date': row['Date Local'].strftime('%Y-%m-%d'),
                'pm25_mean': round(pm25_mean, 2) if not pd.isna(pm25_mean) else None,
                'pm25_min': round(row[('Arithmetic Mean', 'min')], 2) if not pd.isna(row[('Arithmetic Mean', 'min')]) else None,
                'pm25_max': round(row[('Arithmetic Mean', 'max')], 2) if not pd.isna(row[('Arithmetic Mean', 'max')]) else None,
                'aqi': int(aqi) if not pd.isna(aqi) else 50,
                'observations': int(row[('Observation Count', 'sum')])
            })
        
        # Calculate statistics
        pm25_values = [d['pm25_mean'] for d in results if d['pm25_mean'] is not None]
        aqi_values = [d['aqi'] for d in results]
        
        statistics = {
            'avg_pm25': round(np.mean(pm25_values), 2) if pm25_values else None,
            'max_pm25': round(np.max(pm25_values), 2) if pm25_values else None,
            'min_pm25': round(np.min(pm25_values), 2) if pm25_values else None,
            'avg_aqi': round(np.mean(aqi_values), 1) if aqi_values else None,
            'max_aqi': int(np.max(aqi_values)) if aqi_values else None,
            'days_good': sum(1 for aqi in aqi_values if aqi <= 50),
            'days_moderate': sum(1 for aqi in aqi_values if 51 <= aqi <= 100),
            'days_unhealthy': sum(1 for aqi in aqi_values if aqi > 100),
            'total_days': len(results)
        }
        
        return {
            'county': county,
            'state': state,
            'daily_data': sorted(results, key=lambda x: x['date']),
            'statistics': statistics,
            'monitoring_sites': filtered_df['Site Num'].nunique()
        }
    
    def get_county_disease_data(self, state, months=6):
        """Get disease data for a specific state"""
        if self.disease_df is None:
            return None
        
        # Convert state abbreviation if needed
        state_abbr = self._get_state_abbr(state)
        
        filtered_df = self.disease_df[
            self.disease_df['State'].str.upper() == state_abbr.upper()
        ].copy()
        
        if filtered_df.empty:
            return None
        
        # Get recent months
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Filter by time period
        filtered_df = filtered_df[
            (filtered_df['Year'] == current_year) &
            (filtered_df['Month'] >= max(1, current_month - months))
        ]
        
        # Aggregate by pathogen
        pathogen_stats = filtered_df.groupby('Pathogen').agg({
            'Number of isolates': 'sum',
            'Source Type': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        pathogens = []
        for _, row in pathogen_stats.iterrows():
            pathogens.append({
                'pathogen': row['Pathogen'],
                'total_isolates': int(row['Number of isolates']),
                'sources': row['Source Type']
            })
        
        # Monthly trend
        monthly_trend = filtered_df.groupby(['Year', 'Month']).agg({
            'Number of isolates': 'sum'
        }).reset_index()
        
        trend = []
        for _, row in monthly_trend.iterrows():
            trend.append({
                'year': int(row['Year']),
                'month': int(row['Month']),
                'total_isolates': int(row['Number of isolates'])
            })
        
        return {
            'state': state_abbr,
            'pathogens': sorted(pathogens, key=lambda x: x['total_isolates'], reverse=True),
            'monthly_trend': sorted(trend, key=lambda x: (x['year'], x['month'])),
            'total_isolates': int(filtered_df['Number of isolates'].sum()),
            'unique_pathogens': filtered_df['Pathogen'].nunique()
        }
    
    def get_correlation_analysis(self, state, county):
        """Analyze correlation between air quality and disease data"""
        air_data = self.get_county_air_quality(state, county, days=180)
        disease_data = self.get_county_disease_data(state, months=6)
        
        if not air_data or not disease_data:
            return None
        
        # Aggregate air quality by month
        monthly_air = {}
        for day in air_data['daily_data']:
            date = datetime.strptime(day['date'], '%Y-%m-%d')
            month_key = f"{date.year}-{date.month:02d}"
            if month_key not in monthly_air:
                monthly_air[month_key] = []
            if day['pm25_mean']:
                monthly_air[month_key].append(day['pm25_mean'])
        
        monthly_air_avg = {k: np.mean(v) for k, v in monthly_air.items()}
        
        # Combine with disease data
        combined = []
        for trend in disease_data['monthly_trend']:
            month_key = f"{trend['year']}-{trend['month']:02d}"
            if month_key in monthly_air_avg:
                combined.append({
                    'month': month_key,
                    'pm25': round(monthly_air_avg[month_key], 2),
                    'isolates': trend['total_isolates']
                })
        
        # Calculate correlation if we have enough data
        correlation = None
        if len(combined) >= 3:
            pm25_values = [d['pm25'] for d in combined]
            isolate_values = [d['isolates'] for d in combined]
            correlation = round(np.corrcoef(pm25_values, isolate_values)[0, 1], 3)
        
        return {
            'county': county,
            'state': state,
            'monthly_comparison': combined,
            'correlation': correlation,
            'air_quality_summary': air_data['statistics'],
            'disease_summary': {
                'total_isolates': disease_data['total_isolates'],
                'unique_pathogens': disease_data['unique_pathogens']
            }
        }
    
    def _calculate_aqi_from_pm25(self, pm25):
        """Calculate AQI from PM2.5 concentration"""
        if pm25 <= 12.0:
            return int(((50 - 0) / (12.0 - 0.0)) * (pm25 - 0.0) + 0)
        elif pm25 <= 35.4:
            return int(((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51)
        elif pm25 <= 55.4:
            return int(((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101)
        elif pm25 <= 150.4:
            return int(((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151)
        elif pm25 <= 250.4:
            return int(((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201)
        else:
            return int(((500 - 301) / (500.4 - 250.5)) * (pm25 - 250.5) + 301)
    
    def _get_state_abbr(self, state):
        """Convert state name to abbreviation"""
        state_map = {
            'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR',
            'CALIFORNIA': 'CA', 'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE',
            'FLORIDA': 'FL', 'GEORGIA': 'GA', 'HAWAII': 'HI', 'IDAHO': 'ID',
            'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA', 'KANSAS': 'KS',
            'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
            'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
            'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV',
            'NEW HAMPSHIRE': 'NH', 'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY',
            'NORTH CAROLINA': 'NC', 'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK',
            'OREGON': 'OR', 'PENNSYLVANIA': 'PA', 'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC',
            'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN', 'TEXAS': 'TX', 'UTAH': 'UT',
            'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA', 'WEST VIRGINIA': 'WV',
            'WISCONSIN': 'WI', 'WYOMING': 'WY'
        }
        
        state_upper = state.upper()
        if len(state_upper) == 2:
            return state_upper
        return state_map.get(state_upper, state_upper[:2])
    
    def analyze_with_ai(self, correlation_data):
        """Analyze correlation data using Gemini AI"""
        if not self.model:
            return "AI analysis not available. Please configure GEMINI_API_KEY."
        
        try:
            prompt = f"""
            As a public health data analyst, analyze the relationship between air quality and infectious disease data:
            
            Location: {correlation_data['county']}, {correlation_data['state']}
            
            Air Quality Summary (past 6 months):
            - Average PM2.5: {correlation_data['air_quality_summary']['avg_pm25']} µg/m³
            - Average AQI: {correlation_data['air_quality_summary']['avg_aqi']}
            - Good air days: {correlation_data['air_quality_summary']['days_good']}
            - Unhealthy air days: {correlation_data['air_quality_summary']['days_unhealthy']}
            
            Disease Summary (past 6 months):
            - Total isolates: {correlation_data['disease_summary']['total_isolates']}
            - Unique pathogens: {correlation_data['disease_summary']['unique_pathogens']}
            
            {f"Correlation coefficient: {correlation_data['correlation']}" if correlation_data['correlation'] else ""}
            
            Provide:
            1. Interpretation of the air quality levels
            2. Assessment of disease activity
            3. Potential relationships between air quality and infectious disease patterns
            4. Recommendations for public health interventions
            
            Keep response under 200 words and focus on actionable insights.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"AI analysis error: {str(e)}"

# Initialize the agent
agent = IntegratedHealthAgent()

# Routes
@app.route('/')
def index():
    return render_template('index_integrated.html')

@app.route('/api/counties', methods=['GET'])
def get_counties():
    """Get list of all counties with air quality data"""
    state = request.args.get('state')
    counties = agent.get_county_list(state)
    return jsonify({'counties': counties, 'total': len(counties)})

@app.route('/api/county/air-quality', methods=['GET'])
def get_county_air():
    """Get air quality data for a specific county"""
    state = request.args.get('state')
    county = request.args.get('county')
    days = int(request.args.get('days', 30))
    
    if not state or not county:
        return jsonify({'error': 'State and county are required'}), 400
    
    data = agent.get_county_air_quality(state, county, days)
    
    if not data:
        return jsonify({'error': 'No data found for this county'}), 404
    
    return jsonify(data)

@app.route('/api/state/disease', methods=['GET'])
def get_state_disease():
    """Get disease data for a specific state"""
    state = request.args.get('state')
    months = int(request.args.get('months', 6))
    
    if not state:
        return jsonify({'error': 'State is required'}), 400
    
    data = agent.get_county_disease_data(state, months)
    
    if not data:
        return jsonify({'error': 'No data found for this state'}), 404
    
    return jsonify(data)

@app.route('/api/correlation', methods=['GET'])
def get_correlation():
    """Get correlation analysis between air quality and disease data"""
    state = request.args.get('state')
    county = request.args.get('county')
    
    if not state or not county:
        return jsonify({'error': 'State and county are required'}), 400
    
    data = agent.get_correlation_analysis(state, county)
    
    if not data:
        return jsonify({'error': 'Insufficient data for correlation analysis'}), 404
    
    return jsonify(data)

@app.route('/api/analyze-correlation', methods=['POST'])
def analyze_correlation():
    """Analyze correlation with AI"""
    data = request.json
    state = data.get('state')
    county = data.get('county')
    
    if not state or not county:
        return jsonify({'error': 'State and county are required'}), 400
    
    correlation_data = agent.get_correlation_analysis(state, county)
    
    if not correlation_data:
        return jsonify({'error': 'Insufficient data for analysis'}), 404
    
    analysis = agent.analyze_with_ai(correlation_data)
    
    return jsonify({
        'analysis': analysis,
        'correlation_data': correlation_data
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    stats = {
        'air_quality': {
            'available': agent.air_quality_df is not None,
            'total_records': len(agent.air_quality_df) if agent.air_quality_df is not None else 0,
            'states': agent.air_quality_df['State Name'].nunique() if agent.air_quality_df is not None else 0,
            'counties': agent.air_quality_df['County Name'].nunique() if agent.air_quality_df is not None else 0
        },
        'disease': {
            'available': agent.disease_df is not None,
            'total_records': len(agent.disease_df) if agent.disease_df is not None else 0,
            'states': agent.disease_df['State'].nunique() if agent.disease_df is not None else 0,
            'pathogens': agent.disease_df['Pathogen'].nunique() if agent.disease_df is not None else 0
        },
        'ai_available': agent.model is not None
    }
    
    return jsonify(stats)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🌍 Integrated Community Health & Environmental Platform")
    print("="*80)
    print("\n✨ Starting server at http://localhost:8080")
    print("\n📝 Features:")
    print("   • County-level Air Quality Analysis")
    print("   • Infectious Disease Tracking")
    print("   • Correlation Analysis")
    print("   • AI-Powered Insights")
    print("   • Comparative Visualizations")
    print("\n🚀 Open your browser and visit: http://localhost:8080")
    print("="*80 + "\n")
    
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
