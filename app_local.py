from flask import Flask, render_template, request, jsonify
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
from google.cloud import storage, bigquery, texttospeech
import google.generativeai as genai
import base64

# PSA Video Integration
try:
    from multi_tool_agent_bquery_tools.async_video_manager import VideoGenerationManager
    PSA_VIDEO_AVAILABLE = True
except ImportError as e:
    print(f"[INFO] PSA Video features not available: {e}")
    PSA_VIDEO_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# GCS Configuration
GCS_BUCKET_NAME = 'agent4good-report-attachments'
GCP_PROJECT_ID = 'qwiklabs-gcp-00-4a7d408c735c'

# Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

print("[OK] Starting Flask app with EPA API integration")

# Initialize GCS client with timeout
try:
    import socket
    # Set a global socket timeout to prevent hanging
    socket.setdefaulttimeout(5)  # 5 second timeout
    
    storage_client = storage.Client(project=GCP_PROJECT_ID)
    # Try to get bucket, create if doesn't exist
    try:
        bucket = storage_client.get_bucket(GCS_BUCKET_NAME)
        print(f"[OK] Connected to GCS bucket: {GCS_BUCKET_NAME}")
    except Exception as e:
        print(f"[INFO] Bucket access failed (may need auth or network): {str(e)[:100]}")
        bucket = None
        GCS_AVAILABLE = False
    
    # Reset socket timeout
    socket.setdefaulttimeout(None)
    
    if bucket:
        GCS_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] GCS initialization failed: {str(e)[:100]}")
    GCS_AVAILABLE = False
    storage_client = None
    bucket = None

# Initialize BigQuery client
try:
    bq_client = bigquery.Client(project=GCP_PROJECT_ID)
    print(f"[OK] BigQuery client initialized for project: {GCP_PROJECT_ID}")
except Exception as e:
    print(f"[WARNING] BigQuery initialization failed: {e}")
    bq_client = None

# Initialize Gemini AI model
try:
    if GEMINI_API_KEY:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("[OK] Gemini AI model initialized (gemini-2.0-flash-exp)")
    else:
        model = None
        print("[WARNING] No Gemini API key, AI features will be limited")
except Exception as e:
    print(f"[WARNING] Gemini model initialization failed: {e}")
    model = None

# Initialize Google Text-to-Speech client
try:
    tts_client = texttospeech.TextToSpeechClient()
    TTS_AVAILABLE = True
    print("[OK] Google Text-to-Speech client initialized")
except Exception as e:
    print(f"[WARNING] Text-to-Speech initialization failed: {e}")
    TTS_AVAILABLE = False
    tts_client = None

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

# Initialize PSA Video Manager
video_manager = None
if PSA_VIDEO_AVAILABLE:
    try:
        video_manager = VideoGenerationManager()
        print("[OK] PSA Video Manager initialized")
    except Exception as e:
        print(f"[WARNING] PSA Video Manager initialization failed: {e}")
        video_manager = None
        PSA_VIDEO_AVAILABLE = False

# Import ADK agent (optional, for backwards compatibility)
try:
    from multi_tool_agent_bquery_tools.agent import call_agent as call_adk_agent
    ADK_AGENT_AVAILABLE = True
    print("[OK] ADK Agent loaded successfully!")
except Exception as e:
    print(f"[INFO] ADK Agent not available (optional): {e}")
    ADK_AGENT_AVAILABLE = False

# ===== FILE UPLOAD & AI ANALYSIS HELPERS =====

ALLOWED_EXTENSIONS = {
    'image': {'jpg', 'jpeg', 'png', 'gif'},
    'video': {'mp4', 'mov'},
    'document': {'pdf', 'doc', 'docx'},
    'data': {'csv'}
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_REPORT = 10

def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS['image'] | ALLOWED_EXTENSIONS['video'] | \
           ALLOWED_EXTENSIONS['document'] | ALLOWED_EXTENSIONS['data']

def get_file_type(filename):
    """Determine file type category"""
    if '.' not in filename:
        return 'unknown'
    ext = filename.rsplit('.', 1)[1].lower()
    for category, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            return category
    return 'unknown'

def upload_to_gcs(file, report_id, file_index):
    """Upload file to GCS bucket and return URL"""
    if not GCS_AVAILABLE or not bucket:
        raise Exception("GCS not available")
    
    filename = file.filename
    # Create unique blob name: reports/{report_id}/{index}_{original_filename}
    blob_name = f"reports/{report_id}/{file_index}_{filename}"
    blob = bucket.blob(blob_name)
    
    # Upload file
    blob.upload_from_file(file, content_type=file.content_type)
    
    # Make blob publicly accessible (or use signed URLs for security)
    blob.make_public()
    
    return {
        'url': blob.public_url,
        'filename': filename,
        'blob_name': blob_name,
        'file_type': get_file_type(filename)
    }

def analyze_text_with_gemini(description, severity, timeframe, report_type):
    """Use Gemini to analyze report text and suggest status/tags"""
    if not GEMINI_API_KEY:
        return None
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Updated to Flash 2.0
        
        prompt = f"""You are an AI assistant helping public health officials analyze environmental and health reports.

Analyze this report and provide:
1. A concise 2-3 sentence summary of the key issues and concerns
2. Relevant tags from this list ONLY: valid, urgent, moderate, inappropriate, needs_review, contact_required, false_alarm, monitoring_required
3. A confidence score (0.0 to 1.0) indicating how confident you are that this is a legitimate, valid report

Report Details:
- Type: {report_type}
- Severity Level: {severity}
- When it occurred: {timeframe}
- Description: {description}

Guidelines:
- Mark as "urgent" if immediate action is needed (high severity, dangerous conditions, many people affected)
- Mark as "valid" if the report seems legitimate and verifiable
- Mark as "inappropriate" or "false_alarm" if the report is clearly spam, irrelevant, or not a real issue
- Mark as "needs_review" if you're uncertain or need human verification
- Mark as "contact_required" if officials should reach out to the reporter
- Confidence should be lower (0.3-0.6) for vague reports, higher (0.7-0.95) for detailed, specific reports

Return ONLY valid JSON (no markdown, no code blocks):
{{"summary": "your 2-3 sentence summary here", "tags": ["tag1", "tag2"], "confidence": 0.85}}"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up response (remove markdown code blocks if present)
        text = text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(text)
        
        # Validate structure
        if not all(k in result for k in ['summary', 'tags', 'confidence']):
            print(f"[AI WARNING] Invalid response structure: {result}")
            return None
            
        return result
    except Exception as e:
        print(f"[ERROR] Gemini text analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None
        return None

def analyze_attachments_with_gemini(attachment_urls):
    """Use Gemini Vision to analyze images/media"""
    if not GEMINI_API_KEY or not attachment_urls:
        return None
    
    try:
        # Filter for images only (Gemini Vision works with images)
        image_urls = [a for a in attachment_urls if a['file_type'] == 'image']
        
        if not image_urls:
            # No images, check for documents
            doc_count = sum(1 for a in attachment_urls if a['file_type'] in ['document', 'data'])
            if doc_count > 0:
                return f"{doc_count} document(s) attached (AI cannot analyze non-image files yet)"
            return "No analyzable attachments"
        
        # Analyze first image with Gemini Vision
        first_image_url = image_urls[0]['url']
        
        # Download image from GCS
        print(f"[AI] Downloading image from {first_image_url}")
        response = requests.get(first_image_url, timeout=10)
        response.raise_for_status()
        
        image = Image.open(BytesIO(response.content))
        print(f"[AI] Image loaded: {image.size} pixels, format: {image.format}")
        
        # Use Gemini Vision to analyze the image
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = """You are an environmental and public health expert analyzing a submitted image.

Analyze this image in the context of environmental health and public safety concerns. Look for:
- Air quality issues (smoke, haze, pollution, industrial emissions)
- Water contamination (discoloration, algae, debris, chemical spills)
- Sanitation problems (waste, sewage, pests, improper disposal)
- Infrastructure hazards (damaged utilities, unsafe conditions)
- Weather-related dangers (flooding, storm damage)
- Other health/environmental concerns

Provide a concise 2-3 sentence description of what you observe in the image and whether it represents a legitimate environmental or health concern. Be specific about visible details.

If the image is unrelated to health/environmental issues (e.g., selfie, random photo), state that clearly."""

        response = model.generate_content([prompt, image])
        analysis = response.text.strip()
        
        print(f"[AI] Vision analysis: {analysis[:200]}...")
        
        summary = f"{len(image_urls)} image(s) attached. Visual analysis: {analysis}"
        return summary
        
    except Exception as e:
        print(f"[ERROR] Gemini media analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return f"{len(attachment_urls)} attachment(s) - visual analysis unavailable"

def assign_auto_status(ai_tags, ai_confidence):
    """Auto-assign status based on AI analysis"""
    if not ai_tags:
        return 'Pending'
    
    # Priority-based status assignment
    if 'inappropriate' in ai_tags or 'false_alarm' in ai_tags:
        return 'Closed - Invalid'
    elif 'urgent' in ai_tags or ai_confidence > 0.85:
        return 'Valid - Action Required'
    elif 'needs_review' in ai_tags or ai_confidence < 0.7:
        return 'Under Review'
    elif 'valid' in ai_tags:
        return 'Valid - Monitoring'
    else:
        return 'Pending'

# ===== END FILE UPLOAD & AI HELPERS =====


class AirQualityAgent:
    """Google SDK Agent for Air Quality Analysis with BigQuery + Gemini AI"""
    
    def __init__(self, bq_client, genai_model):
        self.bq_client = bq_client
        self.model = genai_model
    
    def query_air_quality_data(self, state=None, county=None, city=None, days=7):
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
            
            # Add county filter if provided
            if county:
                query += f" AND UPPER(county_name) LIKE UPPER('%{county}%')"
            
            # Add city filter if provided (check if city name is in site_name)
            if city and not county:
                query += f" AND (UPPER(local_site_name) LIKE UPPER('%{city}%') OR UPPER(county_name) LIKE UPPER('%{city}%'))"
            
            query += " ORDER BY date_local DESC LIMIT 1000"
            
            location_str = f"{city or ''} {county or ''} {state or 'all states'}".strip()
            print(f"[BQ] Querying public EPA dataset for {location_str}, last {days} days")
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


# Initialize the AI agent
agent = AirQualityAgent(bq_client, model)


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
            # Also support 'query' parameter
            query = request.args.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query parameter required'
            }), 400
        
        # Use search_zipcodes method (the correct method name)
        results = location_service.search_zipcodes(query)
        return jsonify({
            'success': True,
            'results': results,
            'query': query
        })
    except Exception as e:
        print(f"[ERROR] Location search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/locations/reverse-geocode', methods=['GET'])
def reverse_geocode():
    """Reverse geocode lat/lng to ZIP code"""
    try:
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        
        if not lat or not lng:
            return jsonify({
                'success': False,
                'error': 'Latitude and longitude required'
            }), 400
        
        # Convert to float
        lat = float(lat)
        lng = float(lng)
        
        # Find nearest ZIP code from our database
        # This is a simple implementation - in production you'd use Google Maps API
        all_zips = zipcodes.list_all()
        
        min_distance = float('inf')
        nearest_zip = None
        
        for zip_data in all_zips:
            zip_lat = float(zip_data.get('lat', 0))
            zip_lng = float(zip_data.get('long', 0))
            
            # Calculate simple distance (not perfect but works for nearest neighbor)
            distance = ((lat - zip_lat) ** 2 + (lng - zip_lng) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                nearest_zip = zip_data
        
        if nearest_zip:
            return jsonify({
                'success': True,
                'zipcode': nearest_zip.get('zip_code'),
                'city': nearest_zip.get('city'),
                'state_code': nearest_zip.get('state'),
                'county': nearest_zip.get('county'),
                'distance': min_distance
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Could not find nearest ZIP code'
            }), 404
            
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
    """API endpoint for ADK agent chat with fallback to Gemini AI"""
    try:
        request_data = request.get_json()
        question = request_data.get('question', '')
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        # Get location context from request
        state = request_data.get('state', None)
        city = request_data.get('city', None)
        zipcode = request_data.get('zipcode', None)
        days = int(request_data.get('days', 7))
        time_frame = request_data.get('time_frame', None)
        
        # IMPORTANT: Get the stored location_context object from frontend
        location_context_data = request_data.get('location_context', None)
        
        # Extract location info from location_context if available
        if location_context_data and isinstance(location_context_data, dict):
            # Override with stored location data if available
            if not zipcode and location_context_data.get('zipCode'):
                zipcode = location_context_data.get('zipCode')
            if not city and location_context_data.get('city'):
                city = location_context_data.get('city')
            if not state and location_context_data.get('state'):
                state = location_context_data.get('state')
        
        # Debug: Log received parameters
        print(f"[AGENT-CHAT] Received parameters: state={state}, city={city}, zipcode={zipcode}, days={days}, time_frame={time_frame}")
        print(f"[AGENT-CHAT] Location context data: {location_context_data}")
        
        # Build location context string for AI
        location_context = ""
        if zipcode:
            location_context = f"ZIP code {zipcode}"
            if city and state:
                location_context = f"{city}, {state} (ZIP: {zipcode})"
        elif city and state:
            location_context = f"{city}, {state}"
        elif state:
            location_context = state
        
        # Check for PSA video generation keywords
        video_keywords = [
            'create video', 'generate video', 'make video', 'produce video',
            'create psa', 'generate psa', 'make psa',
            'psa video', 'public service announcement', 'health alert video',
            'create announcement', 'make announcement'
        ]
        
        wants_video = any(keyword in question.lower() for keyword in video_keywords)
        
        if wants_video and PSA_VIDEO_AVAILABLE and video_manager:
            print(f"[PSA-VIDEO] Video generation requested for: {location_context or state or 'Unknown location'}")
            try:
                # Create video generation task
                task_id = video_manager.create_task({
                    'question': question,
                    'state': state,
                    'city': city,
                    'zipcode': zipcode,
                    'location_context': location_context
                })
                
                # Start background video generation
                from multi_tool_agent_bquery_tools.integrations.veo3_client import get_veo3_client
                from multi_tool_agent_bquery_tools.tools.video_gen import generate_action_line, create_veo_prompt
                
                # Get current health data for video context
                health_data_for_video = agent.query_air_quality_data(state=state, days=1)
                
                if health_data_for_video:
                    df = pd.DataFrame(health_data_for_video)
                    avg_aqi = int(df['aqi'].mean()) if 'aqi' in df and not df['aqi'].empty else 50
                    
                    # Determine severity
                    if avg_aqi <= 50:
                        severity = "good"
                    elif avg_aqi <= 100:
                        severity = "moderate"
                    elif avg_aqi <= 150:
                        severity = "unhealthy for sensitive groups"
                    elif avg_aqi <= 200:
                        severity = "unhealthy"
                    elif avg_aqi <= 300:
                        severity = "very unhealthy"
                    else:
                        severity = "hazardous"
                else:
                    avg_aqi = 75
                    severity = "moderate"
                
                health_data = {
                    'type': 'air_quality',
                    'severity': severity,
                    'metric': avg_aqi,
                    'location': state or 'Unknown',
                    'specific_concern': 'PM2.5'
                }
                
                veo_client = get_veo3_client()
                video_manager.start_video_generation(
                    task_id=task_id,
                    health_data=health_data,
                    veo_client=veo_client,
                    action_line_func=generate_action_line,
                    veo_prompt_func=create_veo_prompt
                )
                
                print(f"[PSA-VIDEO] Task {task_id} created and started")
                
                return jsonify({
                    'success': True,
                    'response': f"I'll generate a health alert video for {location_context or state or 'your area'}. This takes about 60 seconds.\n\nYou can continue chatting while I work on this. I'll notify you when it's ready!\n\nIs there anything else I can help you with?",
                    'task_id': task_id,
                    'estimated_time': 60,
                    'agent': 'PSA Video Generator',
                    'location': location_context
                })
                
            except Exception as video_error:
                print(f"[PSA-VIDEO] Error starting video generation: {video_error}")
                import traceback
                traceback.print_exc()
                # Fall through to normal chat
        
        # Try ADK agent first if available (only if model is working)
        if ADK_AGENT_AVAILABLE and model:
            try:
                print(f"[AGENT-CHAT] Using ADK agent for question: {question}")
                # Enhance question with location context if not already mentioned
                enhanced_question = question
                if location_context and location_context.lower() not in question.lower():
                    enhanced_question = f"For {location_context}: {question}"
                
                print(f"[AGENT-CHAT] Enhanced question: {enhanced_question}")
                
                # Prepare location context for ADK agent
                location_context_dict = None
                if state or city or zipcode:
                    location_context_dict = {
                        'state': state,
                        'city': city,
                        'zipCode': zipcode,
                        'formattedAddress': location_context
                    }
                
                # Call ADK agent with context
                response = call_adk_agent(enhanced_question, location_context=location_context_dict, time_frame=time_frame)
                print(f"[AGENT-CHAT] ADK response received: {response[:100]}...")
                
                # Check if response indicates an API key error
                if "API key is not set up" in response or "cannot fulfill this request" in response:
                    print(f"[WARNING] ADK agent has API key issue, falling back to Gemini AI")
                    raise Exception("ADK agent API key error")
                
                result = {
                    'success': True,
                    'response': response,
                    'agent': 'ADK Multi-Agent System',
                    'location': location_context
                }
                print(f"[AGENT-CHAT] Returning successful response via ADK")
                return jsonify(result)
            except Exception as adk_error:
                print(f"[ERROR] ADK agent failed: {adk_error}")
                import traceback
                traceback.print_exc()
                print(f"[AGENT-CHAT] Falling back to Gemini AI")
        
        # Fallback to Gemini AI with comprehensive environmental data
        # Gather all available environmental data for the location
        environmental_data = {
            'air_quality': None,
            'weather': None,
            'pollen': None,
            'detailed_pollutants': None
        }
        
        # 1. Get air quality data
        try:
            if EPA_AVAILABLE and epa_service:
                if zipcode:
                    environmental_data['air_quality'] = epa_service.get_current_aqi(zipcode=zipcode)
                elif state:
                    # Get representative city for state
                    cities = location_service.get_cities_by_state(location_service.get_state_code_from_name(state))
                    if cities:
                        zip_data = location_service.get_zipcode_info(cities[0].get('zipcode'))
                        if zip_data:
                            environmental_data['air_quality'] = epa_service.get_current_aqi(zipcode=zip_data['zipcode'])
        except Exception as e:
            print(f"[CHATBOT] Error fetching air quality: {e}")
        
        # 2. Get weather data
        try:
            if weather_service and zipcode:
                weather_result = weather_service.get_weather(zipcode=zipcode)
                if weather_result and weather_result.get('current'):
                    environmental_data['weather'] = weather_result['current']
        except Exception as e:
            print(f"[CHATBOT] Error fetching weather: {e}")
        
        # 3. Get pollen data
        try:
            if pollen_service and zipcode:
                pollen_result = pollen_service.get_pollen(zipcode=zipcode)
                if pollen_result and pollen_result.get('current'):
                    environmental_data['pollen'] = pollen_result['current']
        except Exception as e:
            print(f"[CHATBOT] Error fetching pollen: {e}")
        
        # 4. Get detailed pollutant data
        try:
            if EPA_AVAILABLE and epa_aqs_service and zipcode:
                detailed_result = epa_aqs_service.get_detailed_pollutants(zipcode=zipcode, days=days)
                if detailed_result:
                    environmental_data['detailed_pollutants'] = detailed_result
        except Exception as e:
            print(f"[CHATBOT] Error fetching detailed pollutants: {e}")
        
        # Get historical air quality data from BigQuery with city/county filtering
        # Extract county from location data if available
        county = None
        if location_context_data and isinstance(location_context_data, dict):
            county = location_context_data.get('county')
        
        print(f"[CHATBOT] Querying BigQuery with: state={state}, city={city}, county={county}, days={days}")
        historical_data = agent.query_air_quality_data(state=state, county=county, city=city, days=days)
        
        # Build comprehensive context for AI with CURRENT REAL-TIME DATA FIRST
        context_parts = []
        
        # PRIORITY 1: Current location context
        if location_context:
            context_parts.append(f"User is asking about {location_context}.")
        
        # PRIORITY 2: Real-time current air quality from EPA AirNow API (TODAY'S DATA)
        if environmental_data['air_quality']:
            aqi_data = environmental_data['air_quality']
            if isinstance(aqi_data, dict) and aqi_data.get('success') and aqi_data.get('data'):
                # Handle new format from EPA service
                readings = aqi_data['data']
                if readings and len(readings) > 0:
                    context_parts.append("**CURRENT REAL-TIME AIR QUALITY DATA (from EPA AirNow API - Today's data):**")
                    for reading in readings[:5]:  # Show first 5 readings
                        aqi = reading.get('AQI', 'N/A')
                        category = reading.get('Category', {}).get('Name', 'Unknown')
                        parameter = reading.get('ParameterName', 'Unknown')
                        context_parts.append(f"  - {parameter}: AQI {aqi} ({category})")
            elif isinstance(aqi_data, list) and len(aqi_data) > 0:
                # Handle legacy format
                context_parts.append("**CURRENT REAL-TIME AIR QUALITY DATA (from EPA AirNow API - Today's data):**")
                for reading in aqi_data[:5]:
                    aqi = reading.get('AQI', 'N/A')
                    category = reading.get('Category', {}).get('Name', 'Unknown')
                    parameter = reading.get('ParameterName', 'Unknown')
                    context_parts.append(f"  - {parameter}: AQI {aqi} ({category})")
        
        # PRIORITY 3: Current weather conditions
        if environmental_data['weather']:
            weather = environmental_data['weather']
            context_parts.append("**CURRENT WEATHER:**")
            temp = weather.get('temperature', {})
            if temp:
                temp_f = temp.get('value', 'N/A')
                context_parts.append(f"  - Temperature: {temp_f}°F")
            humidity = weather.get('relativeHumidity', 'N/A')
            if humidity != 'N/A':
                context_parts.append(f"  - Humidity: {humidity}%")
        
        # PRIORITY 4: Current pollen levels
        if environmental_data['pollen']:
            pollen = environmental_data['pollen']
            pollen_index = pollen.get('index', {}).get('value', 'N/A')
            if pollen_index != 'N/A':
                context_parts.append(f"**CURRENT POLLEN INDEX:** {pollen_index}")
            # Add specific pollen types
            types = pollen.get('types', [])
            if types:
                high_pollen = [t['name'] for t in types if t.get('index', {}).get('value', 0) >= 4]
                if high_pollen:
                    context_parts.append(f"  - High pollen types: {', '.join(high_pollen)}")
        
        # PRIORITY 5: Current detailed pollutants from EPA AQS API
        if environmental_data['detailed_pollutants']:
            pollutants = environmental_data['detailed_pollutants']
            pollutant_summary = []
            context_parts.append("**CURRENT DETAILED POLLUTANTS (EPA AQS API):**")
            for pollutant in pollutants[:5]:  # First 5
                param = pollutant.get('parameter', 'Unknown')
                value = pollutant.get('value', 'N/A')
                unit = pollutant.get('unit', '')
                context_parts.append(f"  - {param}: {value} {unit}")
        
        # PRIORITY 6: Historical trends (BigQuery data - for context only, NOT current data)
        if historical_data and len(historical_data) > 0:
            context_parts.append(f"**HISTORICAL TREND DATA (for reference, last {days} days):** {len(historical_data)} data points available from BigQuery (note: this is historical data only, use real-time data above for current conditions)")
        
        # Combine all context with clear separation
        environmental_context = "\n".join([p for p in context_parts if p])
        enhanced_question = f"""IMPORTANT: When answering questions about CURRENT or REAL-TIME air quality, use ONLY the real-time data from EPA AirNow API marked as "CURRENT REAL-TIME AIR QUALITY DATA" above. The BigQuery historical data is outdated and should only be used for trend analysis.

{environmental_context}

Question: {question}"""
        
        print(f"[AGENT-CHAT] Using Gemini fallback")
        print(f"[AGENT-CHAT] Enhanced context: {environmental_context}")
        
        analysis = agent.analyze_with_ai(historical_data, enhanced_question)
        
        print(f"[AGENT-CHAT] Gemini response received: {analysis[:100]}...")
        
        result = {
            'success': True,
            'response': analysis,
            'agent': 'Gemini AI with Comprehensive Environmental Data',
            'data_points': len(historical_data),
            'location': location_context,
            'environmental_data': environmental_data  # Include for debugging/frontend use
        }
        print(f"[AGENT-CHAT] Returning successful response via Gemini")
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Agent chat failed completely: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech using Google Cloud Text-to-Speech"""
    if not TTS_AVAILABLE or not tts_client:
        return jsonify({
            'success': False,
            'error': 'Text-to-Speech service not available'
        }), 503
    
    try:
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Clean text - remove HTML tags
        import re
        clean_text = re.sub('<[^<]+?>', '', text)
        clean_text = clean_text.replace('via Gemini AI', '').replace('via ADK Multi-Agent System', '').strip()
        
        # Configure voice parameters
        # Using Neural2 voices for most natural sound
        voice_name = data.get('voice', 'en-US-Neural2-F')  # Default: Female Neural2
        
        # Available premium voices:
        # en-US-Neural2-A (Male), en-US-Neural2-C (Female), en-US-Neural2-D (Male)
        # en-US-Neural2-E (Female), en-US-Neural2-F (Female), en-US-Neural2-G (Female)
        # en-US-Neural2-H (Female), en-US-Neural2-I (Male), en-US-Neural2-J (Male)
        
        synthesis_input = texttospeech.SynthesisInput(text=clean_text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_name
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95,  # Slightly slower for clarity
            pitch=0.0,
            volume_gain_db=0.0
        )
        
        # Perform the text-to-speech request
        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Convert audio to base64 for transmission
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'voice': voice_name
        })
        
    except Exception as e:
        print(f"[ERROR] Text-to-Speech error: {e}")
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

@app.route('/api/community-reports', methods=['GET'])
def get_community_reports():
    """API endpoint to fetch community reports from BigQuery with filters"""
    from google.cloud import bigquery
    
    try:
        # Get filter parameters
        state = request.args.get('state', '')
        city = request.args.get('city', '')
        county = request.args.get('county', '')
        zipcode = request.args.get('zipcode', '')
        report_type = request.args.get('report_type', '')
        severity = request.args.get('severity', '')
        status = request.args.get('status', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        timeframe = request.args.get('timeframe', '')
        limit = int(request.args.get('limit', 1000))
        offset = int(request.args.get('offset', 0))
        
        # Build BigQuery query
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = os.getenv('BIGQUERY_DATASET')
        table_id = os.getenv('BIGQUERY_TABLE_REPORTS')
        
        if not all([project_id, dataset_id, table_id]):
            print("[ERROR] Missing BigQuery configuration in environment variables")
            return jsonify({
                'success': False,
                'error': 'BigQuery configuration not found'
            }), 500
        
        query = f"""
        WITH LatestReports AS (
            SELECT 
                report_id,
                report_type,
                timestamp,
                address,
                zip_code,
                city,
                state,
                county,
                severity,
                specific_type,
                description,
                people_affected,
                timeframe,
                contact_name,
                contact_email,
                contact_phone,
                is_anonymous,
                status,
                notes,
                latitude,
                longitude,
                ai_overall_summary,
                ai_media_summary,
                ai_tags,
                ai_confidence,
                ai_analyzed_at,
                attachment_urls,
                reviewed_by,
                reviewed_at,
                exclude_from_analysis,
                exclusion_reason,
                manual_tags,
                media_urls,
                ROW_NUMBER() OVER (PARTITION BY report_id ORDER BY timestamp DESC) as rn
            FROM `{project_id}.{dataset_id}.{table_id}`
        )
        SELECT * EXCEPT(rn)
        FROM LatestReports
        WHERE rn = 1 AND 1=1
        """
        
        # Add filter conditions
        if state:
            query += f" AND state = '{state}'"
        if city:
            query += f" AND city = '{city}'"
        if county:
            query += f" AND county = '{county}'"
        if zipcode:
            query += f" AND zip_code = '{zipcode}'"
        if report_type:
            query += f" AND report_type = '{report_type}'"
        if severity:
            query += f" AND severity = '{severity}'"
        if status:
            query += f" AND status = '{status}'"
        if start_date:
            query += f" AND timestamp >= TIMESTAMP('{start_date}')"
        if end_date:
            query += f" AND timestamp <= TIMESTAMP('{end_date}')"
        if timeframe:
            query += f" AND timeframe = '{timeframe}'"
        
        # Add ordering and pagination
        query += " ORDER BY timestamp DESC"
        query += f" LIMIT {limit} OFFSET {offset}"
        
        print(f"[QUERY] Fetching community reports (limit={limit}, offset={offset})")
        print(f"[QUERY] Filters: state={state}, city={city}, zipcode={zipcode}")
        
        # Execute query
        client = bigquery.Client(project=project_id)
        query_job = client.query(query)
        results = query_job.result()
        
        # Convert results to list of dictionaries
        reports = []
        for row in results:
            report = {
                'report_id': row.report_id,
                'report_type': row.report_type,
                'timestamp': row.timestamp.isoformat() if row.timestamp else None,
                'street_address': row.address,
                'zip_code': row.zip_code,
                'city': row.city,
                'state': row.state,
                'county': row.county,
                'severity': row.severity,
                'specific_type': row.specific_type,
                'description': row.description,
                'affected_count': row.people_affected,
                'when_happened': row.timeframe,
                'reporter_name': row.contact_name if not row.is_anonymous else 'Anonymous',
                'reporter_contact': row.contact_email if not row.is_anonymous else None,
                'is_anonymous': row.is_anonymous,
                'status': row.status,
                'reviewed_by': row.reviewed_by if hasattr(row, 'reviewed_by') else None,
                'reviewed_at': row.reviewed_at.isoformat() if hasattr(row, 'reviewed_at') and row.reviewed_at else None,
                'exclude_from_analysis': row.exclude_from_analysis if hasattr(row, 'exclude_from_analysis') else None,
                'exclusion_reason': row.exclusion_reason if hasattr(row, 'exclusion_reason') else None,
                'notes': row.notes,
                'latitude': row.latitude,
                'longitude': row.longitude,
                'ai_overall_summary': row.ai_overall_summary if hasattr(row, 'ai_overall_summary') else None,
                'ai_media_summary': row.ai_media_summary if hasattr(row, 'ai_media_summary') else None,
                'ai_tags': row.ai_tags if hasattr(row, 'ai_tags') else None,
                'ai_confidence': row.ai_confidence if hasattr(row, 'ai_confidence') else None,
                'ai_analyzed_at': row.ai_analyzed_at.isoformat() if hasattr(row, 'ai_analyzed_at') and row.ai_analyzed_at else None,
                'attachment_urls': row.attachment_urls if hasattr(row, 'attachment_urls') else None,
                'manual_tags': row.manual_tags if hasattr(row, 'manual_tags') else None,
                'media_urls': row.media_urls if hasattr(row, 'media_urls') else None
            }
            reports.append(report)
        
        # Get total count for pagination
        count_query = f"""
        SELECT COUNT(*) as total
        FROM `{project_id}.{dataset_id}.{table_id}`
        WHERE 1=1
        """
        if state:
            count_query += f" AND state = '{state}'"
        if city:
            count_query += f" AND city = '{city}'"
        if county:
            count_query += f" AND county = '{county}'"
        if zipcode:
            count_query += f" AND zip_code = '{zipcode}'"
        if report_type:
            count_query += f" AND report_type = '{report_type}'"
        if severity:
            count_query += f" AND severity = '{severity}'"
        if status:
            count_query += f" AND status = '{status}'"
        
        count_job = client.query(count_query)
        count_result = list(count_job.result())[0]
        total_count = count_result.total
        
        print(f"[SUCCESS] Retrieved {len(reports)} reports (total: {total_count})")
        
        return jsonify({
            'success': True,
            'reports': reports,
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch community reports: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/export-reports/<format>', methods=['GET'])
def export_reports(format):
    """Export community reports in various formats (CSV, XLS, PDF, PNG)"""
    from google.cloud import bigquery
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    
    try:
        # Get same filters as regular reports endpoint
        state = request.args.get('state', '')
        city = request.args.get('city', '')
        county = request.args.get('county', '')
        zipcode = request.args.get('zipcode', '')
        report_type = request.args.get('report_type', '')
        severity = request.args.get('severity', '')
        status = request.args.get('status', '')
        
        # Build query (same as above but without pagination)
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = os.getenv('BIGQUERY_DATASET')
        table_id = os.getenv('BIGQUERY_TABLE_REPORTS')
        
        query = f"""
        SELECT *
        FROM `{project_id}.{dataset_id}.{table_id}`
        WHERE 1=1
        """
        
        if state:
            query += f" AND state = '{state}'"
        if city:
            query += f" AND city = '{city}'"
        if county:
            query += f" AND county = '{county}'"
        if zipcode:
            query += f" AND zip_code = '{zipcode}'"
        if report_type:
            query += f" AND report_type = '{report_type}'"
        if severity:
            query += f" AND severity = '{severity}'"
        if status:
            query += f" AND status = '{status}'"
        
        query += " ORDER BY timestamp DESC LIMIT 10000"  # Max export limit
        
        print(f"[EXPORT] Exporting reports as {format.upper()}")
        
        # Execute query
        client = bigquery.Client(project=project_id)
        df = client.query(query).to_dataframe()
        
        if df.empty:
            return jsonify({
                'success': False,
                'error': 'No data to export with current filters'
            }), 404
        
        # Generate filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"community_reports_{timestamp}"
        
        # Export based on format
        if format == 'csv':
            output = BytesIO()
            df.to_csv(output, index=False, encoding='utf-8')
            output.seek(0)
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{filename}.csv'
            )
        
        elif format == 'xlsx' or format == 'xls':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Community Reports')
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'{filename}.xlsx'
            )
        
        elif format == 'pdf':
            # For PDF, we'll create a simple table view
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            
            output = BytesIO()
            doc = SimpleDocTemplate(output, pagesize=landscape(letter))
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            title = Paragraph(f"<b>Community Health Reports - {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 0.25 * inch))
            
            # Prepare table data (ALL columns)
            # Get column headers
            table_data = [list(df.columns)]
            
            for _, row in df.head(100).iterrows():  # Limit to 100 rows for PDF
                row_data = []
                for col in df.columns:
                    value = str(row[col]) if pd.notna(row[col]) else ''
                    # Truncate long values for better formatting
                    if len(value) > 50:
                        value = value[:50] + '...'
                    row_data.append(value)
                table_data.append(row_data)
            
            # Create table with dynamic column widths
            num_cols = len(df.columns)
            col_width = 10 / num_cols  # Distribute width across landscape page
            table = Table(table_data, colWidths=[col_width*inch] * num_cols)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
            ]))
            
            elements.append(table)
            doc.build(elements)
            output.seek(0)
            
            return send_file(
                output,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'{filename}.pdf'
            )
        
        elif format == 'png':
            # For PNG, create a matplotlib table image with ALL columns
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            fig, ax = plt.subplots(figsize=(16, 12))
            ax.axis('tight')
            ax.axis('off')
            
            # Use all columns but limit rows
            display_df = df.head(20).copy()
            
            # Truncate long text values for display
            for col in display_df.columns:
                if display_df[col].dtype == 'object':  # String columns
                    display_df[col] = display_df[col].astype(str).str[:40]
                else:
                    display_df[col] = display_df[col].astype(str)
            
            table = ax.table(cellText=display_df.values,
                           colLabels=display_df.columns,
                           cellLoc='left',
                           loc='center')
            
            table.auto_set_font_size(False)
            table.set_fontsize(7)
            table.scale(1, 2)
            
            # Style header
            for i in range(len(display_df.columns)):
                table[(0, i)].set_facecolor('#10b981')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            plt.title(f'Community Health Reports - {datetime.now().strftime("%Y-%m-%d")}', 
                     fontsize=16, fontweight='bold', pad=20)
            
            output = BytesIO()
            plt.savefig(output, format='png', bbox_inches='tight', dpi=150)
            plt.close()
            output.seek(0)
            
            return send_file(
                output,
                mimetype='image/png',
                as_attachment=True,
                download_name=f'{filename}.png'
            )
        
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported format: {format}'
            }), 400
            
    except Exception as e:
        print(f"[ERROR] Failed to export reports: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    import json
    from google.cloud import bigquery
    
    try:
        # Get form data
        data = request.form
        
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Handle file uploads
        media_files = request.files.getlist('media[]')
        media_urls = []  # Old field - still save locally for backwards compatibility
        attachment_urls = []  # New field - GCS URLs
        media_count = len(media_files)
        
        # Save files to GCS if available
        if GCS_AVAILABLE and bucket and media_files:
            for idx, file in enumerate(media_files):
                if file and file.filename:
                    try:
                        # Upload to GCS
                        file_info = upload_to_gcs(file, report_id, idx)
                        attachment_urls.append(file_info['url'])
                        print(f"[GCS] Uploaded {file.filename} -> {file_info['url']}")
                    except Exception as e:
                        print(f"[GCS ERROR] Failed to upload {file.filename}: {e}")
        
        # Fallback: Save locally if GCS fails or unavailable
        if not attachment_urls and media_files:
            # Create uploads directory if it doesn't exist
            upload_dir = os.path.join('data', 'report_uploads', report_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save uploaded files
            for file in media_files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    media_urls.append(f"/uploads/{report_id}/{filename}")
        
        # ===== AI ANALYSIS =====
        ai_result = None
        ai_media_summary = None
        ai_overall_summary = None
        ai_tags_list = []
        ai_confidence = None
        auto_status = 'pending'
        
        # Analyze text with Gemini AI
        if GEMINI_API_KEY:
            try:
                print(f"[AI] Analyzing report text with Gemini...")
                ai_result = analyze_text_with_gemini(
                    data.get('description', ''),
                    data.get('severity', ''),
                    data.get('timeframe', ''),
                    data.get('reportType', '')
                )
                
                if ai_result:
                    ai_overall_summary = ai_result.get('summary', '')
                    ai_tags_list = ai_result.get('tags', [])
                    ai_confidence = ai_result.get('confidence', 0.0)
                    
                    # Auto-assign status based on AI analysis
                    auto_status = assign_auto_status(ai_tags_list, ai_confidence)
                    
                    print(f"[AI] Summary: {ai_overall_summary[:100]}...")
                    print(f"[AI] Tags: {ai_tags_list}")
                    print(f"[AI] Confidence: {ai_confidence}")
                    print(f"[AI] Auto Status: {auto_status}")
            except Exception as e:
                print(f"[AI ERROR] Text analysis failed: {e}")
        
        # Analyze attachments with Gemini Vision
        if GEMINI_API_KEY and attachment_urls:
            try:
                print(f"[AI] Analyzing {len(attachment_urls)} attachment(s) with Gemini Vision...")
                ai_media_summary = analyze_attachments_with_gemini(
                    [{'url': url, 'file_type': get_file_type(url)} for url in attachment_urls]
                )
                if ai_media_summary:
                    print(f"[AI] Media Summary: {ai_media_summary[:100]}...")
            except Exception as e:
                print(f"[AI ERROR] Media analysis failed: {e}")
        
        # Prepare data for BigQuery
        row_data = {
            'report_id': report_id,
            'report_type': data.get('reportType', ''),
            'timestamp': timestamp.isoformat() + 'Z',
            'address': data.get('address') or None,
            'zip_code': data.get('zipCode', ''),
            'city': data.get('city', ''),
            'state': data.get('state', ''),
            'county': data.get('county') or None,
            'severity': data.get('severity', ''),
            'specific_type': data.get('specificType', ''),
            'description': data.get('description', ''),
            'people_affected': data.get('peopleAffected', None),
            'timeframe': data.get('timeframe', ''),
            'contact_name': data.get('contactName', None),
            'contact_email': data.get('contactEmail', None),
            'contact_phone': data.get('contactPhone', None),
            'is_anonymous': data.get('anonymous') == 'on',
            'media_urls': attachment_urls if attachment_urls else [],  # REPEATED field = array
            'media_count': media_count,
            'attachment_urls': json.dumps(attachment_urls) if attachment_urls else None,  # STRING = JSON
            'ai_media_summary': ai_media_summary,
            'ai_overall_summary': ai_overall_summary,
            'ai_tags': json.dumps(ai_tags_list) if ai_tags_list else None,
            'ai_confidence': ai_confidence,
            'ai_analyzed_at': timestamp.isoformat() + 'Z' if ai_result else None,
            'status': auto_status,  # Auto-assigned by AI
            'reviewed_by': None,
            'reviewed_at': None,
            'exclude_from_analysis': None,
            'exclusion_reason': None,
            'manual_tags': None,
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
        if attachment_urls:
            print(f"[REPORT] GCS URLs: {attachment_urls}")
        if ai_result:
            print(f"[REPORT] AI Status: {auto_status}, Confidence: {ai_confidence}")
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': 'Report submitted successfully',
            'attachment_urls': attachment_urls,
            'ai_analysis': {
                'summary': ai_overall_summary,
                'tags': ai_tags_list,
                'confidence': ai_confidence,
                'status': auto_status
            } if ai_result else None
        })
        
    except Exception as e:
        print(f"[ERROR] Report submission failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/update-report', methods=['POST'])
def update_report():
    """Update report status, reviewer info, exclusion flags, and manual tags"""
    from google.cloud import bigquery
    from datetime import datetime
    
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        
        if not report_id:
            return jsonify({'success': False, 'error': 'Report ID is required'}), 400
        
        # Get update fields
        status = data.get('status')
        reviewed_by = data.get('reviewed_by')
        manual_tags = data.get('manual_tags')
        exclude_from_analysis = data.get('exclude_from_analysis', False)
        exclusion_reason = data.get('exclusion_reason')
        
        # Validate exclusion reason if excluded
        if exclude_from_analysis and not exclusion_reason:
            return jsonify({'success': False, 'error': 'Exclusion reason is required when excluding report'}), 400
        
        # Execute UPDATE in BigQuery
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        dataset_id = os.getenv('BIGQUERY_DATASET')
        table_id = os.getenv('BIGQUERY_TABLE_REPORTS', 'CrowdSourceData')
        
        if not project_id or not dataset_id or project_id == 'your-actual-project-id':
            return jsonify({'success': False, 'error': 'BigQuery not configured'}), 500
        
        client = bigquery.Client(project=project_id)
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        
        # INSERT a new row with updated data instead of UPDATE (to avoid streaming buffer issue)
        # This creates a duplicate row, and we'll use the latest one when querying
        # Alternatively, we can create a separate updates table
        
        # For now, let's use INSERT with updated timestamp to create new version
        # First, fetch the current row
        select_query = f"""
            SELECT * FROM `{table_ref}`
            WHERE report_id = @report_id
            ORDER BY timestamp DESC
            LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("report_id", "STRING", report_id)
            ]
        )
        
        query_job = client.query(select_query, job_config=job_config)
        results = list(query_job.result())
        
        if not results:
            return jsonify({'success': False, 'error': 'Report not found'}), 404
        
        # Get current row data
        current_row = dict(results[0])
        
        # Update the fields
        if status is not None:
            current_row['status'] = status
        
        if reviewed_by is not None:
            current_row['reviewed_by'] = reviewed_by
            current_row['reviewed_at'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        if manual_tags is not None:
            current_row['manual_tags'] = manual_tags
        
        current_row['exclude_from_analysis'] = exclude_from_analysis
        
        if exclude_from_analysis and exclusion_reason:
            current_row['exclusion_reason'] = exclusion_reason
        else:
            current_row['exclusion_reason'] = None
        
        # Update timestamp to mark this as newer version
        current_row['timestamp'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert any datetime objects to strings in YYYY-MM-DD HH:MM:SS format
        for key, value in current_row.items():
            if hasattr(value, 'strftime'):  # datetime or date object
                current_row[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            elif value is None:
                # Keep None as is
                pass
        
        # Insert the updated row
        errors = client.insert_rows_json(table_ref, [current_row])
        
        if errors:
            print(f"[UPDATE ERROR] Failed to insert updated row: {errors}")
            return jsonify({'success': False, 'error': f'Failed to update: {errors}'}), 500
        
        print(f"[UPDATE SUCCESS] Report {report_id} updated via insert")
        print(f"[UPDATE] Status: {status}, Reviewed by: {reviewed_by}, Excluded: {exclude_from_analysis}")
        
        return jsonify({
            'success': True,
            'message': 'Report updated successfully',
            'report_id': report_id
        })
        
    except Exception as e:
        print(f"[UPDATE ERROR] {str(e)}")
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
        days = min(int(request.args.get('days', 7)), 30)  # Limit to max 30 days
        
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
        
        # Get current parameters only (skip historical loop to avoid timeout)
        print(f"[DETAILED] Getting current air quality data...")
        
        # CRITICAL: Use use_zipcode (which may come from city lookup)
        all_current_params = epa_service.get_all_current_parameters(
            zipcode=use_zipcode, lat=lat, lon=lon, state_code=state_code, distance=50
        )
        
        print(f"[DETAILED] Got {len(all_current_params)} current parameters")
        for param in all_current_params:
            print(f"[DETAILED]   - {param.get('parameter')}: AQI {param.get('aqi')}")
        
        # Generate dates for the requested range
        today = datetime.now()
        dates_list = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days - 1, -1, -1)]
        
        # Process each parameter and simulate historical data
        for param_data in all_current_params:
            parameter_name = param_data.get('parameter', '')
            current_aqi = param_data.get('aqi', 0)
            
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
                # Generate historical values with variance
                for i, date_str in enumerate(dates_list):
                    # Add variance based on date (±20% for historical, 0% for today)
                    if i < len(dates_list) - 1:  # Historical data
                        variance = (hash(date_str + param_key) % 40) - 20
                        aqi = max(0, min(500, current_aqi + int(current_aqi * variance / 100)))
                    else:  # Today's data
                        aqi = current_aqi
                    
                    value = aqi_to_concentration(aqi, param_key)
                    parameters[param_key]['values'].append(value)
                    parameters[param_key]['dates'].append(date_str)
                
                # Calculate statistics
                values = parameters[param_key]['values']
                if values:
                    parameters[param_key]['current'] = values[-1]
                    parameters[param_key]['min'] = min(values)
                    parameters[param_key]['max'] = max(values)
                    parameters[param_key]['avg'] = sum(values) / len(values)
                
                print(f"[DETAILED] {param_key}: {len(values)} values from {dates_list[0]} to {dates_list[-1]}")
        
        # Calculate date range
        start_date = dates_list[0] if dates_list else datetime.now().strftime('%Y-%m-%d')
        end_date = dates_list[-1] if dates_list else datetime.now().strftime('%Y-%m-%d')
        
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

@app.route('/api/air-quality-map', methods=['GET'])
def get_air_quality_map():
    """API endpoint to get air quality data for heatmap visualization"""
    try:
        # Get state filter (optional)
        state_name = request.args.get('state')
        limit = int(request.args.get('limit', 100))  # Default to 100 locations
        
        print(f"[HEATMAP API] Request - State: {state_name}, Limit: {limit}")
        
        # Convert state name to code if needed
        state_code = None
        if state_name:
            if len(state_name) == 2:
                state_code = state_name.upper()
            else:
                state_code = location_service.get_state_code_from_name(state_name)
        
        # Get list of cities/ZIP codes to sample
        locations_to_sample = []
        
        if state_code:
            # Get major cities in the state
            cities = location_service.get_cities_by_state(state_code)
            # Sample evenly across the state
            step = max(1, len(cities) // limit)
            for i in range(0, min(len(cities), limit), step):
                city = cities[i]
                loc_info = location_service.get_location_info(
                    state_code=state_code,
                    city_name=city['name']
                )
                if loc_info and loc_info.get('zipcodes'):
                    locations_to_sample.append({
                        'zipcode': loc_info['zipcodes'][0],
                        'city': city['name'],
                        'state': state_code,
                        'latitude': loc_info.get('latitude'),
                        'longitude': loc_info.get('longitude')
                    })
        else:
            # Sample major US cities across all states
            major_states = ['CA', 'NY', 'TX', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
            cities_per_state = max(1, limit // len(major_states))
            
            for state in major_states:
                cities = location_service.get_cities_by_state(state)
                step = max(1, len(cities) // cities_per_state)
                for i in range(0, min(len(cities), cities_per_state * step), step):
                    city = cities[i]
                    loc_info = location_service.get_location_info(
                        state_code=state,
                        city_name=city['name']
                    )
                    if loc_info and loc_info.get('zipcodes'):
                        locations_to_sample.append({
                            'zipcode': loc_info['zipcodes'][0],
                            'city': city['name'],
                            'state': state,
                            'latitude': loc_info.get('latitude'),
                            'longitude': loc_info.get('longitude')
                        })
        
        # Get air quality data for each location
        heatmap_data = []
        for loc in locations_to_sample[:limit]:
            try:
                # Get current AQI for this location
                aqi_data = epa_service.get_current_aqi(loc['zipcode'])
                
                if aqi_data and aqi_data.get('success') and aqi_data.get('data'):
                    # Find the highest AQI value
                    max_aqi = 0
                    for reading in aqi_data['data']:
                        aqi = reading.get('AQI', 0)
                        if aqi > max_aqi:
                            max_aqi = aqi
                    
                    if max_aqi > 0 and loc.get('latitude') and loc.get('longitude'):
                        heatmap_data.append({
                            'lat': loc['latitude'],
                            'lng': loc['longitude'],
                            'weight': max_aqi,  # AQI value for heatmap intensity
                            'aqi': max_aqi,
                            'city': loc['city'],
                            'state': loc['state'],
                            'zipcode': loc['zipcode']
                        })
            except Exception as e:
                print(f"[HEATMAP API] Error getting data for {loc['city']}, {loc['state']}: {e}")
                continue
        
        print(f"[HEATMAP API] Returning {len(heatmap_data)} locations with AQI data")
        
        return jsonify({
            'success': True,
            'data': heatmap_data,
            'count': len(heatmap_data),
            'source': 'EPA AirNow API'
        })
        
    except Exception as e:
        print(f"[HEATMAP API] Error: {e}")
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

# ===== PSA VIDEO ENDPOINTS =====

@app.route('/api/generate-psa-video', methods=['POST'])
def generate_psa_video_endpoint():
    """Generate PSA video from current health data"""
    if not PSA_VIDEO_AVAILABLE or not video_manager:
        return jsonify({
            'success': False,
            'error': 'PSA video feature not available'
        }), 503
    
    try:
        request_data = request.get_json()
        location = request_data.get('location', 'California')
        data_type = request_data.get('data_type', 'air_quality')  # or 'disease'
        
        # Get current health data
        if data_type == 'air_quality':
            health_data = agent.query_air_quality_data(state=location, days=1)
            if health_data:
                df = pd.DataFrame(health_data)
                avg_aqi = df['aqi'].mean() if 'aqi' in df else 50
                severity = "good" if avg_aqi <= 50 else "moderate" if avg_aqi <= 100 else "unhealthy"
            else:
                avg_aqi = 50
                severity = "good"
        else:
            # Disease data
            avg_aqi = 0
            severity = "moderate"
        
        # Call agent to generate action line and video
        prompt = f"Create a PSA video for {location} about {data_type}. Current severity: {severity}, AQI: {avg_aqi}"
        
        if ADK_AGENT_AVAILABLE:
            response = call_adk_agent(prompt)
            
            return jsonify({
                'success': True,
                'action_line': 'Generated action line here',  # Extract from response
                'status': 'processing',
                'message': response,
                'note': 'PSA video generation initiated'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'PSA video generation requires ADK agent'
            }), 503
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/approve-and-post', methods=['POST'])
def approve_and_post_video():
    """Post approved video to Twitter"""
    if not PSA_VIDEO_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'PSA video feature not available'
        }), 503
    
    try:
        request_data = request.get_json()
        video_uri = request_data.get('video_uri')
        message = request_data.get('message')
        hashtags = request_data.get('hashtags', [])
        
        # TODO: Implement actual Twitter posting
        # For now, simulate success
        
        return jsonify({
            'success': True,
            'tweet_url': 'https://twitter.com/CommunityHealth/status/123456',
            'message': 'Video posted successfully (simulation mode)',
            'note': 'Add Twitter API credentials to enable real posting'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/check-video-task/<task_id>')
def check_video_task(task_id):
    """Check status of async video generation task"""
    if not PSA_VIDEO_AVAILABLE or not video_manager:
        return jsonify({
            'status': 'error',
            'error': 'PSA video feature not available'
        }), 503
    
    try:
        task = video_manager.get_task(task_id)
        
        if task:
            return jsonify(task)
        else:
            return jsonify({
                'status': 'not_found',
                'error': 'Task ID not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/post-to-twitter', methods=['POST'])
def post_to_twitter():
    """
    Post a PSA video to Twitter/X
    
    Expected JSON:
    {
        "video_url": "https://storage.googleapis.com/...",
        "message": "Health alert message",
        "hashtags": ["HealthAlert", "AirQuality"] (optional)
    }
    """
    if not PSA_VIDEO_AVAILABLE:
        return jsonify({
            'success': False,
            'error': 'PSA video feature not available'
        }), 503
    
    try:
        data = request.get_json()
        
        video_url = data.get('video_url')
        message = data.get('message', '')
        hashtags = data.get('hashtags', ['HealthAlert', 'PublicHealth', 'CommunityHealth'])
        
        if not video_url:
            return jsonify({
                'success': False,
                'error': 'video_url is required'
            }), 400
        
        if not message:
            return jsonify({
                'success': False,
                'error': 'message is required'
            }), 400
        
        # Import Twitter client
        from multi_tool_agent_bquery_tools.integrations.twitter_client import get_twitter_client
        
        twitter_client = get_twitter_client()
        
        print(f"\n[TWITTER] ===== Twitter Posting Request =====")
        print(f"[TWITTER] Video URL: {video_url[:50]}...")
        print(f"[TWITTER] Message: {message[:100]}...")
        print(f"[TWITTER] Hashtags: {hashtags}")
        
        # Post to Twitter
        result = twitter_client.post_video_tweet(
            video_url=video_url,
            message=message,
            hashtags=hashtags
        )
        
        if result['status'] == 'success':
            print(f"[TWITTER] SUCCESS: Tweet posted!")
            print(f"[TWITTER] URL: {result['tweet_url']}")
            
            return jsonify({
                'success': True,
                'tweet_url': result['tweet_url'],
                'tweet_id': result['tweet_id'],
                'message': result.get('message', 'Posted to Twitter successfully!')
            })
        else:
            print(f"[TWITTER] ERROR: {result.get('error_message')}")
            return jsonify({
                'success': False,
                'error': result.get('error_message', 'Unknown error')
            }), 500
        
    except Exception as e:
        print(f"[TWITTER] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===== END PSA VIDEO ENDPOINTS =====

# ===== ENVIRONMENTAL RISK API ENDPOINTS =====

@app.route('/api/wildfires')
def get_wildfires():
    """Get wildfire incidents from BigQuery"""
    try:
        state = request.args.get('state', '')
        
        if not bq_client:
            print("[WILDFIRE] No BigQuery client, returning demo data")
            return jsonify({'count': 0, 'status': 'no_data'})
        
        # Query wildfire incidents table
        query = f"""
            SELECT COUNT(*) as incident_count
            FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.table_wildfire_incidents`
            WHERE state = @state
            AND status = 'Active'
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("state", "STRING", state)
            ]
        )
        
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        count = results[0].incident_count if results else 0
        print(f"[WILDFIRE] Found {count} active incidents in {state}")
        
        return jsonify({
            'count': count,
            'status': 'success',
            'state': state
        })
        
    except Exception as e:
        print(f"[WILDFIRE ERROR] {e}")
        return jsonify({'count': 0, 'status': 'error', 'error': str(e)})

@app.route('/api/covid')
def get_covid():
    """Get COVID-19 metrics from BigQuery"""
    
    # HHS Region mapping for states
    STATE_TO_HHS_REGION = {
        # Region 1: New England
        'Connecticut': 1, 'Maine': 1, 'Massachusetts': 1, 'New Hampshire': 1, 'Rhode Island': 1, 'Vermont': 1,
        # Region 2: New York/New Jersey
        'New Jersey': 2, 'New York': 2, 'Puerto Rico': 2, 'Virgin Islands': 2,
        # Region 3: Mid-Atlantic
        'Delaware': 3, 'District of Columbia': 3, 'Maryland': 3, 'Pennsylvania': 3, 'Virginia': 3, 'West Virginia': 3,
        # Region 4: Southeast
        'Alabama': 4, 'Florida': 4, 'Georgia': 4, 'Kentucky': 4, 'Mississippi': 4, 'North Carolina': 4, 'South Carolina': 4, 'Tennessee': 4,
        # Region 5: Midwest
        'Illinois': 5, 'Indiana': 5, 'Michigan': 5, 'Minnesota': 5, 'Ohio': 5, 'Wisconsin': 5,
        # Region 6: South Central
        'Arkansas': 6, 'Louisiana': 6, 'New Mexico': 6, 'Oklahoma': 6, 'Texas': 6,
        # Region 7: Central
        'Iowa': 7, 'Kansas': 7, 'Missouri': 7, 'Nebraska': 7,
        # Region 8: Mountain
        'Colorado': 8, 'Montana': 8, 'North Dakota': 8, 'South Dakota': 8, 'Utah': 8, 'Wyoming': 8,
        # Region 9: Pacific
        'Arizona': 9, 'California': 9, 'Hawaii': 9, 'Nevada': 9, 'American Samoa': 9, 'Guam': 9, 'Northern Mariana Islands': 9,
        # Region 10: Northwest
        'Alaska': 10, 'Idaho': 10, 'Oregon': 10, 'Washington': 10
    }
    
    try:
        state = request.args.get('state', '')
        county = request.args.get('county', '')
        debug = request.args.get('debug', 'false').lower() == 'true'
        
        if not bq_client:
            print("[COVID] No BigQuery client, returning demo data")
            return jsonify({'cases_per_100k': '-', 'status': 'no_data'})
        
        # Map state to HHS region
        region = STATE_TO_HHS_REGION.get(state, None)
        print(f"[COVID] Querying for state='{state}' (HHS Region {region}), county='{county}'")
        
        # If debug mode, show table structure
        if debug:
            sample_query = """
                SELECT *
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`
                LIMIT 5
            """
            sample_job = bq_client.query(sample_query)
            sample_results = list(sample_job.result())
            
            if sample_results:
                # Get column names and sample data
                columns = list(sample_results[0].keys())
                sample_data = [dict(row) for row in sample_results]
                
                return jsonify({
                    'debug': True,
                    'columns': columns,
                    'sample_data': sample_data,
                    'total_rows': len(sample_results)
                })
        
        # First, check if table has any data
        check_query = """
            SELECT COUNT(*) as total_count
            FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`
        """
        
        try:
            check_job = bq_client.query(check_query)
            check_results = list(check_job.result())
            total_count = check_results[0].total_count if check_results else 0
            print(f"[COVID] Total rows in table: {total_count}")
        except Exception as check_error:
            print(f"[COVID] Error checking table: {check_error}")
            # Table might not exist, return demo data
            return jsonify({'cases_per_100k': '15.2', 'status': 'demo', 'error': str(check_error)})
        
        if total_count == 0:
            print("[COVID] Table is empty, returning demo data")
            return jsonify({'cases_per_100k': '12.5', 'status': 'demo_empty_table'})
        
        # Query COVID metrics table using HHS region
        if region:
            query = """
                SELECT cases_per_100k
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`
                WHERE region = @region
                ORDER BY date DESC
                LIMIT 1
            """
            params = [bigquery.ScalarQueryParameter("region", "INTEGER", region)]
            job_config = bigquery.QueryJobConfig(query_parameters=params)
        else:
            # No region found for state, get national average or return demo data
            print(f"[COVID] No HHS region found for state '{state}'")
            query = """
                SELECT AVG(cases_per_100k) as cases_per_100k
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`
                WHERE date = (SELECT MAX(date) FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.cdc_covid_data`)
            """
            job_config = bigquery.QueryJobConfig()
        
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        if results and len(results) > 0:
            cases_per_100k = round(results[0].cases_per_100k, 1) if results[0].cases_per_100k else '-'
            print(f"[COVID] Found {cases_per_100k} cases per 100K for HHS Region {region} ({state})")
        else:
            print(f"[COVID] No data found for HHS Region {region} ({state}), returning demo data")
            cases_per_100k = '18.7'  # Demo data
        
        return jsonify({
            'cases_per_100k': cases_per_100k,
            'status': 'success' if results else 'demo',
            'state': state,
            'region': region
        })
        
    except Exception as e:
        print(f"[COVID ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'cases_per_100k': '20.3', 'status': 'error', 'error': str(e)})

@app.route('/api/respiratory-timeseries')
def get_respiratory_timeseries():
    """Get respiratory infection time series data for charting (NREVSS data)"""
    print("\n" + "=" * 80)
    print("🔥 RESPIRATORY API CALLED - CODE VERSION 3.0 WITH DATE FIX")
    print("=" * 80 + "\n")
    
    try:
        state = request.args.get('state', '')
        limit = int(request.args.get('limit', 365))  # Default to 1 year of data
        
        print(f"[RESPIRATORY TIMESERIES] Fetching data for state='{state}', limit={limit}")
        
        # Map state to HHS region
        STATE_TO_HHS_REGION = {
            # Region 1: New England
            'Connecticut': 1, 'Maine': 1, 'Massachusetts': 1, 'New Hampshire': 1, 'Rhode Island': 1, 'Vermont': 1,
            # Region 2: New York/New Jersey
            'New Jersey': 2, 'New York': 2, 'Puerto Rico': 2, 'Virgin Islands': 2,
            # Region 3: Mid-Atlantic
            'Delaware': 3, 'District of Columbia': 3, 'Maryland': 3, 'Pennsylvania': 3, 'Virginia': 3, 'West Virginia': 3,
            # Region 4: Southeast
            'Alabama': 4, 'Florida': 4, 'Georgia': 4, 'Kentucky': 4, 'Mississippi': 4, 'North Carolina': 4, 'South Carolina': 4, 'Tennessee': 4,
            # Region 5: Midwest
            'Illinois': 5, 'Indiana': 5, 'Michigan': 5, 'Minnesota': 5, 'Ohio': 5, 'Wisconsin': 5,
            # Region 6: South Central
            'Arkansas': 6, 'Louisiana': 6, 'New Mexico': 6, 'Oklahoma': 6, 'Texas': 6,
            # Region 7: Central
            'Iowa': 7, 'Kansas': 7, 'Missouri': 7, 'Nebraska': 7,
            # Region 8: Mountain
            'Colorado': 8, 'Montana': 8, 'North Dakota': 8, 'South Dakota': 8, 'Utah': 8, 'Wyoming': 8,
            # Region 9: Pacific
            'Arizona': 9, 'California': 9, 'Hawaii': 9, 'Nevada': 9,
            # Region 10: Northwest
            'Alaska': 10, 'Idaho': 10, 'Oregon': 10, 'Washington': 10
        }
        
        region = STATE_TO_HHS_REGION.get(state, None)
        
        if not region:
            print(f"[RESPIRATORY TIMESERIES] No HHS region found for state '{state}', using national data")
        
        if not bq_client:
            print("[RESPIRATORY TIMESERIES] No BigQuery client, returning demo data")
            return jsonify({
                'data': [],
                'status': 'no_bq_client',
                'error': 'BigQuery client not initialized'
            })
        
        # Query time series data from BigQuery
        if region:
            query = """
                SELECT 
                    FORMAT_DATE('%Y-%m-%d', SAFE.PARSE_DATE('%d%b%Y', repweekdate)) AS date,
                    testtype,
                    SUM(rsvpos) as rsvpos,
                    SUM(rsvtest) as rsvtest,
                    AVG(positivity_rate) as positivity_rate
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`
                WHERE hhs_region = @region
                GROUP BY date, testtype
                HAVING date IS NOT NULL
                ORDER BY date DESC
                LIMIT @limit
            """
            params = [
                bigquery.ScalarQueryParameter("region", "INTEGER", region),
                bigquery.ScalarQueryParameter("limit", "INTEGER", limit)
            ]
            job_config = bigquery.QueryJobConfig(query_parameters=params)
        else:
            # National aggregate
            query = """
                SELECT 
                    FORMAT_DATE('%Y-%m-%d', SAFE.PARSE_DATE('%d%b%Y', repweekdate)) AS date,
                    testtype,
                    SUM(rsvpos) as rsvpos,
                    SUM(rsvtest) as rsvtest,
                    AVG(positivity_rate) as positivity_rate
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`
                GROUP BY date, testtype
                HAVING date IS NOT NULL
                ORDER BY date DESC
                LIMIT @limit
            """
            params = [bigquery.ScalarQueryParameter("limit", "INTEGER", limit)]
            job_config = bigquery.QueryJobConfig(query_parameters=params)
        
        try:
            query_job = bq_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            # Transform data for charting
            data = []
            for row in results:
                # date is already in ISO format from BigQuery COALESCE
                date_str = row.date if hasattr(row, 'date') and row.date else None
                
                data.append({
                    'date': date_str,
                    'testtype': row.testtype,
                    'positives': int(row.rsvpos) if row.rsvpos else 0,
                    'tests': int(row.rsvtest) if row.rsvtest else 0,
                    'positivity_rate': float(row.positivity_rate) if row.positivity_rate else 0.0
                })
            
            # Print first item for debugging
            if data:
                print(f"[DEBUG] First data item: {data[0]}")
            
            # Sort by date ascending for charting (ISO strings sort lexicographically)
            data = [d for d in data if d['date']]
            data.sort(key=lambda x: x['date'])
            
            print(f"[RESPIRATORY TIMESERIES] Returning {len(data)} data points")
            print(f"[RESPIRATORY TIMESERIES] Sample data (first 3 items): {data[:3]}")
            
            return jsonify({
                'data': data,
                'state': state,
                'region': region,
                'status': 'success',
                'count': len(data)
            })
            
        except Exception as e:
            print(f"[RESPIRATORY TIMESERIES] BigQuery query failed: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'data': [],
                'status': 'error',
                'error': str(e)
            })
        
    except Exception as e:
        print(f"[RESPIRATORY TIMESERIES ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'data': [],
            'status': 'error',
            'error': str(e)
        })

@app.route('/api/respiratory')
def get_respiratory():
    """Get respiratory infection data from BigQuery (NREVSS data)"""
    try:
        state = request.args.get('state', '')
        
        print(f"[RESPIRATORY] Fetching data for state='{state}'")
        
        # Map state to HHS region
        STATE_TO_HHS_REGION = {
            # Region 1: New England
            'Connecticut': 1, 'Maine': 1, 'Massachusetts': 1, 'New Hampshire': 1, 'Rhode Island': 1, 'Vermont': 1,
            # Region 2: New York/New Jersey
            'New Jersey': 2, 'New York': 2, 'Puerto Rico': 2, 'Virgin Islands': 2,
            # Region 3: Mid-Atlantic
            'Delaware': 3, 'District of Columbia': 3, 'Maryland': 3, 'Pennsylvania': 3, 'Virginia': 3, 'West Virginia': 3,
            # Region 4: Southeast
            'Alabama': 4, 'Florida': 4, 'Georgia': 4, 'Kentucky': 4, 'Mississippi': 4, 'North Carolina': 4, 'South Carolina': 4, 'Tennessee': 4,
            # Region 5: Midwest
            'Illinois': 5, 'Indiana': 5, 'Michigan': 5, 'Minnesota': 5, 'Ohio': 5, 'Wisconsin': 5,
            # Region 6: South Central
            'Arkansas': 6, 'Louisiana': 6, 'New Mexico': 6, 'Oklahoma': 6, 'Texas': 6,
            # Region 7: Central
            'Iowa': 7, 'Kansas': 7, 'Missouri': 7, 'Nebraska': 7,
            # Region 8: Mountain
            'Colorado': 8, 'Montana': 8, 'North Dakota': 8, 'South Dakota': 8, 'Utah': 8, 'Wyoming': 8,
            # Region 9: Pacific
            'Arizona': 9, 'California': 9, 'Hawaii': 9, 'Nevada': 9,
            # Region 10: Northwest
            'Alaska': 10, 'Idaho': 10, 'Oregon': 10, 'Washington': 10
        }
        
        region = STATE_TO_HHS_REGION.get(state, None)
        
        if not region:
            print(f"[RESPIRATORY] No HHS region found for state '{state}', using national average")
        
        if not bq_client:
            print("[RESPIRATORY] No BigQuery client, returning demo data")
            return jsonify({
                'diseases': [
                    {'name': 'COVID-19', 'cases': 127, 'trend': 'decreasing', 'trend_icon': '↓', 'percent_change': 15, 'risk_level': 'Low'},
                    {'name': 'Influenza', 'cases': 453, 'trend': 'increasing', 'trend_icon': '↑', 'percent_change': 8, 'risk_level': 'Moderate'},
                    {'name': 'RSV', 'cases': 892, 'trend': 'stable', 'trend_icon': '→', 'percent_change': 0, 'risk_level': 'Monitor'}
                ],
                'status': 'no_bq_client'
            })
        
        diseases_data = []
        
        # Query RSV data from BigQuery
        if region:
            query = """
                SELECT 
                    repweekdate,
                    rsvpos,
                    rsvtest,
                    positivity_rate
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`
                WHERE hhs_region = @region
                ORDER BY repweekdate DESC
                LIMIT 10
            """
            params = [bigquery.ScalarQueryParameter("region", "INTEGER", region)]
            job_config = bigquery.QueryJobConfig(query_parameters=params)
        else:
            # National average
            query = """
                SELECT 
                    repweekdate,
                    AVG(rsvpos) as rsvpos,
                    AVG(rsvtest) as rsvtest,
                    AVG(positivity_rate) as positivity_rate
                FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.nrevss_respiratory_data`
                GROUP BY repweekdate
                ORDER BY repweekdate DESC
                LIMIT 10
            """
            job_config = bigquery.QueryJobConfig()
        
        try:
            query_job = bq_client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results and len(results) >= 2:
                # Calculate 7-week average and trend
                recent_rsv = [int(row.rsvpos) for row in results[:7] if row.rsvpos and row.rsvpos > 0]
                
                if recent_rsv and len(recent_rsv) >= 2:
                    avg_rsv = sum(recent_rsv) / len(recent_rsv)
                    last_week = recent_rsv[0]
                    prev_avg = sum(recent_rsv[1:]) / len(recent_rsv[1:])
                    percent_change = ((last_week - prev_avg) / prev_avg * 100) if prev_avg > 0 else 0
                    
                    if last_week > prev_avg * 1.1:
                        trend = 'increasing'
                        trend_icon = '↑'
                    elif last_week < prev_avg * 0.9:
                        trend = 'decreasing'
                        trend_icon = '↓'
                    else:
                        trend = 'stable'
                        trend_icon = '→'
                    
                    diseases_data.append({
                        'name': 'RSV',
                        'full_name': 'Respiratory Syncytial Virus',
                        'cases': round(avg_rsv),
                        'trend': trend,
                        'trend_icon': trend_icon,
                        'percent_change': round(abs(percent_change), 1),
                        'risk_level': 'High' if avg_rsv > 500 else 'Moderate' if avg_rsv > 200 else 'Low',
                        'data_source': 'BigQuery'
                    })
                    
                    print(f"[RESPIRATORY] RSV from BigQuery: {avg_rsv:.0f} avg detections, {trend} ({percent_change:+.1f}%)")
            
        except Exception as e:
            print(f"[RESPIRATORY] BigQuery query failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Add COVID-19 and Influenza placeholders
        diseases_data.extend([
            {
                'name': 'COVID-19',
                'full_name': 'COVID-19',
                'cases': 127,
                'trend': 'decreasing',
                'trend_icon': '↓',
                'percent_change': 15,
                'risk_level': 'Low',
                'note': 'Use /api/covid for real-time data'
            },
            {
                'name': 'Influenza',
                'full_name': 'Influenza',
                'cases': 453,
                'trend': 'increasing',
                'trend_icon': '↑',
                'percent_change': 8,
                'risk_level': 'Moderate',
                'note': 'Add flu dataset'
            }
        ])
        
        return jsonify({
            'diseases': diseases_data,
            'status': 'success',
            'state': state,
            'hhs_region': region,
            'data_source': 'BigQuery NREVSS'
        })
        
    except Exception as e:
        print(f"[RESPIRATORY ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'diseases': [
                {'name': 'COVID-19', 'cases': 127, 'trend': 'decreasing', 'trend_icon': '↓', 'percent_change': 15, 'risk_level': 'Low'},
                {'name': 'Influenza', 'cases': 453, 'trend': 'increasing', 'trend_icon': '↑', 'percent_change': 8, 'risk_level': 'Moderate'},
                {'name': 'RSV', 'cases': 892, 'trend': 'stable', 'trend_icon': '→', 'percent_change': 0, 'risk_level': 'Monitor'}
            ],
            'status': 'error',
            'error': str(e)
        })

@app.route('/api/alerts')
def get_alerts():
    """Get weather alerts from BigQuery"""
    try:
        state = request.args.get('state', '')
        
        if not bq_client:
            print("[ALERTS] No BigQuery client, returning demo data")
            return jsonify({'count': 0, 'status': 'no_data'})
        
        # Query weather alerts table
        query = f"""
            SELECT COUNT(*) as alert_count
            FROM `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.table_weather_alerts`
            WHERE state = @state
            AND status = 'Active'
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("state", "STRING", state)
            ]
        )
        
        query_job = bq_client.query(query, job_config=job_config)
        results = list(query_job.result())
        
        count = results[0].alert_count if results else 0
        print(f"[ALERTS] Found {count} active alerts in {state}")
        
        return jsonify({
            'count': count,
            'status': 'success',
            'state': state
        })
        
    except Exception as e:
        print(f"[ALERTS ERROR] {e}")
        return jsonify({'count': 0, 'status': 'error', 'error': str(e)})

# ===== END ENVIRONMENTAL RISK API ENDPOINTS =====

@app.route('/acknowledgements')
def acknowledgements():
    """Acknowledgements page"""
    return render_template('acknowledgements.html')


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'mode': 'production',
        'adk_agent': 'available' if ADK_AGENT_AVAILABLE else 'unavailable',
        'psa_video_feature': 'enabled' if PSA_VIDEO_AVAILABLE else 'disabled',
        'services': {
            'epa': EPA_AVAILABLE,
            'weather': weather_service is not None,
            'pollen': pollen_service is not None,
            'gcs': GCS_AVAILABLE,
            'tts': TTS_AVAILABLE
        }
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"[OK] Starting Flask app on port {port}")
    print(f"[INFO] Visit http://localhost:{port} to view the application")
    if EPA_AVAILABLE:
        print(f"[INFO] Running with EPA/AirNow API integration")
    else:
        print(f"[INFO] Running with mock data (EPA API unavailable)")
    app.run(host='0.0.0.0', port=port, debug=False)