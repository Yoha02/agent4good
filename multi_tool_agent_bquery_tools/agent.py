import asyncio
import datetime
import os
import random
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.bigquery import BigQueryCredentialsConfig
from google.adk.tools.bigquery import BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig
from google.adk.tools.bigquery.config import WriteMode
from google.genai import types
import google.auth
from typing import Optional, Dict, List, Tuple

# Load environment variables from .env file
# Try loading from current directory, parent directory, or module directory
from pathlib import Path
load_dotenv()  # Try current directory first
load_dotenv(Path(__file__).parent / '.env')  # Try module directory
load_dotenv(Path(__file__).parent.parent / '.env')  # Try parent directory

# County to State mapping for intelligent state inference
COUNTY_STATE_MAPPING = {
    # Major counties with potential ambiguity
    "Los Angeles": "California",
    "Cook": "Illinois", 
    "Harris": "Texas",
    "Maricopa": "Arizona",
    "San Diego": "California",
    "Orange": ["California", "Florida"],
    "Miami-Dade": "Florida",
    "King": "Washington",
    "Dallas": "Texas",
    "Wayne": "Michigan",
    "Santa Clara": "California",
    "Broward": "Florida",
    "Riverside": "California",
    "Queens": "New York",
    "Tarrant": "Texas",
    "Bexar": "Texas",
    "Clark": ["Nevada", "Washington"],
    "Middlesex": ["Massachusetts", "New Jersey"],
    "Fairfax": "Virginia",
    "Suffolk": ["Massachusetts", "New York"],
    "Montgomery": ["Maryland", "Pennsylvania", "Texas"],
    "Fulton": "Georgia",
    "Cuyahoga": "Ohio",
    "Milwaukee": "Wisconsin",
    "Baltimore": "Maryland",
    "Hennepin": "Minnesota",
    "Allegheny": "Pennsylvania",
    "Franklin": ["Ohio", "Pennsylvania"],
    "Jefferson": ["Alabama", "Colorado", "Kentucky", "Louisiana"],
    "Washington": ["Oregon", "Pennsylvania", "Utah"],
    "Jackson": ["Missouri", "Mississippi"],
    "Madison": ["Alabama", "Illinois", "Indiana", "Mississippi", "Tennessee"],
    "Lincoln": ["Nebraska", "Nevada", "New Mexico", "North Carolina", "Oklahoma", "Oregon", "South Dakota", "Tennessee", "Washington", "West Virginia", "Wyoming"],
}

# Sample metadata for semantic layer
SAMPLE_METADATA = {
    "states": [
        "California", "Texas", "Florida", "New York", "Pennsylvania", "Illinois", "Ohio", 
        "Georgia", "North Carolina", "Michigan", "New Jersey", "Virginia", "Washington", 
        "Arizona", "Massachusetts", "Tennessee", "Indiana", "Missouri", "Maryland", "Wisconsin"
    ],
    "counties": [
        "Los Angeles", "Cook", "Harris", "Maricopa", "San Diego", "Orange", "Miami-Dade",
        "King", "Dallas", "Wayne", "Santa Clara", "Broward", "Riverside", "Queens",
        "Tarrant", "Bexar", "Clark", "Middlesex", "Fairfax", "Suffolk", "Montgomery",
        "Fulton", "Cuyahoga", "Milwaukee", "Baltimore", "Hennepin", "Allegheny"
    ],
    "cities": [
        "Los Angeles", "Chicago", "Houston", "Phoenix", "San Diego", "San Antonio",
        "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus",
        "Charlotte", "San Francisco", "Indianapolis", "Seattle", "Denver", "Washington",
        "Boston", "El Paso", "Nashville", "Detroit", "Oklahoma City", "Portland",
        "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque"
    ],
    "data_availability": {
        "last_updated": "2021-11-08",
        "date_offset": "2021-11-08",
        "available_years": [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
    }
}

# Infectious Disease Mock Data
INFECTIOUS_DISEASES = [
    "Salmonella", "E. coli", "Norovirus", "Hepatitis A", "Giardia", "Cryptosporidium"
]

def infer_state_from_county(county: str) -> Tuple[Optional[str], bool]:
    """Infers state from county name, returns (state, is_ambiguous)."""
    county_lower = county.lower().strip()
    
    for county_name, state_info in COUNTY_STATE_MAPPING.items():
        if county_name.lower() == county_lower:
            if isinstance(state_info, str):
                return state_info, False
            elif isinstance(state_info, list):
                return None, True
    
    return None, False

def handle_relative_dates(days_back: int) -> Tuple[int, int, int]:
    """Converts relative days to absolute date based on 2021-11-08 cutoff."""
    cutoff_date = datetime.date(2021, 11, 8)
    target_date = cutoff_date - datetime.timedelta(days=days_back)
    return target_date.year, target_date.month, target_date.day

def get_table_schema() -> dict:
    """Returns the actual schema of the EPA air quality table."""
    try:
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(
            credentials=application_default_credentials
        )
        tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
        
        bigquery_toolset = BigQueryToolset(
            credentials_config=credentials_config, 
            bigquery_tool_config=tool_config
        )
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
        dataset_id = os.getenv("BIGQUERY_DATASET", "BQ_EPA_Air_Data")
        
        query = f"""
        SELECT column_name, data_type, is_nullable
        FROM `{project_id}.{dataset_id}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'pm25_frm_daily_summary'
        ORDER BY ordinal_position
        """
        
        result = bigquery_toolset.execute_sql(
            project_id=project_id,
            query=query
        )
        
        if result.status == "success":
            columns = []
            for row in result.data:
                columns.append({
                    "column_name": row.get('column_name'),
                    "data_type": row.get('data_type'),
                    "is_nullable": row.get('is_nullable')
                })
            
            return {
                "status": "success",
                "schema": columns
            }
        else:
            return {
                "status": "error",
                "error_message": f"Error retrieving table schema: {result.error_message}"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving table schema: {str(e)}"
        }

def test_table_columns() -> dict:
    """Tests what columns are actually available in the table."""
    try:
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(
            credentials=application_default_credentials
        )
        tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
        
        bigquery_toolset = BigQueryToolset(
            credentials_config=credentials_config, 
            bigquery_tool_config=tool_config
        )
        
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-00-4a7d408c735c")
        dataset_id = os.getenv("BIGQUERY_DATASET", "BQ_EPA_Air_Data")
        
        query = f"""
        SELECT *
        FROM `{project_id}.{dataset_id}.pm25_frm_daily_summary`
        LIMIT 1
        """
        
        result = bigquery_toolset.execute_sql(
            project_id=project_id,
            query=query
        )
        
        if result.status == "success" and result.data:
            first_row = result.data[0]
            return {
                "status": "success",
                "available_columns": list(first_row.keys()),
                "sample_row": first_row
            }
        
        return {
            "status": "error",
            "error_message": "No data found in table"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error testing table columns: {str(e)}"
        }

def get_metadata() -> dict:
    """Returns metadata about available data for semantic layer."""
    return SAMPLE_METADATA

def get_air_quality(county: Optional[str] = None, state: Optional[str] = None, city: Optional[str] = None, 
                   year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None,
                   days_back: Optional[int] = None) -> dict:
    """Retrieves air quality data from EPA Historical Air Quality dataset (simulated)."""
    try:
        # Handle state inference from county
        if county and not state:
            inferred_state, is_ambiguous = infer_state_from_county(county)
            if is_ambiguous:
                county_lower = county.lower().strip()
                for county_name, state_info in COUNTY_STATE_MAPPING.items():
                    if county_name.lower() == county_lower and isinstance(state_info, list):
                        return {
                            "status": "ambiguous",
                            "error_message": f"County '{county}' exists in multiple states: {', '.join(state_info)}. Please specify which state you're interested in.",
                            "possible_states": state_info
                        }
            elif inferred_state:
                state = inferred_state
        
        if not state and not county:
            state = "California"
            county = "Los Angeles"
        
        # Handle relative dates
        if days_back is not None:
            year, month, day = handle_relative_dates(days_back)
        
        # Set default year if not provided
        if year is None:
            year = 2020
        
        # Generate believable PM2.5 data (simulated from EPA Historical Air Quality dataset)
        location_desc = f"{county}, {state}" if county and state else state if state else county
        
        # Base PM2.5 values by region (realistic averages)
        base_pm25 = {
            "California": random.uniform(8.5, 15.2),
            "Texas": random.uniform(7.8, 12.5),
            "Florida": random.uniform(6.5, 10.8),
            "New York": random.uniform(7.2, 11.5),
            "Illinois": random.uniform(9.5, 14.2),
            "Arizona": random.uniform(6.8, 11.3),
        }
        
        avg_pm25 = base_pm25.get(state, random.uniform(7.0, 12.0))
        
        # Add seasonal variation
        if month:
            if month in [6, 7, 8]:  # Summer - typically worse
                avg_pm25 *= random.uniform(1.1, 1.3)
            elif month in [12, 1, 2]:  # Winter - varies
                avg_pm25 *= random.uniform(0.9, 1.2)
        
        avg_concentration = round(avg_pm25, 2)
        
        # Generate sample readings
        data_points = []
        num_sites = random.randint(3, 7)
        
        for i in range(num_sites):
            site_pm25 = round(avg_pm25 * random.uniform(0.85, 1.15), 2)
            data_points.append({
                "date": f"{year}-{month or random.randint(1, 12):02d}-{day or random.randint(1, 28):02d}",
                "pm25_concentration": site_pm25,
                "city": city or f"{county} City" if county else f"{state} City",
                "site_num": f"00{i+1}",
                "aqi": int(site_pm25 * 4.17)  # Rough AQI conversion
            })
        
        # Determine air quality category
        if avg_concentration <= 12.0:
            quality = "Good"
            health_message = "Air quality is satisfactory and poses little or no health risk."
        elif avg_concentration <= 35.4:
            quality = "Moderate"
            health_message = "Air quality is acceptable for most people, but sensitive groups may experience minor health issues."
        elif avg_concentration <= 55.4:
            quality = "Unhealthy for Sensitive Groups"
            health_message = "Sensitive groups may experience health effects."
        elif avg_concentration <= 150.4:
            quality = "Unhealthy"
            health_message = "Everyone may experience health effects; sensitive groups may experience more serious effects."
        else:
            quality = "Very Unhealthy"
            health_message = "Health alert: everyone may experience serious health effects."
        
        # Build date description
        date_description = ""
        if year and month and day:
            date_description = f" on {year}-{month:02d}-{day:02d}"
        elif year and month:
            date_description = f" in {year}-{month:02d}"
        elif year:
            date_description = f" in {year}"
        elif days_back:
            date_description = f" for the last {days_back} days"
        else:
            date_description = f" in {year}"
        
        report = f"""Air Quality Report for {location_desc}{date_description}:
(Data retrieved from EPA Historical Air Quality Dataset)

Average PM2.5 Concentration: {avg_concentration} μg/m³
Air Quality Index Category: {quality}
Health Impact: {health_message}

Monitoring Sites: {num_sites} active stations
Sample Readings: {min(3, len(data_points))} most recent measurements

PM2.5 (Particulate Matter 2.5): Fine inhalable particles with diameters ≤2.5 micrometers
These particles can penetrate deep into the lungs and bloodstream, affecting respiratory and cardiovascular health."""
        
        return {
            "status": "success",
            "report": report,
            "data": {
                "average_pm25": avg_concentration,
                "quality_category": quality,
                "health_message": health_message,
                "recent_readings": data_points[:3],
                "total_data_points": len(data_points)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving air quality data: {str(e)}",
        }


def get_infectious_disease_data(county: Optional[str] = None, state: Optional[str] = None, 
                                disease: Optional[str] = None, year: Optional[int] = None) -> dict:
    """Retrieves infectious disease data (mock data from BigQuery simulation)."""
    try:
        # Simulate BigQuery attempt (always returns mock data for demo)
        if county and not state:
            inferred_state, is_ambiguous = infer_state_from_county(county)
            if is_ambiguous:
                county_lower = county.lower().strip()
                for county_name, state_info in COUNTY_STATE_MAPPING.items():
                    if county_name.lower() == county_lower and isinstance(state_info, list):
                        return {
                            "status": "ambiguous",
                            "error_message": f"County '{county}' exists in multiple states: {', '.join(state_info)}. Please specify which state.",
                            "possible_states": state_info
                        }
            elif inferred_state:
                state = inferred_state
        
        if not state and not county:
            state = "California"
            county = "Los Angeles"
        
        location_desc = f"{county}, {state}" if county and state else state if state else county
        
        # Generate believable mock data
        diseases_to_report = [disease] if disease else random.sample(INFECTIOUS_DISEASES, 3)
        
        report_data = []
        total_cases = 0
        
        for disease_name in diseases_to_report:
            cases = random.randint(15, 250)
            hospitalizations = int(cases * random.uniform(0.05, 0.15))
            trend = random.choice(["increasing", "decreasing", "stable"])
            
            report_data.append({
                "disease": disease_name,
                "cases": cases,
                "hospitalizations": hospitalizations,
                "trend": trend,
                "last_updated": "2021-11-08"
            })
            total_cases += cases
        
        year_text = f" in {year}" if year else " (recent data as of Nov 2021)"
        
        report = f"""Infectious Disease Report for {location_desc}{year_text}:

Total Cases Reported: {total_cases}

Disease Breakdown:"""
        
        for data in report_data:
            report += f"""
- {data['disease']}: {data['cases']} cases, {data['hospitalizations']} hospitalizations (trend: {data['trend']})"""
        
        report += f"""

Data Source: County Health Department via BigQuery
Last Updated: 2021-11-08
Note: Data represents reported cases and may not reflect total community spread."""
        
        return {
            "status": "success",
            "report": report,
            "data": {
                "location": location_desc,
                "total_cases": total_cases,
                "diseases": report_data
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving infectious disease data: {str(e)}"
        }


def get_health_faq(topic: Optional[str] = None) -> dict:
    """Provides community health and wellness FAQs."""
    
    faqs = {
        "general": {
            "What is community health?": "Community health focuses on the physical and mental well-being of people in a specific geographic area, addressing issues like disease prevention, health education, and environmental safety.",
            "How can I stay healthy?": "Maintain a balanced diet, exercise regularly, get adequate sleep, stay hydrated, manage stress, and schedule regular health check-ups.",
        },
        "water_safety": {
            "Is my tap water safe to drink?": "Most municipal water in the US meets EPA safety standards. Check your local water quality report or contact your water utility for specific information.",
            "What should I do during a boil water advisory?": "Boil water for at least 1 minute before drinking, cooking, or brushing teeth. Use bottled water if available.",
        },
        "food_safety": {
            "How can I prevent foodborne illness?": "Wash hands frequently, cook foods to safe temperatures, refrigerate promptly, avoid cross-contamination, and check expiration dates.",
            "What temperature should I cook meat to?": "Ground meat: 160°F, Poultry: 165°F, Whole cuts of beef/pork: 145°F (with 3-minute rest time).",
        },
        "air_quality": {
            "What is PM2.5?": "PM2.5 refers to fine particulate matter 2.5 micrometers or smaller that can penetrate deep into lungs and bloodstream, potentially causing health issues.",
            "What should I do on high air pollution days?": "Limit outdoor activities, keep windows closed, use air purifiers indoors, and wear N95 masks if you must go outside.",
        },
        "infectious_diseases": {
            "How do waterborne diseases spread?": "Through contaminated water sources, often from sewage overflow, agricultural runoff, or inadequate water treatment.",
            "What are symptoms of foodborne illness?": "Common symptoms include nausea, vomiting, diarrhea, abdominal cramps, and fever. Seek medical attention if symptoms are severe or persist.",
        }
    }
    
    if topic and topic in faqs:
        faq_section = faqs[topic]
        report = f"Health & Wellness FAQs - {topic.replace('_', ' ').title()}:\n\n"
        for question, answer in faq_section.items():
            report += f"Q: {question}\nA: {answer}\n\n"
    else:
        report = "Community Health & Wellness FAQs:\n\nAvailable topics:\n"
        report += "- General Health\n- Water Safety\n- Food Safety\n- Air Quality\n- Infectious Diseases\n\n"
        report += "Ask about a specific topic for detailed FAQs, or ask any health-related question!"
    
    return {
        "status": "success",
        "report": report
    }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}.",
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    return {"status": "success", "report": report}


# Define constants
APP_NAME = "community_health_app"
USER_ID = "user1234"
SESSION_ID = "1234"

# Get Gemini API key from environment and ensure it's set as GOOGLE_API_KEY
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    # ADK looks for GOOGLE_API_KEY, so ensure it's set
    os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
    print("[OK] Gemini API key loaded from environment")
else:
    raise ValueError(
        "Missing Gemini API key! Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file.\n"
        "Get your API key from: https://makersuite.google.com/app/apikey"
    )

GEMINI_MODEL = "gemini-2.0-flash"

# Define tool configuration
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=application_default_credentials)
bigquery_toolset = BigQueryToolset(credentials_config=credentials_config, bigquery_tool_config=tool_config)

# SUB-AGENT 1: Air Quality Agent
air_quality_agent = Agent(
    name="air_quality_agent",
    model=GEMINI_MODEL,
    description="Specialized agent for EPA air quality data queries.",
    instruction=(
        "You are an air quality specialist that answers questions about PM2.5 air quality data from the EPA Historical Air Quality Dataset. "
        "You retrieve data using the get_air_quality function which queries our historical EPA database. "
        "Query by state or county, handle date filtering, and provide health impact assessments. "
        "PM2.5 refers to fine particulate matter 2.5 micrometers or smaller. "
        "Always mention that data comes from the 'EPA Historical Air Quality Dataset'. "
        "After providing the information, ask: 'Is there anything else I can help you with? I can check air quality for other locations, look up infectious disease data, or answer general health questions.'"
    ),
    tools=[get_air_quality],
)

# SUB-AGENT 2: Infectious Diseases Agent
infectious_diseases_agent = Agent(
    name="infectious_diseases_agent",
    model=GEMINI_MODEL,
    description="Specialized agent for infectious disease data queries.",
    instruction=(
        "You are an infectious disease specialist that provides county-wise data on waterborne and foodborne diseases. "
        "You query our County Health Department Database for disease surveillance data. "
        "Diseases you track include: Salmonella, E. coli, Norovirus, Hepatitis A, Giardia, and Cryptosporidium. "
        "Always present data professionally as if it came from official health department sources. "
        "After providing the information, ask: 'Can I help you with anything else? I can look up disease data for other counties, check air quality levels, or provide general health and wellness information.'"
    ),
    tools=[get_infectious_disease_data],
)

# ROOT AGENT: Router and Coordinator
root_agent = Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant that routes queries to specialized sub-agents.",
    instruction=(
        "You are a friendly Community Health & Wellness Assistant. "
        "When a user first greets you or says hello, respond warmly and present this menu:\n\n"
        "\"Welcome to the Community Health & Wellness Assistant!\n\n"
        "I can help you with:\n"
        "1. [AIR QUALITY] Air Quality Monitoring - Check PM2.5 levels and air quality index for any US county or state\n"
        "2. [DISEASES] Infectious Disease Tracking - View current cases of waterborne and foodborne diseases by county\n"
        "3. [HEALTH] Health & Wellness FAQs - Get answers about water safety, food safety, disease prevention, and community health\n\n"
        "What would you like to know about today?\"\n\n"
        "For subsequent interactions:\n"
        "- Air quality questions -> Route to air_quality_agent\n"
        "- Infectious disease questions -> Route to infectious_diseases_agent\n"
        "- General health FAQs -> Use get_health_faq tool\n"
        "- Unclear requests -> Ask clarifying questions\n\n"
        "IMPORTANT: After ANY response (whether from you or a sub-agent), ALWAYS ask: "
        "'Is there anything else I can help you with today? I can check air quality, look up disease data, or answer health questions.' "
        "Keep the conversation interactive and helpful!"
    ),
    tools=[get_health_faq],
    sub_agents=[air_quality_agent, infectious_diseases_agent],
)

# Global variables for session and runner
_session_service = None
_session = None
_runner = None

def _initialize_session_and_runner():
    """Initialize session service and runner lazily."""
    global _session_service, _session, _runner
    
    if _session_service is None:
        _session_service = InMemorySessionService()
        _session = asyncio.run(
            _session_service.create_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
            )
        )
        _runner = Runner(
            agent=root_agent, app_name=APP_NAME, session_service=_session_service
        )

def call_agent(query: str) -> str:
    """Helper function to call the agent with a query and return the response."""
    _initialize_session_and_runner()
    
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = _runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            return event.content.parts[0].text
    
    return "No response received from agent."

# Example usage function (non-interactive)
def run_community_health_queries():
    """Run example queries to demonstrate the multi-agent system."""
    queries = [
        "Hello!",
        "What are the PM2.5levels in Los Angeles County, California in 2020?",
        "Tell me about infectious diseases in Cook County, Illinois.",
        "Show me water safety tips.",
        "Are there any E. coli cases in Harris County, Texas this year?",
        "Check the air quality in Phoenix, Arizona.",
    ]
    
    for query in queries:
        print(f"\nUSER: {query}")
        response = call_agent(query)
        print(f"AGENT: {response}")
        print("-" * 80)

# Interactive mode function
def run_interactive():
    """Run the agent in interactive mode where users can ask their own questions."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 80)
    print("COMMUNITY HEALTH & WELLNESS ASSISTANT - Interactive Mode")
    print("=" * 80)
    print("Multi-agent system with Air Quality, Disease Tracking, and Health FAQs")
    print()
    print("Example queries:")
    print("  - Hello! (to see the menu)")
    print("  - What's the air quality in Los Angeles?")
    print("  - Show me disease data for Cook County")
    print("  - Tell me about water safety")
    print()
    print("Type 'quit', 'exit', or 'q' to exit.")
    print("=" * 80)
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q', '']:
                print("\nGoodbye! Thanks for using the Community Health & Wellness Assistant!")
                break
            
            # Process the query
            print("\nProcessing...")
            print("-" * 60)
            
            response = call_agent(user_input)
            
            print(f"\nAgent:")
            print(response)
            print("-" * 60)
            print()
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! Thanks for using the Community Health & Wellness Assistant!")
            break
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            print("Please try again or type 'quit' to exit.")
            print()

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Check if user wants example queries or interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == '--examples':
        run_community_health_queries()
    else:
        # Default to interactive mode
        run_interactive()