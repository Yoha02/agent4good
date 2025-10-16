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

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class EPAAirQualityAgent:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-86088b6278cb')
        self.dataset_id = os.getenv('BIGQUERY_DATASET', 'BQ_EPA_Air_Data')
        self.local_csv_path = os.getenv('LOCAL_EPA_CSV', r'c:\Users\semaa\OneDrive\Documents\Google\Agents4Impact10162025\AIr Quality\daily_88101_2025\daily_88101_2025.csv')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Try to initialize BigQuery client
        self.bq_client = None
        self.use_bigquery = False
        self.use_local_csv = False
        self.df = None
        
        # Column mappings for CSV file
        self.csv_columns = {
            'date': 'Date Local',
            'state': 'State Name',
            'county': 'County Name',
            'city': 'City Name',
            'parameter': 'Parameter Name',
            'aqi': 'AQI',
            'mean_value': 'Arithmetic Mean',
            'max_value': '1st Max Value',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'site_name': 'Local Site Name',
            'units': 'Units of Measure'
        }
        
        self._initialize_data_sources()
        self._initialize_ai()
        
    def _initialize_data_sources(self):
        """Initialize BigQuery and/or local CSV data sources"""
        print("\n" + "="*80)
        print("🌍 EPA Air Quality Data Source Initialization")
        print("="*80)
        
        # Try BigQuery first
        try:
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
                self.bq_client = bigquery.Client(project=self.project_id)
                
                # Test connection
                query = f"SELECT table_id FROM `{self.project_id}.{self.dataset_id}.__TABLES__` LIMIT 1"
                self.bq_client.query(query).result()
                
                self.use_bigquery = True
                print("✅ BigQuery Connection: SUCCESS")
                self._explore_bigquery_schema()
            else:
                print("⚠️  BigQuery credentials not found")
        except Exception as e:
            print(f"⚠️  BigQuery Connection: FAILED - {str(e)}")
        
        # Try local CSV file
        if os.path.exists(self.local_csv_path):
            try:
                print(f"\n📂 Loading local CSV file...")
                print(f"   Path: {self.local_csv_path}")
                
                # Read CSV with proper dtypes to handle large file efficiently
                dtype_dict = {
                    'State Code': str,
                    'County Code': str,
                    'Site Num': str,
                    'AQI': 'Int64'  # Use nullable integer
                }
                
                self.df = pd.read_csv(
                    self.local_csv_path,
                    dtype=dtype_dict,
                    parse_dates=['Date Local']
                )
                
                self.use_local_csv = True
                print(f"✅ Local CSV Loaded: {len(self.df):,} rows")
                print(f"   Date Range: {self.df['Date Local'].min()} to {self.df['Date Local'].max()}")
                print(f"   States: {self.df['State Name'].nunique()}")
                print(f"   Counties: {self.df['County Name'].nunique()}")
                print(f"   Parameters: {self.df['Parameter Name'].unique()[:3]}...")
                
            except Exception as e:
                print(f"⚠️  Local CSV Loading: FAILED - {str(e)}")
        else:
            print(f"⚠️  Local CSV not found at: {self.local_csv_path}")
        
        # Determine which source to use
        if self.use_local_csv:
            print("\n🎯 Primary Data Source: LOCAL CSV")
        elif self.use_bigquery:
            print("\n🎯 Primary Data Source: BIGQUERY")
        else:
            print("\n⚠️  No data sources available - will use DEMO MODE")
        
        print("="*80 + "\n")
    
    def _explore_bigquery_schema(self):
        """Explore BigQuery dataset structure"""
        if not self.bq_client:
            return
        
        try:
            print(f"\n📊 BigQuery Dataset: {self.dataset_id}")
            
            # List all tables
            tables = self.bq_client.list_tables(f"{self.project_id}.{self.dataset_id}")
            table_list = list(tables)
            
            print(f"📋 Available Tables ({len(table_list)}):")
            for table in table_list[:10]:  # Show first 10
                table_ref = f"{self.project_id}.{self.dataset_id}.{table.table_id}"
                table_obj = self.bq_client.get_table(table_ref)
                print(f"   • {table.table_id} ({table_obj.num_rows:,} rows)")
                
        except Exception as e:
            print(f"   ⚠️  Could not explore schema: {str(e)}")
    
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
    
    def query_air_quality_data(self, state=None, county=None, city=None, days=7):
        """Query air quality data from available sources"""
        
        # Use local CSV if available
        if self.use_local_csv and self.df is not None:
            return self._query_from_csv(state, county, city, days)
        
        # Use BigQuery if available
        elif self.use_bigquery and self.bq_client:
            return self._query_from_bigquery(state, county, city, days)
        
        # Fallback to demo data
        else:
            return self._generate_demo_data(state, days)
    
    def _query_from_csv(self, state=None, county=None, city=None, days=7):
        """Query data from local CSV file"""
        try:
            # Filter by date
            end_date = self.df['Date Local'].max()
            start_date = end_date - timedelta(days=days)
            
            filtered_df = self.df[self.df['Date Local'] >= start_date].copy()
            
            # Filter by location
            if state:
                filtered_df = filtered_df[filtered_df['State Name'].str.contains(state, case=False, na=False)]
            if county:
                filtered_df = filtered_df[filtered_df['County Name'].str.contains(county, case=False, na=False)]
            if city:
                filtered_df = filtered_df[filtered_df['City Name'].str.contains(city, case=False, na=False)]
            
            if filtered_df.empty:
                return self._generate_demo_data(state or "No data", days)
            
            # Group by date and calculate statistics
            daily_stats = filtered_df.groupby('Date Local').agg({
                'AQI': ['mean', 'max', 'min'],
                'Arithmetic Mean': 'mean',
                '1st Max Value': 'max',
                'State Name': 'first',
                'County Name': 'first'
            }).reset_index()
            
            # Format results
            results = []
            for _, row in daily_stats.iterrows():
                aqi_mean = row[('AQI', 'mean')]
                aqi_max = row[('AQI', 'max')]
                
                # Handle NaN values
                if pd.isna(aqi_mean):
                    aqi_mean = row[('Arithmetic Mean', 'mean')] * 10  # Approximate AQI from PM2.5
                if pd.isna(aqi_max):
                    aqi_max = row[('1st Max Value', 'max')] * 10
                
                results.append({
                    'date': row['Date Local'].strftime('%Y-%m-%d'),
                    'aqi': int(aqi_mean) if not pd.isna(aqi_mean) else 50,
                    'max_aqi': int(aqi_max) if not pd.isna(aqi_max) else 50,
                    'pm25': round(row[('Arithmetic Mean', 'mean')], 2) if not pd.isna(row[('Arithmetic Mean', 'mean')]) else None,
                    'location': f"{row[('County Name', 'first')]}, {row[('State Name', 'first')]}",
                    'data_source': 'Local CSV'
                })
            
            return sorted(results, key=lambda x: x['date'])
            
        except Exception as e:
            print(f"Error querying CSV: {str(e)}")
            return self._generate_demo_data(state or "Error", days)
    
    def _query_from_bigquery(self, state=None, county=None, city=None, days=7):
        """Query data from BigQuery"""
        try:
            # Build query with filters
            where_clauses = [f"date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)"]
            
            if state:
                where_clauses.append(f"LOWER(state_name) LIKE LOWER('%{state}%')")
            if county:
                where_clauses.append(f"LOWER(county_name) LIKE LOWER('%{county}%')")
            if city:
                where_clauses.append(f"LOWER(city_name) LIKE LOWER('%{city}%')")
            
            where_clause = " AND ".join(where_clauses)
            
            # Try multiple table name patterns
            table_patterns = [
                'daily_88101_2025',
                'daily_aqi_by_county',
                'epa_daily_air_quality'
            ]
            
            for table_name in table_patterns:
                try:
                    query = f"""
                        SELECT 
                            date,
                            state_name,
                            county_name,
                            AVG(aqi) as avg_aqi,
                            MAX(aqi) as max_aqi,
                            AVG(arithmetic_mean) as avg_pm25
                        FROM `{self.project_id}.{self.dataset_id}.{table_name}`
                        WHERE {where_clause}
                        GROUP BY date, state_name, county_name
                        ORDER BY date DESC
                        LIMIT 100
                    """
                    
                    results = self.bq_client.query(query).result()
                    
                    data = []
                    for row in results:
                        data.append({
                            'date': row['date'].strftime('%Y-%m-%d'),
                            'aqi': int(row['avg_aqi']) if row['avg_aqi'] else 50,
                            'max_aqi': int(row['max_aqi']) if row['max_aqi'] else 50,
                            'pm25': round(row['avg_pm25'], 2) if row['avg_pm25'] else None,
                            'location': f"{row['county_name']}, {row['state_name']}",
                            'data_source': 'BigQuery'
                        })
                    
                    if data:
                        return data
                        
                except Exception as e:
                    continue
            
            # If all queries failed
            return self._generate_demo_data(state or "BigQuery", days)
            
        except Exception as e:
            print(f"BigQuery error: {str(e)}")
            return self._generate_demo_data(state or "Error", days)
    
    def _generate_demo_data(self, location="Demo Location", days=7):
        """Generate demo data as fallback"""
        import random
        
        data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
            base_aqi = 50 + random.randint(-20, 40)
            
            data.append({
                'date': date,
                'aqi': base_aqi,
                'max_aqi': base_aqi + random.randint(5, 15),
                'pm25': round(base_aqi / 10 + random.uniform(-2, 2), 2),
                'location': location,
                'data_source': 'Demo Mode'
            })
        
        return data
    
    def get_statistics(self, data):
        """Calculate statistics from data"""
        if not data:
            return {}
        
        aqi_values = [d['aqi'] for d in data if d.get('aqi')]
        
        return {
            'average_aqi': round(sum(aqi_values) / len(aqi_values), 1) if aqi_values else 0,
            'max_aqi': max(aqi_values) if aqi_values else 0,
            'min_aqi': min(aqi_values) if aqi_values else 0,
            'days_good': sum(1 for aqi in aqi_values if aqi <= 50),
            'days_moderate': sum(1 for aqi in aqi_values if 51 <= aqi <= 100),
            'days_unhealthy': sum(1 for aqi in aqi_values if aqi > 100),
            'data_source': data[0].get('data_source', 'Unknown')
        }
    
    def analyze_with_ai(self, data, user_question=None):
        """Analyze data using Gemini AI"""
        if not self.model:
            return "AI analysis not available. Please configure GEMINI_API_KEY."
        
        try:
            stats = self.get_statistics(data)
            
            prompt = f"""
            As an air quality health advisor, analyze this data:
            
            Location: {data[0].get('location', 'Unknown')}
            Average AQI: {stats['average_aqi']}
            Max AQI: {stats['max_aqi']}
            Days with good air (AQI ≤ 50): {stats['days_good']}
            Days with moderate air (AQI 51-100): {stats['days_moderate']}
            Days with unhealthy air (AQI > 100): {stats['days_unhealthy']}
            
            {f'User question: {user_question}' if user_question else ''}
            
            Provide:
            1. Brief health assessment
            2. Recommendations for sensitive groups
            3. Outdoor activity guidance
            
            Keep response under 150 words.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"AI analysis error: {str(e)}"

# Initialize the agent
agent = EPAAirQualityAgent()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/air-quality', methods=['GET'])
def get_air_quality():
    """Get air quality data"""
    state = request.args.get('state', 'California')
    county = request.args.get('county')
    city = request.args.get('city')
    days = int(request.args.get('days', 7))
    
    data = agent.query_air_quality_data(state, county, city, days)
    stats = agent.get_statistics(data)
    
    return jsonify({
        'data': data,
        'statistics': stats,
        'location': f"{county or city or state}",
        'data_source': data[0].get('data_source', 'Unknown') if data else 'No data'
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze air quality with AI"""
    data = request.json
    state = data.get('state', 'California')
    question = data.get('question', '')
    days = int(data.get('days', 7))
    
    air_data = agent.query_air_quality_data(state=state, days=days)
    analysis = agent.analyze_with_ai(air_data, question)
    
    return jsonify({
        'analysis': analysis,
        'statistics': agent.get_statistics(air_data)
    })

@app.route('/api/dataset-info', methods=['GET'])
def dataset_info():
    """Get information about available data sources"""
    info = {
        'bigquery_available': agent.use_bigquery,
        'local_csv_available': agent.use_local_csv,
        'ai_available': agent.model is not None,
        'primary_source': 'Local CSV' if agent.use_local_csv else ('BigQuery' if agent.use_bigquery else 'Demo Mode')
    }
    
    if agent.use_local_csv and agent.df is not None:
        info['csv_info'] = {
            'rows': len(agent.df),
            'date_range': f"{agent.df['Date Local'].min()} to {agent.df['Date Local'].max()}",
            'states': agent.df['State Name'].nunique(),
            'counties': agent.df['County Name'].nunique(),
            'parameters': agent.df['Parameter Name'].unique().tolist()
        }
    
    return jsonify(info)

@app.route('/api/health-recommendations', methods=['GET'])
def health_recommendations():
    """Get health recommendations based on current conditions"""
    state = request.args.get('state', 'California')
    
    data = agent.query_air_quality_data(state=state, days=1)
    
    if not data:
        return jsonify({'error': 'No data available'}), 404
    
    current_aqi = data[-1]['aqi']
    
    recommendations = {
        'aqi': current_aqi,
        'category': get_aqi_category(current_aqi),
        'color': get_aqi_color(current_aqi),
        'recommendations': get_health_recommendations(current_aqi)
    }
    
    return jsonify(recommendations)

def get_aqi_category(aqi):
    """Get AQI category"""
    if aqi <= 50:
        return 'Good'
    elif aqi <= 100:
        return 'Moderate'
    elif aqi <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif aqi <= 200:
        return 'Unhealthy'
    elif aqi <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'

def get_aqi_color(aqi):
    """Get AQI color"""
    if aqi <= 50:
        return '#00E400'  # Green
    elif aqi <= 100:
        return '#FFFF00'  # Yellow
    elif aqi <= 150:
        return '#FF7E00'  # Orange
    elif aqi <= 200:
        return '#FF0000'  # Red
    elif aqi <= 300:
        return '#8F3F97'  # Purple
    else:
        return '#7E0023'  # Maroon

def get_health_recommendations(aqi):
    """Get health recommendations based on AQI"""
    if aqi <= 50:
        return {
            'general': 'Air quality is excellent. Perfect day for outdoor activities!',
            'sensitive': 'No precautions needed.',
            'everyone': 'Enjoy your outdoor activities!'
        }
    elif aqi <= 100:
        return {
            'general': 'Air quality is acceptable. Most people can enjoy outdoor activities.',
            'sensitive': 'Unusually sensitive people should consider limiting prolonged outdoor exertion.',
            'everyone': 'It\'s OK to be active outside.'
        }
    elif aqi <= 150:
        return {
            'general': 'Sensitive groups may experience health effects.',
            'sensitive': 'Reduce prolonged or heavy outdoor exertion. Take more breaks, do less intense activities.',
            'everyone': 'It\'s OK to be active outside, especially for short activities.'
        }
    elif aqi <= 200:
        return {
            'general': 'Everyone may begin to experience health effects.',
            'sensitive': 'Avoid prolonged or heavy outdoor exertion. Schedule outdoor activities when air quality is better.',
            'everyone': 'Reduce prolonged or heavy outdoor exertion. Take more breaks during outdoor activities.'
        }
    else:
        return {
            'general': 'Health warnings. Everyone may experience serious health effects.',
            'sensitive': 'Avoid all outdoor physical activity.',
            'everyone': 'Avoid prolonged or heavy outdoor exertion. Consider moving activities indoors or rescheduling.'
        }

if __name__ == '__main__':
    print("\n" + "="*80)
    if agent.use_local_csv:
        print("🌍 Community Health & Wellness Platform - LOCAL CSV MODE")
    elif agent.use_bigquery:
        print("🌍 Community Health & Wellness Platform - BIGQUERY MODE")
    else:
        print("🌍 Community Health & Wellness Platform - DEMO MODE")
    print("="*80)
    print("\n✨ Starting server at http://localhost:8080")
    print("\n📝 Features:")
    print("   • Real EPA Air Quality Data (from local CSV)")
    print("   • AI Health Advisor (Gemini)")
    print("   • Interactive Visualizations")
    print("   • Health Recommendations")
    print("\n🚀 Open your browser and visit: http://localhost:8080")
    print("="*80 + "\n")
    
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
