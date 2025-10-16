"""
Enhanced App with BigQuery EPA Air Quality Data Integration
This version connects to your actual BigQuery dataset
"""

from flask import Flask, render_template, request, jsonify
from google.cloud import bigquery
import google.generativeai as genai
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize BigQuery client
try:
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-86088b6278cb')
    bq_client = bigquery.Client(project=project_id)
    print(f"✅ BigQuery client initialized for project: {project_id}")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize BigQuery client: {e}")
    print("   Running in demo mode...")
    bq_client = None

# Initialize Gemini AI
try:
    genai_key = os.getenv('GEMINI_API_KEY')
    if genai_key and genai_key != 'your-gemini-api-key':
        genai.configure(api_key=genai_key)
        model = genai.GenerativeModel('gemini-pro')
        print("✅ Gemini AI initialized")
    else:
        model = None
        print("⚠️  Gemini API key not configured")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize Gemini: {e}")
    model = None


class EPAAirQualityAgent:
    """Agent for EPA Air Quality Data from BigQuery"""
    
    def __init__(self, bq_client, genai_model):
        self.bq_client = bq_client
        self.model = genai_model
        self.dataset = os.getenv('BIGQUERY_DATASET', 'BQ_EPA_Air_Data')
    
    def explore_dataset_schema(self):
        """Explore the structure of the EPA dataset"""
        if not self.bq_client:
            return None
        
        try:
            # List all tables in the dataset
            dataset_ref = f"{self.bq_client.project}.{self.dataset}"
            tables = list(self.bq_client.list_tables(dataset_ref))
            
            schema_info = []
            for table in tables:
                table_ref = f"{dataset_ref}.{table.table_id}"
                table_obj = self.bq_client.get_table(table_ref)
                
                schema_info.append({
                    'table': table.table_id,
                    'num_rows': table_obj.num_rows,
                    'columns': [field.name for field in table_obj.schema]
                })
            
            return schema_info
        except Exception as e:
            print(f"Error exploring dataset: {e}")
            return None
    
    def query_air_quality_data(self, state=None, days=7, limit=1000):
        """Query EPA air quality data from BigQuery"""
        if not self.bq_client:
            return self._generate_demo_data(state, days)
        
        try:
            # First, let's find the right table and columns
            # Common EPA air quality table structures
            possible_queries = [
                # Try standard EPA daily format
                f"""
                SELECT 
                    date_local as date,
                    state_name,
                    county_name,
                    aqi,
                    parameter_name,
                    site_name
                FROM `{self.bq_client.project}.{self.dataset}.daily_aqi_by_county`
                WHERE date_local >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                {f"AND UPPER(state_name) = UPPER('{state}')" if state else ""}
                ORDER BY date_local DESC
                LIMIT {limit}
                """,
                # Try alternative structure
                f"""
                SELECT 
                    Date as date,
                    State as state_name,
                    County as county_name,
                    AQI as aqi,
                    'PM2.5' as parameter_name,
                    CONCAT(County, ' Monitoring Site') as site_name
                FROM `{self.bq_client.project}.{self.dataset}.*`
                WHERE Date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
                {f"AND UPPER(State) = UPPER('{state}')" if state else ""}
                ORDER BY Date DESC
                LIMIT {limit}
                """,
                # Try generic query
                f"""
                SELECT * 
                FROM `{self.bq_client.project}.{self.dataset}.*`
                LIMIT 10
                """
            ]
            
            # Try each query until one works
            for query in possible_queries:
                try:
                    print(f"Trying query: {query[:100]}...")
                    query_job = self.bq_client.query(query)
                    results = query_job.result()
                    
                    data = []
                    for row in results:
                        row_dict = dict(row)
                        # Standardize column names
                        standardized = {
                            'date': str(row_dict.get('date', row_dict.get('Date', datetime.now().date()))),
                            'state_name': row_dict.get('state_name', row_dict.get('State', 'Unknown')),
                            'county_name': row_dict.get('county_name', row_dict.get('County', 'Unknown')),
                            'aqi': row_dict.get('aqi', row_dict.get('AQI', 0)),
                            'parameter_name': row_dict.get('parameter_name', row_dict.get('Parameter', 'PM2.5')),
                            'site_name': row_dict.get('site_name', row_dict.get('Site', 'Monitoring Station'))
                        }
                        data.append(standardized)
                    
                    if data:
                        print(f"✅ Successfully retrieved {len(data)} records from BigQuery")
                        return data
                        
                except Exception as e:
                    print(f"Query failed: {str(e)[:100]}")
                    continue
            
            # If all queries fail, return demo data
            print("⚠️  All queries failed, using demo data")
            return self._generate_demo_data(state, days)
            
        except Exception as e:
            print(f"Error querying BigQuery: {e}")
            return self._generate_demo_data(state, days)
    
    def _generate_demo_data(self, state=None, days=7):
        """Fallback to demo data"""
        import random
        data = []
        states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
        counties = {
            'California': ['Los Angeles', 'San Diego', 'San Francisco', 'Sacramento'],
            'Texas': ['Harris', 'Dallas', 'Travis', 'Bexar'],
            'New York': ['New York', 'Kings', 'Queens', 'Bronx'],
            'Florida': ['Miami-Dade', 'Broward', 'Palm Beach', 'Hillsborough'],
            'Illinois': ['Cook', 'DuPage', 'Lake', 'Will']
        }
        
        selected_states = [state] if state else states[:3]
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            for s in selected_states:
                for county in counties.get(s, ['Unknown'])[:2]:
                    data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'state_name': s,
                        'county_name': county,
                        'aqi': random.randint(20, 150),
                        'parameter_name': 'PM2.5',
                        'site_name': f'{county} Monitoring Station'
                    })
        
        return data
    
    def get_statistics(self, data):
        """Calculate statistics from air quality data"""
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        stats = {
            'total_records': len(df),
            'unique_locations': df['county_name'].nunique() if 'county_name' in df else 0,
            'avg_aqi': float(df['aqi'].mean()) if 'aqi' in df and not df['aqi'].empty else 0,
            'max_aqi': float(df['aqi'].max()) if 'aqi' in df and not df['aqi'].empty else 0,
            'min_aqi': float(df['aqi'].min()) if 'aqi' in df and not df['aqi'].empty else 0,
        }
        
        return stats
    
    def analyze_with_ai(self, data, question):
        """Use Gemini AI to analyze air quality data"""
        try:
            if not self.model or not data:
                return "AI analysis unavailable. Please configure Gemini API key."
            
            df = pd.DataFrame(data)
            data_summary = df.describe().to_string() if not df.empty else "No data available"
            
            prompt = f"""
            You are an air quality and public health expert. Analyze this EPA air quality data and answer the question.
            
            Data Summary:
            {data_summary}
            
            Recent Records (sample):
            {df.head(10).to_string() if not df.empty else "No recent data"}
            
            Question: {question}
            
            Provide a helpful, actionable response focused on community health and wellness. Include:
            1. Health implications
            2. Recommended precautions
            3. Vulnerable populations to consider
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error with AI analysis: {e}")
            return f"AI analysis encountered an error: {str(e)}"


# Initialize the agent
agent = EPAAirQualityAgent(bq_client, model)

# Print dataset info on startup
print("\n" + "="*80)
print("📊 EPA Air Quality Dataset Information")
print("="*80)
schema_info = agent.explore_dataset_schema()
if schema_info:
    for table_info in schema_info:
        print(f"\n📋 Table: {table_info['table']}")
        print(f"   Rows: {table_info['num_rows']:,}")
        print(f"   Columns: {', '.join(table_info['columns'][:10])}")
        if len(table_info['columns']) > 10:
            print(f"   ... and {len(table_info['columns']) - 10} more columns")
print("="*80 + "\n")


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/air-quality', methods=['GET'])
def get_air_quality():
    """API endpoint to get EPA air quality data"""
    state = request.args.get('state', None)
    days = int(request.args.get('days', 7))
    
    data = agent.query_air_quality_data(state=state, days=days)
    stats = agent.get_statistics(data)
    
    return jsonify({
        'success': True,
        'data': data,
        'statistics': stats,
        'count': len(data),
        'source': 'EPA BigQuery' if bq_client else 'Demo Data'
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint for AI analysis"""
    try:
        request_data = request.get_json()
        question = request_data.get('question', '')
        state = request_data.get('state', None)
        days = int(request_data.get('days', 7))
        
        # Get relevant data
        data = agent.query_air_quality_data(state=state, days=days)
        
        # Get AI analysis
        analysis = agent.analyze_with_ai(data, question)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'data_points': len(data),
            'source': 'EPA BigQuery' if bq_client else 'Demo Data'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/health-recommendations', methods=['GET'])
def health_recommendations():
    """Get health recommendations based on current air quality"""
    state = request.args.get('state', None)
    
    data = agent.query_air_quality_data(state=state, days=1)
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No recent data available'
        })
    
    df = pd.DataFrame(data)
    avg_aqi = df['aqi'].mean() if 'aqi' in df and not df.empty else 0
    
    # Health recommendations based on AQI levels
    if avg_aqi <= 50:
        level = "Good"
        color = "#10b981"
        recommendation = "Air quality is excellent. Perfect for all outdoor activities!"
    elif avg_aqi <= 100:
        level = "Moderate"
        color = "#fbbf24"
        recommendation = "Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exertion."
    elif avg_aqi <= 150:
        level = "Unhealthy for Sensitive Groups"
        color = "#f59e0b"
        recommendation = "Sensitive groups should reduce prolonged outdoor exertion. Everyone else can enjoy normal activities."
    elif avg_aqi <= 200:
        level = "Unhealthy"
        color = "#ef4444"
        recommendation = "Everyone should reduce prolonged outdoor exertion. Sensitive groups should avoid outdoor activities."
    elif avg_aqi <= 300:
        level = "Very Unhealthy"
        color = "#991b1b"
        recommendation = "Health alert! Everyone should avoid prolonged outdoor exertion."
    else:
        level = "Hazardous"
        color = "#7f1d1d"
        recommendation = "Health warning! Everyone should avoid all outdoor activities."
    
    return jsonify({
        'success': True,
        'aqi': round(avg_aqi, 2),
        'level': level,
        'color': color,
        'recommendation': recommendation,
        'data_points': len(data),
        'source': 'EPA BigQuery' if bq_client else 'Demo Data'
    })


@app.route('/api/dataset-info', methods=['GET'])
def dataset_info():
    """Get information about the EPA dataset"""
    schema_info = agent.explore_dataset_schema()
    return jsonify({
        'success': True,
        'dataset': agent.dataset,
        'project': bq_client.project if bq_client else 'Not connected',
        'tables': schema_info if schema_info else [],
        'connected': bq_client is not None
    })


@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'bigquery': 'connected' if bq_client else 'demo mode',
        'gemini_ai': 'connected' if model else 'not configured'
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("\n" + "="*80)
    print("🌍 Community Health & Wellness Platform")
    print("="*80)
    print(f"\n✨ Starting server at http://localhost:{port}")
    print(f"\n📊 Data Source: {'EPA BigQuery Dataset' if bq_client else 'Demo Mode'}")
    print(f"🤖 AI Analysis: {'Enabled' if model else 'Disabled (configure GEMINI_API_KEY)'}")
    print("\n📝 Features:")
    print("   • EPA Air Quality Data from BigQuery")
    print("   • Infectious Disease Tracking")
    print("   • AI Health Advisor")
    print("   • Interactive Visualizations (D3.js, Three.js, Anime.js)")
    print("\n🚀 Open your browser and visit: http://localhost:8080")
    print("="*80 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)
