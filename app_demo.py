from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'demo-secret-key'

# Demo data generator for air quality
def generate_demo_data(state=None, days=7):
    """Generate demo air quality data"""
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
                    'parameter_name': 'Ozone',
                    'site_name': f'{county} Monitoring Station'
                })
    
    return data

# Demo data generator for infectious diseases
def generate_disease_data(disease=None, days=7):
    """Generate demo infectious disease data"""
    diseases = ['COVID-19', 'Influenza', 'RSV', 'Norovirus']
    selected_disease = disease if disease else random.choice(diseases)
    
    data = []
    for day in range(days):
        date = datetime.now() - timedelta(days=day)
        cases = random.randint(50, 500)
        trend = random.choice(['up', 'down', 'stable'])
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'disease': selected_disease,
            'cases': cases,
            'trend': trend,
            'risk_level': 'low' if cases < 150 else 'moderate' if cases < 300 else 'high'
        })
    
    return data


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/air-quality', methods=['GET'])
def get_air_quality():
    """API endpoint to get air quality data"""
    state = request.args.get('state', None)
    days = int(request.args.get('days', 7))
    
    data = generate_demo_data(state=state, days=days)
    
    # Calculate statistics
    aqi_values = [d['aqi'] for d in data]
    stats = {
        'total_records': len(data),
        'unique_locations': len(set(d['county_name'] for d in data)),
        'avg_aqi': sum(aqi_values) / len(aqi_values) if aqi_values else 0,
        'max_aqi': max(aqi_values) if aqi_values else 0,
        'min_aqi': min(aqi_values) if aqi_values else 0,
    }
    
    return jsonify({
        'success': True,
        'data': data,
        'statistics': stats,
        'count': len(data)
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint for AI analysis (demo mode)"""
    try:
        request_data = request.get_json()
        question = request_data.get('question', '')
        
        # Demo AI responses
        responses = {
            'health': 'Based on current air quality data, individuals with respiratory conditions should limit outdoor activities. The AQI levels suggest moderate air quality, which is generally acceptable for most people but may cause concern for sensitive groups.',
            'exercise': 'For most people, outdoor exercise is safe at current AQI levels. However, if you have asthma or other respiratory conditions, consider indoor alternatives or exercise during early morning hours when air quality tends to be better.',
            'children': 'Children can play outdoors at current air quality levels, but monitor for any signs of difficulty breathing. Reduce prolonged or heavy outdoor activities if AQI exceeds 100.',
            'default': 'Air quality varies by location and time. Generally, an AQI below 50 is good, 51-100 is moderate, and above 150 may pose health risks for sensitive groups. Stay informed and adjust outdoor activities accordingly.'
        }
        
        # Simple keyword matching for demo
        question_lower = question.lower()
        if any(word in question_lower for word in ['health', 'risk', 'impact']):
            analysis = responses['health']
        elif any(word in question_lower for word in ['exercise', 'run', 'outdoor']):
            analysis = responses['exercise']
        elif any(word in question_lower for word in ['children', 'kids', 'play']):
            analysis = responses['children']
        else:
            analysis = responses['default']
        
        return jsonify({
            'success': True,
            'analysis': f"🤖 Demo AI Response:\n\n{analysis}\n\n💡 Note: This is a demo response. Connect to Gemini AI for real-time intelligent analysis.",
            'data_points': 50
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
    data = generate_demo_data(state=state, days=1)
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No recent data available'
        })
    
    # Calculate average AQI
    aqi_values = [d['aqi'] for d in data]
    avg_aqi = sum(aqi_values) / len(aqi_values) if aqi_values else 0
    
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



@app.route('/api/infectious-diseases', methods=['GET'])
def get_infectious_diseases():
    """API endpoint to get infectious disease data"""
    disease = request.args.get('disease', None)
    days = int(request.args.get('days', 7))
    
    data = generate_disease_data(disease=disease, days=days)
    
    # Calculate statistics
    cases = [d['cases'] for d in data]
    stats = {
        'total_cases': sum(cases),
        'avg_daily_cases': sum(cases) / len(cases) if cases else 0,
        'peak_cases': max(cases) if cases else 0,
        'trend': data[0]['trend'] if data else 'stable'
    }
    
    return jsonify({
        'success': True,
        'data': data,
        'statistics': stats,
        'count': len(data)
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'mode': 'demo'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 80)
    print("🌍 Community Health & Wellness Platform - DEMO MODE")
    print("=" * 80)
    print(f"\n✨ Starting server at http://localhost:{port}")
    print("\n📝 Features:")
    print("   • Air Quality Monitoring")
    print("   • Infectious Disease Tracking")
    print("   • AI Health Advisor")
    print("   • Interactive Visualizations (D3.js, Three.js, Anime.js)")
    print("\n💡 Note: Running in demo mode with sample data")
    print("   To use real data, configure Google Cloud credentials")
    print("\n🚀 Open your browser and visit: http://localhost:8080")
    print("=" * 80)
    app.run(host='0.0.0.0', port=port, debug=True)
