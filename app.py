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
    bq_client = bigquery.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT'))
except Exception as e:
    print(f"Warning: Could not initialize BigQuery client: {e}")
    bq_client = None

# Initialize Gemini AI
try:
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Warning: Could not initialize Gemini: {e}")
    model = None


class AirQualityAgent:
    """Google SDK Agent for Air Quality Analysis"""
    
    def __init__(self, bq_client, genai_model):
        self.bq_client = bq_client
        self.model = genai_model
    
    def query_air_quality_data(self, state=None, days=7):
        """Query air quality data from BigQuery"""
        try:
            dataset = os.getenv('BIGQUERY_DATASET', 'air_quality_dataset')
            table = os.getenv('BIGQUERY_TABLE', 'air_quality_data')
            
            query = f"""
            SELECT 
                date,
                state_name,
                county_name,
                aqi,
                parameter_name,
                site_name
            FROM `{os.getenv('GOOGLE_CLOUD_PROJECT')}.{dataset}.{table}`
            WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
            """
            
            if state:
                query += f" AND UPPER(state_name) = UPPER('{state}')"
            
            query += " ORDER BY date DESC LIMIT 1000"
            
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error querying BigQuery: {e}")
            return []
    
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
    return render_template('index.html')


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


@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
