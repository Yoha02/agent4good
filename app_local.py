from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import json
import random
from epa_service import EPAAirQualityService
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
    location_service = ComprehensiveLocationService()
    weather_service = GoogleWeatherService()
    pollen_service = GooglePollenService()
    EPA_AVAILABLE = True
    print("[OK] EPA API service initialized successfully")
    print("[OK] Google Weather & Pollen services initialized")
except Exception as e:
    print(f"[WARNING] Service initialization: {e}")
    EPA_AVAILABLE = False
    epa_service = None
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
        
        # Get EPA data based on time period
        epa_data = []
        if time_period == 'live':
            current_data = epa_service.get_current_aqi(zipcode=zipcode)
            if current_data:
                epa_data = [current_data]
        
        elif time_period in ['1day', '7day', '14day', '30day', '1year']:
            days_map = {'1day': 1, '7day': 7, '14day': 14, '30day': 30, '1year': 365}
            days = days_map.get(time_period, 7)
            
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            historical_data = epa_service.get_historical_data(
                zipcode=zipcode, start_date=start_date, end_date=end_date
            )
            epa_data = historical_data
        
        else:  # hourly or other
            # For hourly, get current + forecast
            current_data = epa_service.get_current_aqi(zipcode=zipcode)
            forecast_data = epa_service.get_forecast(zipcode=zipcode)
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
            if zipcode:
                current_data = epa_service.get_current_aqi(zipcode=zipcode)
            elif state_code and city:
                location_info = location_service.get_location_info(state_code=state_code, city_name=city)
                if location_info and location_info.get('zipcodes'):
                    current_data = epa_service.get_current_aqi(zipcode=location_info['zipcodes'][0])
                else:
                    current_data = None
            else:
                # Default location
                current_data = epa_service.get_current_aqi(zipcode="90210")
            
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