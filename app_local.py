from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

print("[OK] Starting Flask app in local development mode")

# Mock data for local testing
class MockAirQualityAgent:
    """Mock agent for local testing"""
    
    def query_air_quality_data(self, state=None, days=7):
        """Generate mock air quality data"""
        data = []
        states = ['California', 'Texas', 'New York', 'Florida', 'Illinois']
        counties = {
            'California': ['Los Angeles', 'San Diego', 'San Francisco'],
            'Texas': ['Harris', 'Dallas', 'Travis'],
            'New York': ['New York', 'Kings', 'Queens'],
            'Florida': ['Miami-Dade', 'Broward', 'Palm Beach'],
            'Illinois': ['Cook', 'DuPage', 'Lake']
        }
        
        selected_states = [state] if state and state in states else states[:3]
        
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
        """Mock AI analysis"""
        df = pd.DataFrame(data)
        avg_aqi = df['aqi'].mean() if not df.empty else 50
        
        responses = [
            f"Based on the air quality data, the average AQI is {avg_aqi:.1f}. This indicates moderate air quality.",
            f"The PM2.5 levels in your area are within acceptable ranges. Consider outdoor activities during morning hours.",
            f"Air quality monitoring shows seasonal variations. Stay informed about daily AQI levels for better health planning.",
        ]
        
        return random.choice(responses)
    
    def get_statistics(self, data):
        """Calculate statistics from mock data"""
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

# Initialize the mock agent
agent = MockAirQualityAgent()
ADK_AGENT_AVAILABLE = False  # Set to False for local testing

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

@app.route('/api/agent-chat', methods=['POST'])
def agent_chat():
    """API endpoint for agent chat - fallback mode"""
    try:
        request_data = request.get_json()
        question = request_data.get('question', '')
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        # Use mock AI since ADK agent is not available
        state = request_data.get('state', None)
        days = int(request_data.get('days', 7))
        data = agent.query_air_quality_data(state=state, days=days)
        analysis = agent.analyze_with_ai(data, question)
        
        return jsonify({
            'success': True,
            'response': analysis,
            'agent': 'Mock AI (Local Development Mode)',
            'data_points': len(data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/officials-login')
def officials_login():
    """Public Health Officials login page"""
    return render_template('officials_login.html')

@app.route('/officials-dashboard')
def officials_dashboard():
    """Public Health Officials dashboard - requires authentication in production"""
    return render_template('officials_dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'local_development',
        'adk_agent': 'unavailable (local mode)'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"[OK] Starting Flask app on port {port}")
    print(f"[INFO] Visit http://localhost:{port} to view the application")
    print(f"[INFO] Running in local development mode with mock data")
    app.run(host='0.0.0.0', port=port, debug=True)