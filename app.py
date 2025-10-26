from flask import Flask, render_template, request, jsonify, send_file
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json
import random
import zipcodes
import requests
from PIL import Image
from io import BytesIO
from epa_service import EPAAirQualityService
from epa_aqs_service import EPAAQSService
from location_service_comprehensive import ComprehensiveLocationService
from google_weather_service import GoogleWeatherService
from google_pollen_service import GooglePollenService
from google.cloud import storage, bigquery
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# GCS Configuration
GCS_BUCKET_NAME = 'agent4good-report-attachments'
GCP_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

print("[OK] Starting Flask app with EPA API integration")

# Initialize GCS client
try:
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    try:
        bucket = storage_client.get_bucket(GCS_BUCKET_NAME)
        print(f"[OK] Connected to GCS bucket: {GCS_BUCKET_NAME}")
    except Exception as e:
        print(f"[INFO] Bucket not found, creating: {GCS_BUCKET_NAME}")
        bucket = storage_client.create_bucket(GCS_BUCKET_NAME, location='us-central1')
        print(f"[OK] Created GCS bucket: {GCS_BUCKET_NAME}")
    GCS_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] GCS initialization failed: {e}")
    GCS_AVAILABLE = False
    storage_client = None
    bucket = None

# Initialize services
try:
    epa_service = EPAAirQualityService()
    epa_aqs_service = EPAAQSService()
    location_service = ComprehensiveLocationService()
    weather_service = GoogleWeatherService()
    pollen_service = GooglePollenService()
    EPA_AVAILABLE = True
    print("[OK] EPA API service initialized successfully")
    print("[OK] EPA AQS service initialized for detailed pollutant data")
    print("[OK] Google Weather & Pollen services initialized")
except Exception as e:
    print(f"[WARNING] Service initialization: {e}")
    EPA_AVAILABLE = False
    epa_service = None
    epa_aqs_service = None
    location_service = ComprehensiveLocationService()
    weather_service = None
    pollen_service = None

# Import ADK agent (optional, for backwards compatibility)
try:
    from multi_tool_agent_bquery_tools.agent import call_agent as call_adk_agent
    ADK_AGENT_AVAILABLE = True
    print("[OK] ADK Agent loaded successfully!")
except Exception as e:
    print(f"[INFO] ADK Agent not available (optional): {e}")
    ADK_AGENT_AVAILABLE = False


class AirQualityAgent:
    """Google SDK Agent for Air Quality Analysis"""
    
    def __init__(self, bq_client, genai_model):
        self.bq_client = bq_client
        self.model = genai_model
    
    def query_air_quality_data(self, state=None, days=7):
        """Query air quality data from public BigQuery EPA dataset"""
        if not self.bq_client:
            print("[BQ] No BigQuery client, using demo data")
            return self._generate_demo_data(state, days)
            
        try:
            # Use public EPA dataset
            query = f"""
            SELECT 
                date_local as date,
                state_name,
                county_name,
                CAST(aqi AS INT64) as aqi,
                parameter_name,
                local_site_name as site_name,
                arithmetic_mean as pm25_mean
            FROM `bigquery-public-data.epa_historical_air_quality.pm25_frm_daily_summary`
            WHERE date_local >= DATE_SUB(DATE('2021-11-08'), INTERVAL {days} DAY)
            AND aqi IS NOT NULL
            """
            
            if state:
                query += f" AND UPPER(state_name) = UPPER('{state}')"
            
            query += " ORDER BY date_local DESC LIMIT 1000"
            
            print(f"[BQ] Querying public EPA dataset for {state or 'all states'}, last {days} days")
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            data = [dict(row) for row in results]
            
            if data:
                print(f"[BQ] Retrieved {len(data)} records from public EPA dataset")
                return data
            else:
                print(f"[BQ] No data found, using demo data")
                return self._generate_demo_data(state, days)
                
        except Exception as e:
            print(f"[BQ ERROR] {e}")
            print("[BQ] Falling back to demo data")
            return self._generate_demo_data(state, days)
    
    def _generate_demo_data(self, state=None, days=7):
        """Generate demo data when BigQuery is unavailable"""
        import random
        data = []
        states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
        counties = {
            'California': ['Los Angeles', 'San Diego', 'San Francisco'],
            'Texas': ['Harris', 'Dallas', 'Travis'],
            'New York': ['New York', 'Kings', 'Queens'],
            'Florida': ['Miami-Dade', 'Broward', 'Palm Beach'],
            'Illinois': ['Cook', 'DuPage', 'Lake']
        }
        
        selected_states = [state] if state else states[:3]
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            for s in selected_states:
                if s in counties:
                    for county in counties[s][:2]:
                        data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'state_name': s,
                            'county_name': county,
                            'aqi': random.randint(20, 120),
                            'parameter_name': 'PM2.5',
                            'site_name': f'{county} Monitoring Station',
                            'pm25_mean': round(random.uniform(5.0, 25.0), 2)
                        })
        
        return data
    
    def analyze_with_ai(self, data, question):
        """Use Gemini AI to analyze air quality data"""
        try:
            if not self.model or not data:
                return "AI analysis unavailable at the moment."
            
            # Prepare data summary for AI
            df = pd.DataFrame(data)
            data_summary = df.describe().to_string() if not df.empty else "No data available"
            
            prompt = f"""
            You are an air quality health advisor. Analyze this air quality data and answer the question.
            
            Data Summary:
            {data_summary}
            
            Recent Records:
            {df.head(10).to_string() if not df.empty else "No recent data"}
            
            Question: {question}
            
            Provide a helpful, actionable response focused on community health and wellness.
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error with AI analysis: {e}")
            return "Unable to generate AI analysis at this time."
    
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


# Initialize the agent
agent = AirQualityAgent(bq_client, model)


@app.route('/')
def index():
    """Main dashboard page"""
    # Use the same Google API key for Maps (works for multiple Google services)
    google_maps_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
    return render_template('index.html', google_maps_key=google_maps_key)


@app.route('/api/air-quality', methods=['GET'])
def get_air_quality():
    """API endpoint to get air quality data"""
    state = request.args.get('state', None)
    days = int(request.args.get('days', 7))
    
    data = agent.query_air_quality_data(state=state, days=days)
    stats = agent.get_statistics(data)
    
    return jsonify({
        'success': True,
        'data': data,
        'statistics': stats,
        'count': len(data)
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
            'data_points': len(data)
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
        color = "#00E400"
        recommendation = "Air quality is satisfactory. Enjoy outdoor activities!"
    elif avg_aqi <= 100:
        level = "Moderate"
        color = "#FFFF00"
        recommendation = "Air quality is acceptable. Sensitive individuals should consider limiting prolonged outdoor exertion."
    elif avg_aqi <= 150:
        level = "Unhealthy for Sensitive Groups"
        color = "#FF7E00"
        recommendation = "Sensitive groups should reduce prolonged outdoor exertion."
    elif avg_aqi <= 200:
        level = "Unhealthy"
        color = "#FF0000"
        recommendation = "Everyone should reduce prolonged outdoor exertion."
    elif avg_aqi <= 300:
        level = "Very Unhealthy"
        color = "#8F3F97"
        recommendation = "Everyone should avoid prolonged outdoor exertion."
    else:
        level = "Hazardous"
        color = "#7E0023"
        recommendation = "Everyone should avoid outdoor activities."
    
    return jsonify({
        'success': True,
        'aqi': round(avg_aqi, 2),
        'level': level,
        'color': color,
        'recommendation': recommendation,
        'data_points': len(data)
    })


@app.route('/api/agent-chat', methods=['POST'])
def agent_chat():
    """API endpoint for ADK agent chat"""
    try:
        if not ADK_AGENT_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'ADK Agent not available. Using fallback AI.'
            }), 503
        
        request_data = request.get_json()
        question = request_data.get('question', '')
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        # Call the ADK agent
        response = call_adk_agent(question)
        
        return jsonify({
            'success': True,
            'response': response,
            'agent': 'ADK Multi-Agent System'
        })
    except Exception as e:
        # Fallback to original AI if ADK agent fails
        try:
            state = request_data.get('state', None)
            days = int(request_data.get('days', 7))
            data = agent.query_air_quality_data(state=state, days=days)
            analysis = agent.analyze_with_ai(data, question)
            
            return jsonify({
                'success': True,
                'response': analysis,
                'agent': 'Gemini AI (Fallback)',
                'data_points': len(data)
            })
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'error': str(e),
                'fallback_error': str(fallback_error)
            }), 500


@app.route('/acknowledgements')
def acknowledgements():
    """Acknowledgements page"""
    return render_template('acknowledgements.html')


@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'adk_agent': 'available' if ADK_AGENT_AVAILABLE else 'unavailable'
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
