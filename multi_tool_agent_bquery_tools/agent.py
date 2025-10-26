# ./agent.py
# -*- coding: utf-8 -*-
import os
import asyncio
from datetime import datetime
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search

# === Import all sub-agents and tools ===
from .agents.air_quality_agent import air_quality_agent
from .agents.live_air_quality_agent import live_air_quality_agent
from .agents.infectious_diseases_agent import infectious_diseases_agent
from .agents.clinic_finder_agent import clinic_finder_agent
from .agents.health_faq_agent import health_faq_agent
from .agents.psa_video import create_psa_video_agents
from .tools.health_tools import get_health_faq

# Try to import analytics agent, use None if it fails
try:
    from .agents.analytics_agent import analytics_agent
except Exception as e:
    print(f"[WARNING] Analytics agent not available: {e}")
    analytics_agent = None

# === Model configuration ===
GEMINI_MODEL = "gemini-2.0-flash"

def get_current_time_context():
    """Generate current time context for the agent"""
    now = datetime.now()
    current_time = now.strftime("%A, %B %d, %Y at %I:%M %p")
    current_date = now.strftime("%Y-%m-%d")
    current_year = now.year
    
    return f"""
CURRENT TIME CONTEXT:
- Current Date & Time: {current_time}
- Current Date (ISO): {current_date}
- Current Year: {current_year}

IMPORTANT: Always reference the current time when providing health advice, especially for:
- Seasonal health recommendations
- Time-sensitive health alerts
- Current weather conditions affecting health
- Recent data trends and patterns
"""

def create_root_agent_with_context(location_context=None, time_frame=None):
    """Create the root agent with dynamic context including current time, location, and time frame"""
    
    # Get current time context
    time_context = get_current_time_context()
    
    # Build location context if provided
    location_info = ""
    if location_context:
        location_parts = []
        if location_context.get('city'):
            location_parts.append(f"City: {location_context['city']}")
        if location_context.get('state'):
            location_parts.append(f"State: {location_context['state']}")
        if location_context.get('county'):
            location_parts.append(f"County: {location_context['county']}")
        if location_context.get('zipCode'):
            location_parts.append(f"ZIP Code: {location_context['zipCode']}")
        if location_context.get('formattedAddress'):
            location_parts.append(f"Address: {location_context['formattedAddress']}")
        
        if location_parts:
            location_info = f"""
USER LOCATION CONTEXT:
- {', '.join(location_parts)}
- Coordinates: {location_context.get('coordinates', {}).get('lat', 'N/A')}, {location_context.get('coordinates', {}).get('lng', 'N/A')}
"""
    
    # Build time frame context if provided
    time_frame_info = ""
    if time_frame:
        time_frame_info = f"""
DATA TIME FRAME CONTEXT:
- Start Date: {time_frame.get('start_date', 'Not specified')}
- End Date: {time_frame.get('end_date', 'Not specified')}
- Analysis Period: {time_frame.get('period', 'Not specified')}
"""
    
    # Combine all context
    global_context = f"{time_context}{location_info}{time_frame_info}"
    
    return Agent(
        name="community_health_assistant",
        model=GEMINI_MODEL,
        description="Main community health assistant that routes queries to specialized sub-agents.",
        global_instruction=global_context,
        instruction=(
            "You are a friendly Community Health & Wellness Assistant. "
            "When a user greets you, respond warmly with this menu:\n\n"
            "\"Welcome to the Community Health & Wellness Assistant!\n\n"
            "I can help you with:\n"
            "1. [LIVE AIR QUALITY] Check current air quality via the AirNow API\n"
            "2. [HISTORICAL AIR QUALITY] View past PM2.5 data from EPA BigQuery\n"
            "3. [DISEASES] Infectious Disease Tracking - County-level CDC data\n"
            "4. [CLINICS] Find nearby clinics or doctors using Google Search\n"
            "5. [HEALTH] General wellness, hygiene, and preventive care advice\n"
            "6. [ANALYTICS] Cross-dataset analysis across air quality and disease data\n"
            "7. [PSA VIDEOS] Generate and share public health announcement videos\n\n"
            "What would you like to know about today?\"\n\n"
            "Routing Rules:\n"
            "- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.\n"
            "- Questions mentioning years, months, or historical data → air_quality_agent.\n"
            "- Mentions of infections, outbreaks, or diseases → infectious_diseases_agent.\n"
            "- If the user describes symptoms or feeling unwell "
            "(e.g., 'I have a rash', 'I feel dizzy', 'my tooth hurts', 'I cut my hand', "
            "'my child is sick'), route to clinic_finder_agent."
            "- General health, hygiene, prevention, wellness, or safety advice → health_faq_agent.\n"
            "- Analytical questions spanning multiple datasets, correlations, trends, or complex analysis → analytics_agent.\n"
            "- Requests to create PSA videos, announcements, or post to social media → PSA video agents.\n\n"
            "Process:\n"
            "1. If clinic_finder_agent provides a search phrase (e.g., 'dermatologist near San Jose'), "
            "use google_search with that phrase.\n"
            "2. Summarize the top 3–5 results clearly with clinic names and addresses.\n\n"
            "After any response (from you or a sub-agent), always end with: "
            "'Is there anything else I can help you with today?'"
        ),
        sub_agents=[
            air_quality_agent,
            live_air_quality_agent,
            infectious_diseases_agent,
            clinic_finder_agent,
            health_faq_agent,
        ] + ([analytics_agent] if analytics_agent else []) + psa_agents  # Add PSA video agents (ActionLine, VeoPrompt, Twitter)
    )

# === Create PSA Video Agents ===
psa_agents = create_psa_video_agents(model=GEMINI_MODEL, tools_module=None)

# === Default Root Agent (for backward compatibility) ===
root_agent = create_root_agent_with_context()

# === Runner & Session Setup ===
APP_NAME = "community_health_app"
USER_ID = "user1234"
SESSION_ID = "1234"

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
        _runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)

def call_agent(query: str, location_context=None, time_frame=None) -> str:
    """Helper function to call the agent with a query and return the response."""
    _initialize_session_and_runner()
    
    # Create agent with context if provided
    if location_context or time_frame:
        agent_with_context = create_root_agent_with_context(location_context, time_frame)
        # Create a new runner with the context-aware agent
        context_runner = Runner(agent=agent_with_context, app_name=APP_NAME, session_service=_session_service)
        runner_to_use = context_runner
    else:
        runner_to_use = _runner
    
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = runner_to_use.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            return event.content.parts[0].text
    return "No response received from agent."

# === Interactive Runner ===
def run_interactive():
    print("🌿 COMMUNITY HEALTH & WELLNESS ASSISTANT 🌿")
    print("Type 'quit' or 'exit' to leave.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Agent: Take care and stay healthy! 👋")
            break
        response = call_agent(user_input)
        print(f"Agent: {response}\n")

if __name__ == "__main__":
    run_interactive()
