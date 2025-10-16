import asyncio
import datetime
import os
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
load_dotenv()

# County to State mapping for intelligent state inference
COUNTY_STATE_MAPPING = {
    # Major counties with potential ambiguity
    "Los Angeles": "California",
    "Cook": "Illinois", 
    "Harris": "Texas",
    "Maricopa": "Arizona",
    "San Diego": "California",
    "Orange": ["California", "Florida"],  # Ambiguous - both CA and FL have Orange County
    "Miami-Dade": "Florida",
    "King": "Washington",
    "Dallas": "Texas",
    "Wayne": "Michigan",
    "Santa Clara": "California",
    "Broward": "Florida",
    "Riverside": "California",
    "Queens": "New York",
    "King": "Washington",
    "Tarrant": "Texas",
    "Bexar": "Texas",
    "Clark": ["Nevada", "Washington"],  # Ambiguous
    "Middlesex": ["Massachusetts", "New Jersey"],  # Ambiguous
    "Fairfax": "Virginia",
    "Suffolk": ["Massachusetts", "New York"],  # Ambiguous
    "Montgomery": ["Maryland", "Pennsylvania", "Texas"],  # Ambiguous
    "Fulton": "Georgia",
    "Cuyahoga": "Ohio",
    "Milwaukee": "Wisconsin",
    "Baltimore": "Maryland",
    "Hennepin": "Minnesota",
    "Allegheny": "Pennsylvania",
    "Franklin": ["Ohio", "Pennsylvania"],  # Ambiguous
    "Jefferson": ["Alabama", "Colorado", "Kentucky", "Louisiana"],  # Very ambiguous
    "Washington": ["Oregon", "Pennsylvania", "Utah"],  # Ambiguous
    "Jackson": ["Missouri", "Mississippi"],  # Ambiguous
    "Madison": ["Alabama", "Illinois", "Indiana", "Mississippi", "Tennessee"],  # Very ambiguous
    "Lincoln": ["Nebraska", "Nevada", "New Mexico", "North Carolina", "Oklahoma", "Oregon", "South Dakota", "Tennessee", "Washington", "West Virginia", "Wyoming"],  # Very ambiguous
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
        "date_offset": "2021-11-08",  # Use this as reference for "last X days"
        "available_years": [2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
    }
}

def infer_state_from_county(county: str) -> Tuple[Optional[str], bool]:
    """Infers state from county name, returns (state, is_ambiguous).
    
    Args:
        county (str): County name
        
    Returns:
        Tuple[Optional[str], bool]: (inferred_state, is_ambiguous)
    """
    county_lower = county.lower().strip()
    
    # Direct mapping
    for county_name, state_info in COUNTY_STATE_MAPPING.items():
        if county_name.lower() == county_lower:
            if isinstance(state_info, str):
                return state_info, False
            elif isinstance(state_info, list):
                return None, True  # Ambiguous
    
    return None, False

def handle_relative_dates(days_back: int) -> Tuple[int, int, int]:
    """Converts relative days to absolute date based on 2021-11-08 cutoff.

    Args:
        days_back (int): Number of days back from cutoff
        
    Returns:
        Tuple[int, int, int]: (year, month, day)
    """
    cutoff_date = datetime.date(2021, 11, 8)
    target_date = cutoff_date - datetime.timedelta(days=days_back)
    return target_date.year, target_date.month, target_date.day

def get_table_schema() -> dict:
    """Returns the actual schema of the EPA air quality table using ADK BigQuery tools.
    
    Returns:
        dict: Table schema information
    """
    try:
        # Initialize BigQuery toolset for schema query
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(
            credentials=application_default_credentials
        )
        tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
        
        bigquery_toolset = BigQueryToolset(
            credentials_config=credentials_config, 
            bigquery_tool_config=tool_config
        )
        
        # Query to get table schema using ADK tools
        query = """
        SELECT column_name, data_type, is_nullable
        FROM `bigquery-public-data.epa_historical_air_quality.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = 'pm25_frm_daily_summary'
        ORDER BY ordinal_position
        """
        
        # Use the execute_sql tool from the toolset
        result = bigquery_toolset.execute_sql(
            project_id="bigquery-public-data",
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
    """Tests what columns are actually available in the table using ADK BigQuery tools.
    
    Returns:
        dict: Available columns and sample data
    """
    try:
        # Initialize BigQuery toolset
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(
            credentials=application_default_credentials
        )
        tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
        
        bigquery_toolset = BigQueryToolset(
            credentials_config=credentials_config, 
            bigquery_tool_config=tool_config
        )
        
        # Simple query to get one row and see what columns exist
        query = """
        SELECT *
        FROM `bigquery-public-data.epa_historical_air_quality.pm25_frm_daily_summary`
        LIMIT 1
        """
        
        # Use the execute_sql tool from the toolset
        result = bigquery_toolset.execute_sql(
            project_id="bigquery-public-data",
            query=query
        )
        
        if result.status == "success" and result.data:
            # Get the first row and examine its structure
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
    """Returns metadata about available data for semantic layer.
    
    Returns:
        dict: Metadata about states, counties, cities, and data availability
    """
    return SAMPLE_METADATA

def get_air_quality(county: Optional[str] = None, state: Optional[str] = None, city: Optional[str] = None, 
                   year: Optional[int] = None, month: Optional[int] = None, day: Optional[int] = None,
                   days_back: Optional[int] = None) -> dict:
    """Retrieves air quality data from EPA's BigQuery dataset for a specific location and date.

    Args:
        county (str, optional): The name of the county (e.g., "Los Angeles")
        state (str, optional): The name of the state (e.g., "California") 
        city (str, optional): City name for more specific data
        year (int, optional): Year to filter data (e.g., 2023)
        month (int, optional): Month to filter data (1-12)
        day (int, optional): Day to filter data (1-31)
        days_back (int, optional): Number of days back from 2021-11-08 (data cutoff)

    Returns:
        dict: status and result or error msg with air quality data.
    """
    try:
        # Handle state inference from county if state not provided
        if county and not state:
            inferred_state, is_ambiguous = infer_state_from_county(county)
            if is_ambiguous:
                # Get all possible states for this county
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
            else:
                return {
                    "status": "error", 
                    "error_message": f"Could not infer state for county '{county}'. Please specify the state."
                }
        
        # Validate that we have either state or county
        if not state and not county:
            return {
                "status": "error",
                "error_message": "Please provide either a state or county name."
            }
        
        # Handle relative dates (days_back)
        if days_back is not None:
            year, month, day = handle_relative_dates(days_back)
        
        # Initialize BigQuery toolset
        application_default_credentials, _ = google.auth.default()
        credentials_config = BigQueryCredentialsConfig(
            credentials=application_default_credentials
        )
        tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)
        
        bigquery_toolset = BigQueryToolset(
            credentials_config=credentials_config, 
            bigquery_tool_config=tool_config
        )
        
        # Build the WHERE clause based on available parameters
        where_conditions = []
        
        if state:
            where_conditions.append(f"state_name = '{state}'")
        if county:
            where_conditions.append(f"county_name = '{county}'")
        if city:
            where_conditions.append(f"city_name = '{city}'")
        
        # Add date filtering if year, month, or day are provided
        if year is not None:
            if month is not None:
                if day is not None:
                    # Specific date
                    where_conditions.append(f"date_local = DATE({year}, {month}, {day})")
                else:
                    # Specific year and month
                    where_conditions.append(f"EXTRACT(YEAR FROM date_local) = {year}")
                    where_conditions.append(f"EXTRACT(MONTH FROM date_local) = {month}")
            else:
                # Specific year only
                where_conditions.append(f"EXTRACT(YEAR FROM date_local) = {year}")
        elif month is not None:
            # Specific month only (current year)
            where_conditions.append(f"EXTRACT(MONTH FROM date_local) = {month}")
        
        where_clause = " AND ".join(where_conditions)
        
        # Query the EPA air quality dataset
        query = f"""
        SELECT 
            date_local,
            arithmetic_mean,
            state_name,
            county_name,
            city_name,
            site_num,
            latitude,
            longitude,
            address,
            local_site_name,
            aqi
        FROM 
            `bigquery-public-data.epa_historical_air_quality.pm25_frm_daily_summary`
        WHERE 
            {where_clause}
            AND arithmetic_mean IS NOT NULL
        ORDER BY 
            date_local DESC
        LIMIT 100
        """
        
        # Execute the query using ADK tools
        result = bigquery_toolset.execute_sql(
            project_id="bigquery-public-data",
            query=query
        )
        
        if result.status != "success":
            return {
                "status": "error",
                "error_message": f"Error executing query: {result.error_message}"
            }
        
        results = result.data
        
        # Process results
        data_points = []
        total_concentration = 0
        count = 0
        
        for row_dict in results:
            # Get PM2.5 concentration value
            pm25_value = row_dict.get('arithmetic_mean')
            
            if pm25_value is not None:
                data_points.append({
                    "date": str(row_dict.get('date_local', '')),
                    "pm25_concentration": round(float(pm25_value), 2),
                    "city": row_dict.get('city_name'),
                    "site_num": row_dict.get('site_num'),
                    "latitude": row_dict.get('latitude'),
                    "longitude": row_dict.get('longitude'),
                    "address": row_dict.get('address'),
                    "site_name": row_dict.get('local_site_name'),
                    "aqi": row_dict.get('aqi')
                })
                total_concentration += float(pm25_value)
            count += 1
        
        if count == 0:
            date_filter = ""
            if year is not None and month is not None and day is not None:
                date_filter = f" on {year}-{month:02d}-{day:02d}"
            elif year is not None and month is not None:
                date_filter = f" in {year}-{month:02d}"
            elif year is not None:
                date_filter = f" in {year}"
            elif month is not None:
                date_filter = f" in month {month}"
            elif days_back is not None:
                date_filter = f" for the last {days_back} days (from 2021-11-08)"
            
            location_desc = ""
            if county and state:
                location_desc = f"{county}, {state}"
            elif county:
                location_desc = f"{county} County"
            elif state:
                location_desc = f"{state}"
            
            return {
                "status": "error",
                "error_message": f"No air quality data found for {location_desc}" + (f" (City: {city})" if city else "") + date_filter,
            }
        
        # Calculate average PM2.5 concentration
        avg_concentration = round(total_concentration / count, 2)
        
        # Determine air quality category based on EPA standards
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
        
        # Build date description for the report
        date_description = ""
        if year is not None and month is not None and day is not None:
            date_description = f" on {year}-{month:02d}-{day:02d}"
        elif year is not None and month is not None:
            date_description = f" in {year}-{month:02d}"
        elif year is not None:
            date_description = f" in {year}"
        elif month is not None:
            date_description = f" in month {month}"
        elif days_back is not None:
            date_description = f" for the last {days_back} days (from 2021-11-08)"
        else:
            date_description = " (all available data)"
        
        # Build location description
        location_desc = ""
        if county and state:
            location_desc = f"{county}, {state}"
        elif county:
            location_desc = f"{county} County"
        elif state:
            location_desc = f"{state}"
        
        report = f"""Air Quality Report for {location_desc}{' (City: ' + city + ')' if city else ''}{date_description}:

Average PM2.5 Concentration: {avg_concentration} μg/m³
Air Quality Index Category: {quality}
Health Impact: {health_message}

Data points: {min(5, len(data_points))} most recent readings
Data available from: {len(data_points)} monitoring sites
Monitoring locations: {', '.join(set([dp['city'] for dp in data_points[:5] if dp['city']]))}"""
        
        return {
            "status": "success",
            "report": report,
            "data": {
                "average_pm25": avg_concentration,
                "quality_category": quality,
                "health_message": health_message,
                "recent_readings": data_points[:5],
                "total_data_points": len(data_points)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Error retrieving air quality data: {str(e)}",
        }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city.

    Args:
        city (str): The name of the city for which to retrieve the current time.

    Returns:
        dict: status and result or error msg.
    """

    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


# Define constants for this example agent
AGENT_NAME = "epa_air_quality_agent"
APP_NAME = "epa_air_quality_app"
USER_ID = "user1234"
SESSION_ID = "1234"

# Get Gemini API key from environment and ensure it's set as GOOGLE_API_KEY
GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

if GEMINI_API_KEY:
    # ADK looks for GOOGLE_API_KEY, so ensure it's set
    os.environ['GOOGLE_API_KEY'] = GEMINI_API_KEY
    print(f"✅ Gemini API key loaded from environment")
    GEMINI_MODEL = "gemini-2.0-flash"
else:
    print("⚠️ WARNING: No Gemini API key found. Set GOOGLE_API_KEY or GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-2.0-flash"

# Define a tool configuration to block any write operations
tool_config = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)

# Define a credentials config - using application default credentials
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# Instantiate a BigQuery toolset
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, 
    bigquery_tool_config=tool_config
)

# Agent Definition with API key
if GEMINI_API_KEY:
    # Use Gemini API with API key - ADK will pick it up from GOOGLE_API_KEY env var
    root_agent = Agent(
        name=AGENT_NAME,
        model=GEMINI_MODEL,
        description=(
            "Intelligent agent for EPA air quality data queries using BigQuery ADK tools with flexible location and date filtering, state inference, and semantic metadata support."
        ),
        instruction=(
            "You are an intelligent air quality agent that can answer questions about air quality data from EPA's BigQuery dataset using ADK BigQuery tools. "
            "You have access to the BigQueryToolset which includes: list_dataset_ids, get_dataset_info, list_table_ids, get_table_info, execute_sql, forecast, and ask_data_insights. "
            "The main dataset is 'bigquery-public-data.epa_historical_air_quality' and the table is 'pm25_frm_daily_summary'. "
            "You can query by state OR county - if only a county is provided, you'll intelligently infer the state. "
            "If a county exists in multiple states, you'll ask the user to clarify. "
            "You support flexible date queries including specific dates, months, years, or relative dates like 'last 10 days' (calculated from 2021-11-08 data cutoff). "
            "You can also provide metadata about available states, counties, cities, and data availability to help users understand what data is available. "
            "The air quality data includes PM2.5 concentrations with health impact assessments based on EPA standards, along with monitoring site information and AQI values. "
            "Use the BigQuery tools to execute SQL queries, get table information, and provide data insights."
        ),
        tools=[bigquery_toolset, get_air_quality, get_current_time, get_metadata, get_table_schema, test_table_columns],
    )
else:
    raise ValueError(
        "Missing Gemini API key! Please set GOOGLE_API_KEY or GEMINI_API_KEY environment variable.\n"
        "Get your API key from: https://makersuite.google.com/app/apikey\n"
        "Then set it in your .env file: GOOGLE_API_KEY=your-key-here"
    )

# Global variables for session and runner (initialized lazily)
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
    """
    Helper function to call the agent with a query and return the response.
    
    Args:
        query (str): The user's question or request
        
    Returns:
        str: The agent's response
    """
    # Initialize session and runner if not already done
    _initialize_session_and_runner()
    
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = _runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            return event.content.parts[0].text
    
    return "No response received from agent."

# Example usage function
def run_epa_air_quality_queries():
    """Run example queries to demonstrate the EPA air quality agent capabilities."""
    queries = [
        "What datasets are available in the bigquery-public-data project?",
        "Tell me about the epa_historical_air_quality dataset.",
        "What tables are available in the epa_historical_air_quality dataset?",
        "Get information about the pm25_frm_daily_summary table.",
        "What are the PM2.5 levels in Los Angeles County, California in 2020?",
        "Show me the air quality data for Cook County, Illinois for the last 30 days from the data cutoff.",
        "What is the average PM2.5 concentration in Texas in 2019?"
    ]
    
    for query in queries:
        print(f"\nUSER: {query}")
        response = call_agent(query)
        print(f"AGENT: {response}")
        print("-" * 80)
