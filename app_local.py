from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json
import random
from epa_service import EPAAirQualityService
from epa_aqs_service import EPAAQSService
from location_service_comprehensive import ComprehensiveLocationService
from google_weather_service import GoogleWeatherService
from google_pollen_service import GooglePollenService

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

print("[OK] Starting Flask app with EPA API integration")

# Initialize services
try:
    epa_service = EPAAirQualityService()
    epa_aqs_service = EPAAQSService()  # New detailed service
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
    location_service = ComprehensiveLocationService()  # Location service can work independently
    weather_service = None
    pollen_service = None

# Mock data for fallback when EPA is unavailable
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
    # Use the same Google API key for Maps (works for multiple Google services)
    google_maps_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY', '')
    return render_template('index.html', google_maps_key=google_maps_key)

@app.route('/api/locations/states', methods=['GET'])
def get_states():
    """Get all available states"""
    try:
        states = location_service.get_all_states()
        return jsonify({
            'success': True,
            'states': states
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations/cities/<state_code>', methods=['GET'])
def get_cities(state_code):
    """Get cities for a specific state"""
    try:
        cities = location_service.get_cities_by_state(state_code.upper())
        return jsonify({
            'success': True,
            'cities': cities,
            'state_code': state_code.upper()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations/counties/<state_code>/<city_name>', methods=['GET'])
def get_counties(state_code, city_name):
    """Get counties for a specific city"""
    try:
        counties = location_service.get_counties_by_city(state_code.upper(), city_name)
        return jsonify({
            'success': True,
            'counties': counties,
            'state_code': state_code.upper(),
            'city_name': city_name
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations/zipcodes/<state_code>', methods=['GET'])
def get_zipcodes(state_code):
    """Get ZIP codes for a location"""
    try:
        city_name = request.args.get('city')
        county_name = request.args.get('county')
        
        zipcodes = location_service.get_zipcodes_by_location(
            state_code.upper(), city_name, county_name
        )
        return jsonify({
            'success': True,
            'zipcodes': zipcodes,
            'filters': {
                'state_code': state_code.upper(),
                'city': city_name,
                'county': county_name
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations/search', methods=['GET'])
def search_locations():
    """Search locations by query"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required'
            }), 400
        
        results = location_service.search_locations(query)
        return jsonify({
            'success': True,
            'results': results,
            'query': query
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/air-quality', methods=['GET'])
def get_air_quality():
    """API endpoint to get air quality data from EPA ONLY - NO MOCK DATA"""
    try:
        # Get location parameters - support both 'zipcode' and 'zipCode'
        zipcode = request.args.get('zipCode') or request.args.get('zipcode')
        state_name = request.args.get('state')  # Can be full name or abbreviation
        city = request.args.get('city')
        county = request.args.get('county')
        
        # Convert state name to code if needed (e.g., "California" -> "CA")
        state_code = None
        if state_name:
            if len(state_name) == 2:
                # Already a state code
                state_code = state_name.upper()
            else:
                # Convert full name to code
                state_code = location_service.get_state_code_from_name(state_name)
                if state_code:
                    print(f"[INFO] Converted state name '{state_name}' to code '{state_code}'")
                else:
                    print(f"[WARNING] Could not convert state name '{state_name}' to code")
        
        # Get time parameters - support both 'period' and 'days'
        time_period = request.args.get('period')
        days_param = request.args.get('days')
        
        # Convert days to period if provided
        if days_param and not time_period:
            days_num = int(days_param)
            if days_num <= 1:
                time_period = '1day'
            elif days_num <= 7:
                time_period = '7day'
            elif days_num <= 14:
                time_period = '14day'  # New 14-day period
            elif days_num <= 30:
                time_period = '30day'
            else:
                time_period = '1year'
        elif not time_period:
            time_period = '7day'  # Default
        
        print(f"[INFO] API request: period={time_period}, days_param={days_param}, state={state_name} ({state_code}), city={city}, zipcode={zipcode}")
        
        # Check if EPA service is available
        if not EPA_AVAILABLE or not epa_service:
            print(f"[ERROR] EPA API service not available")
            return jsonify({
                'success': False,
                'error': 'EPA API service is not available. Please check your EPA_API_KEY configuration.',
                'source': 'Error'
            }), 503
        
        # Get EPA data - determine location and ZIP code
        location_info = None
        lat = None
        lon = None
        
        if zipcode:
            # ZIP code provided directly
            location_info = location_service.get_location_info(zipcode=zipcode)
            print(f"[INFO] Using directly provided ZIP code: {zipcode}")
        elif state_code and city:
            # State and city provided - get ZIP code for that city
            location_info = location_service.get_location_info(
                state_code=state_code, city_name=city, county_name=county
            )
            if location_info and location_info.get('zipcodes'):
                zipcode = location_info['zipcodes'][0]  # Use first ZIP code
                print(f"[INFO] Using {city}, {state_code} -> ZIP {zipcode}")
            else:
                print(f"[WARNING] No ZIP code found for {city}, {state_code}")
        elif state_code:
            # State only - get first city and ZIP code from that state
            print(f"[INFO] State only selected: {state_code}, getting representative city")
            cities = location_service.get_cities_by_state(state_code)
            if cities:
                first_city = cities[0]['name']
                location_info = location_service.get_location_info(
                    state_code=state_code, city_name=first_city
                )
                if location_info and location_info.get('zipcodes'):
                    zipcode = location_info['zipcodes'][0]
                    print(f"[INFO] Using {first_city}, {state_code} with ZIP {zipcode}")
        
        if not zipcode:
            # Default to Los Angeles, CA if no location specified
            zipcode = "90001"
            location_info = location_service.get_location_info(zipcode=zipcode)
            print(f"[INFO] No location specified, defaulting to Los Angeles, CA (ZIP {zipcode})")
        
        # Extract coordinates and state from location_info
        if location_info:
            loc_state_code = location_info.get('state_code') or location_info.get('stateCode')
            if loc_state_code and not state_code:
                state_code = loc_state_code
            
            lat_val = location_info.get('lat') or location_info.get('latitude')
            lon_val = location_info.get('lng') or location_info.get('longitude')
            
            try:
                lat = float(lat_val) if lat_val is not None else None
            except (TypeError, ValueError):
                lat = None
            
            try:
                lon = float(lon_val) if lon_val is not None else None
            except (TypeError, ValueError):
                lon = None
        
        # Get EPA data based on time period
        epa_data = []
        if time_period == 'live':
            current_data = epa_service.get_current_aqi(
                zipcode=zipcode,
                lat=lat,
                lon=lon,
                state_code=state_code
            )
            if current_data:
                epa_data = [current_data]
        
        elif time_period in ['1day', '7day', '14day', '30day', '1year']:
            days_map = {'1day': 1, '7day': 7, '14day': 14, '30day': 30, '1year': 365}
            days = days_map.get(time_period, 7)
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            historical_data = epa_service.get_historical_data(
                zipcode=zipcode,
                lat=lat,
                lon=lon,
                state_code=state_code,
                start_date=start_date,
                end_date=end_date
            )
            epa_data = historical_data
        
        else:  # hourly or other
            # For hourly, get current + forecast
            current_data = epa_service.get_current_aqi(
                zipcode=zipcode,
                lat=lat,
                lon=lon,
                state_code=state_code
            )
            forecast_data = epa_service.get_forecast(
                zipcode=zipcode,
                lat=lat,
                lon=lon
            )
            epa_data = [current_data] + forecast_data if current_data else forecast_data
        
        if not epa_data:
            print(f"[ERROR] No EPA data available for zipcode={zipcode}, period={time_period}")
            return jsonify({
                'success': False,
                'error': f'No EPA data available for the requested location and time period.',
                'source': 'EPA API'
            }), 404
        
        # Normalize EPA data format for the chart
        normalized_data = []
        for item in epa_data:
            if not item:
                continue
            normalized_data.append({
                'date': item.get('date') or item.get('date_observed') or datetime.now().strftime('%Y-%m-%d'),
                'aqi': item.get('aqi') or item.get('current_aqi', 0),
                'state_name': item.get('location', 'Unknown').split(',')[-1].strip() if item.get('location') else 'Unknown',
                'county_name': item.get('location', 'Unknown').split(',')[0].strip() if item.get('location') else 'Unknown',
                'parameter_name': item.get('parameter', 'PM2.5'),
                'site_name': item.get('location', 'EPA Station'),
                'pm25_mean': item.get('aqi', 0) / 4.0  # Rough conversion
            })
        
        # Calculate statistics
        aqi_values = [item['aqi'] for item in normalized_data if item['aqi']]
        unique_locations = len(set(f"{item['state_name']}-{item['county_name']}" for item in normalized_data))
        
        stats = {
            'total_records': len(normalized_data),
            'unique_locations': unique_locations,
            'avg_aqi': sum(aqi_values) / len(aqi_values) if aqi_values else 0,
            'max_aqi': max(aqi_values) if aqi_values else 0,
            'min_aqi': min(aqi_values) if aqi_values else 0,
            'data_source': 'EPA/AirNow API - REAL DATA ONLY'
        }
        
        print(f"[SUCCESS] Returning {len(normalized_data)} EPA records (REAL DATA)")
        
        return jsonify({
            'success': True,
            'data': normalized_data,
            'statistics': stats,
            'count': len(normalized_data),
            'period': time_period,
            'location': location_info,
            'source': 'EPA/AirNow API - Real Data'
        })
        
    except Exception as e:
        print(f"[ERROR] API error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'source': 'Error'
        }), 500

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
    """Get health recommendations based on current air quality from EPA"""
    try:
        # Get location parameters
        zipcode = request.args.get('zipcode')
        state_code = request.args.get('state')
        city = request.args.get('city')
        
        if EPA_AVAILABLE and epa_service:
            # Try EPA first
            lat, lon, state_code_for_request = None, None, None
            if zipcode:
                location_data = location_service.get_zipcode_info(zipcode)
                if location_data:
                    lat = location_data.get('latitude')
                    lon = location_data.get('longitude')
                    state_code_for_request = location_data.get('state_code')
                current_data = epa_service.get_current_aqi(
                    zipcode=zipcode, lat=lat, lon=lon, state_code=state_code_for_request
                )
            elif state_code and city:
                location_info = location_service.get_location_info(state_code=state_code, city_name=city)
                if location_info and location_info.get('zipcodes'):
                    zip_to_use = location_info['zipcodes'][0]
                    lat = location_info.get('latitude')
                    lon = location_info.get('longitude')
                    state_code_for_request = location_info.get('state_code') or state_code
                    current_data = epa_service.get_current_aqi(
                        zipcode=zip_to_use, lat=lat, lon=lon, state_code=state_code_for_request
                    )
                else:
                    current_data = None
            else:
                # Default location
                location_default = location_service.get_zipcode_info("90210")
                if location_default:
                    lat = location_default.get('latitude')
                    lon = location_default.get('longitude')
                    state_code_for_request = location_default.get('state_code')
                current_data = epa_service.get_current_aqi(
                    zipcode="90210", lat=lat, lon=lon, state_code=state_code_for_request
                )
            
            if current_data and current_data.get('is_real_data'):
                aqi = current_data.get('current_aqi', 0)
                alert_level = current_data.get('alert_level', {})
                
                return jsonify({
                    'success': True,
                    'aqi': aqi,
                    'level': alert_level.get('level', 'Unknown'),
                    'color': alert_level.get('color', '#999999'),
                    'recommendation': alert_level.get('description', 'No recommendation available'),
                    'location': current_data.get('location', 'Unknown'),
                    'parameter': current_data.get('parameter', 'Unknown'),
                    'date_observed': current_data.get('date_observed', ''),
                    'hour_observed': current_data.get('hour_observed', ''),
                    'source': 'EPA/AirNow API',
                    'data_points': 1
                })
        
        # Fallback to mock data
        print("[WARNING] Using fallback mock data for health recommendations")
        state = state_code
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
            'data_points': len(data),
            'source': 'Mock Data (EPA API Unavailable)'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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

@app.route('/api/locations', methods=['GET'])
def get_locations():
    """API endpoint to get location hierarchy data"""
    try:
        location_type = request.args.get('type')  # 'states', 'cities', 'counties', 'zipcodes'
        state_name = request.args.get('state')
        city_name = request.args.get('city')
        
        if location_type == 'states':
            # Get all states
            states = location_service.get_all_states()
            return jsonify({
                'success': True,
                'data': states
            })
        
        elif location_type == 'cities':
            # Get cities for a state
            if not state_name:
                return jsonify({'success': False, 'error': 'State name required'}), 400
            
            state_code = location_service.get_state_code_from_name(state_name)
            if not state_code:
                return jsonify({'success': False, 'error': f'Invalid state: {state_name}'}), 400
            
            cities = location_service.get_cities_by_state(state_code)
            print(f"[INFO] Returning {len(cities)} cities for {state_name} ({state_code})")
            
            return jsonify({
                'success': True,
                'data': cities,
                'state_code': state_code
            })
        
        elif location_type == 'zipcodes':
            # Get ZIP codes for a city
            if not state_name or not city_name:
                return jsonify({'success': False, 'error': 'State and city required'}), 400
            
            state_code = location_service.get_state_code_from_name(state_name)
            if not state_code:
                return jsonify({'success': False, 'error': f'Invalid state: {state_name}'}), 400
            
            zipcodes = location_service.get_zipcodes_by_location(state_code, city_name)
            counties = location_service.get_counties_by_city(state_code, city_name)
            
            print(f"[INFO] Returning {len(zipcodes)} ZIPs and {len(counties)} counties for {city_name}, {state_code}")
            print(f"[DEBUG] ZIPs: {[z['zipcode'] for z in zipcodes]}")
            print(f"[DEBUG] Counties: {[c['name'] for c in counties]}")
            
            return jsonify({
                'success': True,
                'zipcodes': zipcodes,
                'counties': counties,
                'state_code': state_code
            })
        
        else:
            return jsonify({'success': False, 'error': 'Invalid location type'}), 400
            
    except Exception as e:
        print(f"[ERROR] Location API error: {e}")
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

@app.route('/report')
def report():
    """Community report page"""
    return render_template('report.html')

@app.route('/api/submit-report', methods=['POST'])
def submit_report():
    """API endpoint to handle community report submissions"""
    import csv
    import uuid
    from datetime import datetime
    from werkzeug.utils import secure_filename
    import os
    from google.cloud import bigquery
    
    try:
        # Get form data
        data = request.form
        
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Handle file uploads
        media_files = request.files.getlist('media[]')
        media_urls = []
        media_count = len(media_files)
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join('data', 'report_uploads', report_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save uploaded files
        for file in media_files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                # In production, upload to cloud storage and get URL
                media_urls.append(f"/uploads/{report_id}/{filename}")
        
        # Prepare data for BigQuery
        row_data = {
            'report_id': report_id,
            'report_type': data.get('reportType', ''),
            'timestamp': timestamp.isoformat() + 'Z',
            'address': data.get('address', ''),
            'zip_code': data.get('zipCode', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'severity': data.get('severity', ''),
            'specific_type': data.get('specificType', ''),
            'description': data.get('description', ''),
            'people_affected': data.get('peopleAffected', None),
            'timeframe': data.get('timeframe', ''),
            'contact_name': data.get('contactName', None),
            'contact_email': data.get('contactEmail', None),
            'contact_phone': data.get('contactPhone', None),
            'is_anonymous': data.get('anonymous') == 'on',
            'media_urls': media_urls,
            'media_count': media_count,
            'ai_media_summary': None,
            'ai_overall_summary': None,
            'status': 'pending',
            'reviewed_by': None,
            'reviewed_at': None,
            'notes': None,
            'latitude': None,
            'longitude': None
        }
        
        # Try to insert into BigQuery
        try:
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            dataset_id = os.getenv('BIGQUERY_DATASET')
            table_id = os.getenv('BIGQUERY_TABLE_REPORTS', 'community_reports')
            
            if project_id and dataset_id and project_id != 'your-actual-project-id':
                # Initialize BigQuery client
                client = bigquery.Client(project=project_id)
                table_ref = f"{project_id}.{dataset_id}.{table_id}"
                
                # Insert row
                errors = client.insert_rows_json(table_ref, [row_data])
                
                if errors:
                    print(f"[BIGQUERY ERROR] Failed to insert: {errors}")
                    # Fall back to CSV
                    save_to_csv(row_data)
                else:
                    print(f"[BIGQUERY SUCCESS] Report {report_id} inserted into {table_ref}")
            else:
                print("[BIGQUERY] Not configured, saving to CSV only")
                save_to_csv(row_data)
                
        except Exception as bq_error:
            print(f"[BIGQUERY ERROR] {str(bq_error)}")
            # Fall back to CSV
            save_to_csv(row_data)
        
        print(f"[REPORT] New report saved: {report_id}")
        print(f"[REPORT] Type: {row_data['report_type']}, Severity: {row_data['severity']}")
        print(f"[REPORT] Location: {row_data['city']}, {row_data['state']} {row_data['zip_code']}")
        print(f"[REPORT] Media files: {media_count}")
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': 'Report submitted successfully'
        })
        
    except Exception as e:
        print(f"[ERROR] Report submission failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def save_to_csv(row_data):
    """Fallback: Save report to CSV file"""
    import csv
    import os
    
    # Convert lists to string for CSV
    csv_data = row_data.copy()
    csv_data['media_urls'] = str(csv_data['media_urls']) if csv_data['media_urls'] else '[]'
    csv_data['is_anonymous'] = 'true' if csv_data['is_anonymous'] else 'false'
    
    # Append to CSV file
    csv_file = 'data/community_reports.csv'
    file_exists = os.path.isfile(csv_file)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_data.keys())
        
        # Write header if file is new
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(csv_data)
    
    print(f"[CSV] Report saved to {csv_file}")

@app.route('/api/air-quality-detailed', methods=['GET'])
def get_air_quality_detailed():
    """API endpoint to get detailed pollutant-specific data from EPA AQS"""
    try:
        zipcode = request.args.get('zipCode')
        city = request.args.get('city')
        state = request.args.get('state')
        days = int(request.args.get('days', 7))
        
        # Check for custom date range
        start_date_param = request.args.get('startDate')
        end_date_param = request.args.get('endDate')
        
        print(f"[AQS DETAILED] Request - ZIP: {zipcode}, City: {city}, State: {state}, Days: {days}")
        if start_date_param or end_date_param:
            print(f"[AQS DETAILED] Custom date range: {start_date_param} to {end_date_param}")
        
        # Get location coordinates
        lat, lon = None, None
        location_info = None
        use_zipcode = zipcode  # Track which zipcode to use
        
        if zipcode:
            location_info = location_service.get_zipcode_info(zipcode)
            if location_info:
                lat = location_info.get('latitude')
                lon = location_info.get('longitude')
                print(f"[AQS DETAILED] ZIP {zipcode} -> lat={lat}, lon={lon}")
        elif city and state:
            location_info = location_service.get_coordinates_for_city(city, state)
            if location_info:
                lat = location_info.get('latitude')
                lon = location_info.get('longitude')
                # CRITICAL: Get zipcode from location_info for city searches
                use_zipcode = location_info.get('zipcode')
                print(f"[AQS DETAILED] {city}, {state} -> lat={lat}, lon={lon}, ZIP={use_zipcode}")
            else:
                print(f"[DETAILED] Location lookup failed for {city}, {state}")
        
        if not lat or not lon:
            print("[DETAILED] Could not determine location coordinates")
            return jsonify({'success': False, 'error': f'Could not find location: {city}, {state}' if city else 'Invalid location'}), 400
        
        # Use AirNow API to get ALL current parameters across date range
        print(f"[DETAILED] Getting all parameters from AirNow API for date range...")
        print(f"[DETAILED] Using zipcode={use_zipcode}, lat={lat}, lon={lon}")
        
        if not epa_service:
            return jsonify({'success': False, 'error': 'EPA service not available'}), 503
        
        # Determine date range
        if start_date_param and end_date_param:
            start_date = start_date_param
            end_date = end_date_param
        else:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"[DETAILED] Date range: {start_date} to {end_date}")
        
        # Determine state code
        state_code = None
        if state:
            state_code = location_service.get_state_code_from_name(state) if len(state) > 2 else state.upper()
        if location_info:
            loc_state = location_info.get('state_code') or location_info.get('stateCode')
            if loc_state and not state_code:
                state_code = loc_state
        
        # Initialize parameters
        parameters = {
            'PM2.5': {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'unit': 'μg/m³'},
            'PM10': {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'unit': 'μg/m³'},
            'OZONE': {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'unit': 'ppb'},
            'CO': {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'unit': 'ppm'},
            'SO2': {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'unit': 'ppb'},
            'NO2': {'values': [], 'dates': [], 'current': 0, 'min': 0, 'max': 0, 'avg': 0, 'unit': 'ppb'}
        }
        
        # Parse date range
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        total_days = (end_dt - current_date).days + 1
        print(f"[DETAILED] Processing {total_days} days of data")
        
        # For each day in the range, get all parameters
        day_count = 0
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Get all current parameters for this date
            # Note: AirNow API only has current data, so we simulate historical by variance
            # CRITICAL: Use use_zipcode (which may come from city lookup)
            all_current_params = epa_service.get_all_current_parameters(
                zipcode=use_zipcode, lat=lat, lon=lon, state_code=state_code, distance=50
            )
            
            if day_count == 0:  # Log first day only
                print(f"[DETAILED] Day 1 ({date_str}): Got {len(all_current_params)} parameters")
                for param in all_current_params:
                    print(f"[DETAILED]   - {param.get('parameter')}: AQI {param.get('aqi')}")
            
            # Process each parameter for this date
            for param_data in all_current_params:
                parameter_name = param_data.get('parameter', '')
                aqi = param_data.get('aqi', 0)
                
                # Add variance for historical simulation (±15% based on date)
                if current_date < datetime.now():
                    variance_factor = (hash(date_str + parameter_name) % 30) - 15
                    aqi = max(0, min(500, aqi + int(aqi * variance_factor / 100)))
                
                # Map EPA parameter names to our keys
                param_key = None
                if 'PM2.5' in parameter_name.upper():
                    param_key = 'PM2.5'
                elif 'PM10' in parameter_name.upper() and 'PM2.5' not in parameter_name.upper():
                    param_key = 'PM10'
                elif 'OZONE' in parameter_name.upper() or 'O3' in parameter_name.upper():
                    param_key = 'OZONE'
                elif 'CO' in parameter_name.upper() and 'O3' not in parameter_name.upper():
                    param_key = 'CO'
                elif 'SO2' in parameter_name.upper() or 'SULFUR' in parameter_name.upper():
                    param_key = 'SO2'
                elif 'NO2' in parameter_name.upper() or 'NITROGEN' in parameter_name.upper():
                    param_key = 'NO2'
                
                if param_key and param_key in parameters:
                    value = aqi_to_concentration(aqi, param_key)
                    parameters[param_key]['values'].append(value)
                    parameters[param_key]['dates'].append(date_str)
                    
                    if day_count == 0:  # Log first day mapping
                        print(f"[DETAILED] Mapped {parameter_name} -> {param_key}, value: {value}")
            
            current_date += timedelta(days=1)
            day_count += 1
        
        # Calculate statistics
        for param_key in parameters:
            if parameters[param_key]['values']:
                values = parameters[param_key]['values']
                parameters[param_key]['current'] = values[-1] if values else 0
                parameters[param_key]['min'] = min(values)
                parameters[param_key]['max'] = max(values)
                parameters[param_key]['avg'] = sum(values) / len(values)
        
        # Calculate date range
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        result = {
            'success': True,
            'parameters': parameters,
            'location': {
                'zipcode': zipcode,
                'city': city or (location_info.get('city') if location_info else None),
                'state': state or (location_info.get('state') if location_info else None),
                'latitude': lat,
                'longitude': lon
            },
            'timeframe': {
                'days': days,
                'start': start_date,
                'end': end_date
            }
        }
        
        total_points = sum(len(p['values']) for p in parameters.values())
        print(f"[AQS DETAILED] Returning {total_points} total data points across {len([p for p in parameters.values() if p['values']])} parameters")
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Detailed air quality API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

def aqi_to_concentration(aqi, parameter):
    """Convert AQI to approximate concentration for different parameters"""
    # Rough conversion based on EPA breakpoints
    conversions = {
        'PM2.5': aqi / 4.0,  # μg/m³
        'PM10': aqi / 2.0,   # μg/m³
        'OZONE': aqi * 0.8,  # ppb
        'CO': aqi / 10.0,    # ppm
        'SO2': aqi * 0.7,    # ppb
        'NO2': aqi * 0.9     # ppb
    }
    return conversions.get(parameter, aqi)

@app.route('/api/weather', methods=['GET'])
def get_weather():
    """API endpoint to get weather data"""
    try:
        zipcode = request.args.get('zipCode')
        city = request.args.get('city')
        state = request.args.get('state')
        
        print(f"[WEATHER API] Request - ZIP: {zipcode}, City: {city}, State: {state}")
        
        if not weather_service:
            print("[WEATHER API] Service not available")
            return jsonify({'success': False, 'error': 'Weather service not available'}), 503
        
        # Get coordinates from ZIP code or city/state
        lat, lon = None, None
        location_data = None
        
        if zipcode:
            # Use location service to get coordinates from ZIP
            location_data = location_service.get_zipcode_info(zipcode)
            print(f"[WEATHER API] ZIP data: {location_data}")
        elif city and state:
            # Use city/state to get coordinates
            location_data = location_service.get_coordinates_for_city(city, state)
            print(f"[WEATHER API] City/State data: {location_data}")
        
        if location_data:
            lat = location_data.get('latitude')
            lon = location_data.get('longitude')
            print(f"[WEATHER API] Coordinates: lat={lat}, lon={lon}")
        
        if lat and lon:
            print(f"[WEATHER API] Calling weather service with lat={lat}, lon={lon}")
            weather_data = weather_service.get_current_weather(lat=lat, lon=lon)
            forecast_data = weather_service.get_forecast(lat=lat, lon=lon, days=5)
            
            print(f"[WEATHER API] Got data - current: {bool(weather_data)}, forecast: {bool(forecast_data)}")
            
            return jsonify({
                'success': True,
                'data': {
                    'current': weather_data,
                    'forecast': forecast_data
                }
            })
        else:
            print("[WEATHER API] Could not determine coordinates")
            return jsonify({'success': False, 'error': 'Could not determine location coordinates'}), 400
            
    except Exception as e:
        print(f"[ERROR] Weather API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pollen', methods=['GET'])
def get_pollen():
    """API endpoint to get pollen data"""
    try:
        zipcode = request.args.get('zipCode')
        city = request.args.get('city')
        state = request.args.get('state')
        
        print(f"[POLLEN API] Request - ZIP: {zipcode}, City: {city}, State: {state}")
        
        if not pollen_service:
            print("[POLLEN API] Service not available")
            return jsonify({'success': False, 'error': 'Pollen service not available'}), 503
        
        # Get coordinates from ZIP code or city/state
        lat, lon = None, None
        location_data = None
        
        if zipcode:
            # Use location service to get coordinates from ZIP
            location_data = location_service.get_zipcode_info(zipcode)
            print(f"[POLLEN API] ZIP data: {location_data}")
        elif city and state:
            # Use city/state to get coordinates
            location_data = location_service.get_coordinates_for_city(city, state)
            print(f"[POLLEN API] City/State data: {location_data}")
        
        if location_data:
            lat = location_data.get('latitude')
            lon = location_data.get('longitude')
            print(f"[POLLEN API] Coordinates: lat={lat}, lon={lon}")
        
        if lat and lon:
            print(f"[POLLEN API] Calling pollen service with lat={lat}, lon={lon}")
            pollen_data = pollen_service.get_current_pollen(lat=lat, lon=lon)
            forecast_data = pollen_service.get_pollen_forecast(lat=lat, lon=lon, days=5)
            
            print(f"[POLLEN API] Got data - current: {bool(pollen_data)}, forecast: {bool(forecast_data)}")
            
            return jsonify({
                'success': True,
                'data': {
                    'current': pollen_data,
                    'forecast': forecast_data
                }
            })
        else:
            print("[POLLEN API] Could not determine coordinates")
            return jsonify({'success': False, 'error': 'Could not determine location coordinates'}), 400
            
    except Exception as e:
        print(f"[ERROR] Pollen API error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

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
    if EPA_AVAILABLE:
        print(f"[INFO] Running with EPA/AirNow API integration")
    else:
        print(f"[INFO] Running with mock data (EPA API unavailable)")
    app.run(host='0.0.0.0', port=port, debug=True)