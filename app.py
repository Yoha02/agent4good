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

# Ensure API key is set before importing agent
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if GOOGLE_API_KEY:
    os.environ['GOOGLE_API_KEY'] = GOOGLE_API_KEY
    print(f"[OK] API key configured for agent")

# Import the ADK agent
try:
    from multi_tool_agent_bquery_tools.agent import call_agent as call_adk_agent
    ADK_AGENT_AVAILABLE = True
    print("[OK] ADK Agent loaded successfully!")
except Exception as e:
    print(f"[WARNING] ADK Agent not available: {e}")
    import traceback
    traceback.print_exc()
    ADK_AGENT_AVAILABLE = False

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
    
    def query_air_quality_data(self, state=None, days=7, start_date=None, end_date=None):
        """Query air quality data from YOUR BigQuery dataset"""
        if not self.bq_client:
            print("[BQ] No BigQuery client, using demo data")
            return self._generate_demo_data(state, days, start_date, end_date)
            
        try:
            # Use YOUR dataset: AirQualityData.Daily-AQI-County-2025
            project = os.getenv('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')
            
            # First, let's see what date range is available in the table
            # The table is called "Daily-AQI-County-2025" so it likely has 2025 data
            query = f"""
            SELECT 
                `Date Local` as date,
                `State Name` as state_name,
                `County Name` as county_name,
                CAST(AQI AS INT64) as aqi,
                'PM2.5' as parameter_name,
                'Monitoring Station' as site_name
            FROM `{project}.AirQualityData.Daily-AQI-County-2025`
            WHERE AQI IS NOT NULL
            """
            
            if state:
                query += f" AND UPPER(`State Name`) = UPPER('{state}')"
            
            # Add date filtering
            if start_date:
                query += f" AND Date_Local >= '{start_date}'"
            if end_date:
                query += f" AND Date_Local <= '{end_date}'"
            
            query += " ORDER BY Date_Local DESC LIMIT 100"
            
            print(f"[BQ] Querying YOUR dataset: AirQualityData.Daily-AQI-County-2025 for {state or 'all states'}")
            query_job = self.bq_client.query(query)
            results = query_job.result()
            
            data = [dict(row) for row in results]
            
            if data:
                # Show the date range we got
                dates = [d['date'] for d in data if 'date' in d]
                if dates:
                    print(f"[BQ] SUCCESS: Retrieved {len(data)} REAL records! Date range: {min(dates)} to {max(dates)}")
                else:
                    print(f"[BQ] SUCCESS: Retrieved {len(data)} REAL records from YOUR dataset!")
                return data
            else:
                print(f"[BQ] No data found, using demo data")
                return self._generate_demo_data(state, days, start_date, end_date)
                
        except Exception as e:
            print(f"[BQ ERROR] {e}")
            print("[BQ] Falling back to demo data")
            return self._generate_demo_data(state, days, start_date, end_date)
    
    def _generate_demo_data(self, state=None, days=7, start_date=None, end_date=None):
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
        
        # Determine date range for demo data
        if start_date and end_date:
            # Use provided date range
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            date_range = (end_dt - start_dt).days + 1
            print(f"[DEMO] Generating data for date range: {start_date} to {end_date} ({date_range} days)")
        else:
            # Use days parameter as fallback
            start_dt = datetime.now() - timedelta(days=days-1)
            end_dt = datetime.now()
            date_range = days
            print(f"[DEMO] Generating data for last {days} days")
        
        # Generate data for each day in the range
        for day_offset in range(min(date_range, 365)):  # Limit to 1 year max
            current_date = start_dt + timedelta(days=day_offset)
            
            for s in selected_states:
                if s in counties:
                    for county in counties[s][:2]:
                        data.append({
                            'date': current_date.strftime('%Y-%m-%d'),
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
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    data = agent.query_air_quality_data(state=state, days=days, start_date=start_date, end_date=end_date)
    stats = agent.get_statistics(data)
    
    return jsonify({
        'success': True,
        'data': data,
        'statistics': stats,
        'count': len(data),
        'date_range': {
            'start_date': start_date,
            'end_date': end_date
        }
    })


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint for AI analysis"""
    try:
        request_data = request.get_json()
        question = request_data.get('question', '')
        state = request_data.get('state', None)
        days = int(request_data.get('days', 7))
        start_date = request_data.get('start_date', None)
        end_date = request_data.get('end_date', None)
        
        # Get relevant data
        data = agent.query_air_quality_data(state=state, days=days, start_date=start_date, end_date=end_date)
        
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
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    data = agent.query_air_quality_data(state=state, days=1, start_date=start_date, end_date=end_date)
    
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
    """API endpoint for ADK agent chat - with async video generation support"""
    try:
        if not ADK_AGENT_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'ADK Agent not available. Using fallback AI.'
            }), 503
        
        request_data = request.get_json()
        question = request_data.get('question', '')
        location_context = request_data.get('location_context', None)
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'No question provided'
            }), 400
        
        # Add location context to the question if available
        if location_context:
            location_info = []
            if location_context.get('city'):
                location_info.append(f"City: {location_context['city']}")
            if location_context.get('state'):
                location_info.append(f"State: {location_context['state']}")
            if location_context.get('county'):
                location_info.append(f"County: {location_context['county']}")
            if location_context.get('zipCode'):
                location_info.append(f"ZIP Code: {location_context['zipCode']}")
            if location_context.get('formattedAddress'):
                location_info.append(f"Address: {location_context['formattedAddress']}")
            
            if location_info:
                location_text = " | ".join(location_info)
                enhanced_question = f"User Location Context: {location_text}\n\nUser Question: {question}"
                print(f"[CHAT] Enhanced question with location context: {enhanced_question}")
                question = enhanced_question
        
        # Check if user wants to generate PSA video
        video_keywords = ['create video', 'generate psa', 'make video', 'create psa', 'video psa', 'psa video']
        wants_video = any(keyword in question.lower() for keyword in video_keywords)
        
        print(f"[CHAT] Question: {question}")
        print(f"[CHAT] Wants video: {wants_video}")
        
        if wants_video:
            # Start async video generation
            try:
                from multi_tool_agent_bquery_tools.async_video_manager import get_video_manager
                from multi_tool_agent_bquery_tools.integrations.veo3_client import get_veo3_client
                from multi_tool_agent_bquery_tools.tools.video_gen import generate_action_line, create_veo_prompt
                
                # Get current state from request or default to California
                state = request_data.get('state', currentState if 'currentState' in locals() else 'California')
                
                # Get current health data
                health_data_list = agent.query_air_quality_data(state=state, days=1)
                
                if health_data_list:
                    df = pd.DataFrame(health_data_list)
                    avg_aqi = int(df['aqi'].mean()) if 'aqi' in df and not df['aqi'].empty else 50
                    
                    # Determine severity based on AQI
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
                    # Use demo data
                    avg_aqi = 75  # Moderate default
                    severity = "moderate"
                
                print(f"[CHAT] Air quality data: AQI {avg_aqi}, Severity: {severity}")
                
                health_data = {
                    'type': 'air_quality',
                    'severity': severity,
                    'metric': avg_aqi,
                    'location': state,
                    'specific_concern': 'PM2.5'
                }
                
                # Create task
                video_manager = get_video_manager()
                task_id = video_manager.create_task(location=state, data_type='air_quality')
                
                # Start background generation
                veo_client = get_veo3_client()
                video_manager.start_video_generation(
                    task_id=task_id,
                    health_data=health_data,
                    veo_client=veo_client,
                    action_line_func=generate_action_line,
                    veo_prompt_func=create_veo_prompt
                )
                
                # Return immediate response
                return jsonify({
                    'success': True,
                    'response': f"I'll generate a health alert video for {state}. This takes about 60 seconds.\n\nYou can continue chatting while I work on this. I'll notify you when it's ready!\n\nIs there anything else I can help you with?",
                    'task_id': task_id,
                    'estimated_time': 60,
                    'agent': 'ADK Multi-Agent System'
                })
                
            except Exception as video_error:
                print(f"[CHAT] Video generation error: {video_error}")
                import traceback
                traceback.print_exc()
                # Fall through to normal chat
        
        # Normal chat flow
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
            
            # Use the enhanced question (with location context) for fallback AI
            fallback_question = question  # This already has location context if available
            analysis = agent.analyze_with_ai(data, fallback_question)
            
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
@app.route('/api/generate-psa-video', methods=['POST'])
def generate_psa_video_endpoint():
    """Generate PSA video from current health data"""
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
    try:
        from multi_tool_agent_bquery_tools.async_video_manager import get_video_manager
        
        video_manager = get_video_manager()
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
        
        print(f"\n[FLASK] ===== Twitter Posting Request =====")
        print(f"[FLASK] Video URL: {video_url[:50]}...")
        print(f"[FLASK] Message: {message[:100]}...")
        print(f"[FLASK] Hashtags: {hashtags}")
        
        # Post to Twitter
        result = twitter_client.post_video_tweet(
            video_url=video_url,
            message=message,
            hashtags=hashtags
        )
        
        if result['status'] == 'success':
            print(f"[FLASK] SUCCESS: Tweet posted successfully!")
            print(f"[FLASK] URL: {result['tweet_url']}")
            
            return jsonify({
                'success': True,
                'tweet_url': result['tweet_url'],
                'tweet_id': result['tweet_id'],
                'message': result.get('message', 'Posted to Twitter successfully!')
            })
        else:
            print(f"[FLASK] ERROR: Tweet posting failed: {result.get('error_message')}")
            return jsonify({
                'success': False,
                'error': result.get('error_message', 'Unknown error')
            }), 500
        
    except Exception as e:
        print(f"[FLASK] ERROR: Twitter endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'adk_agent': 'available' if ADK_AGENT_AVAILABLE else 'unavailable',
        'psa_video_feature': 'enabled'
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
