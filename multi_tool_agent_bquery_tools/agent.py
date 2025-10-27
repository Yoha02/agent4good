# ./agent.py
# -*- coding: utf-8 -*-
import os
import asyncio
import logging
from datetime import datetime
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Gemini API key - ADK uses GOOGLE_API_KEY
# Ensure GOOGLE_API_KEY is set for ADK framework
if not os.getenv('GOOGLE_API_KEY') and os.getenv('GEMINI_API_KEY'):
    os.environ['GOOGLE_API_KEY'] = os.getenv('GEMINI_API_KEY')
    print("[ADK] Using GEMINI_API_KEY as GOOGLE_API_KEY for ADK framework")

GEMINI_API_KEY = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print(f"[ADK] Gemini API configured with key: {GEMINI_API_KEY[:10]}...")
else:
    print("[WARNING] No API key found - ADK agent may not work properly")

# === Import all sub-agents and tools ===
from .agents.air_quality_agent import air_quality_agent
from .agents.live_air_quality_agent import live_air_quality_agent
from .agents.infectious_diseases_agent import infectious_diseases_agent
from .agents.clinic_finder_agent import clinic_finder_agent
from .agents.health_faq_agent import health_faq_agent
from .agents.psa_video import create_psa_video_agents
from .tools.health_tools import get_health_faq

# Import new crowdsourcing and health official agents
from .agents.crowdsourcing_agent import crowdsourcing_agent
from .agents.health_official_agent import health_official_agent
from .tools.embedding_tool import generate_report_embeddings

# Try to import analytics agent, use None if it fails
try:
    from .agents.analytics_agent import analytics_agent
except Exception as e:
    print(f"[WARNING] Analytics agent not available: {e}")
    analytics_agent = None

# === Model configuration ===
GEMINI_MODEL = "gemini-2.5-pro"

# === Create PSA Video Agents ===
psa_agents = create_psa_video_agents(model=GEMINI_MODEL, tools_module=None)

# === Persona Definitions ===
USER_PROMPT = (
    "You are a friendly and approachable **Community Health & Wellness Assistant**.\n\n"
    "Your goal is to help everyday citizens with their local health, environment, and wellness needs.\n\n"
    "Always start every new session by showing this clear and easy-to-read main menu:\n\n"
    "🩺 **Community Health Menu**\n"
    "1. 🌤️ **Live Air Quality** — Check current air quality via the AirNow API.\n"
    "2. 📊 **Historical Air Quality** — View past PM2.5 and AQI data from the EPA BigQuery database.\n"
    "3. 🦠 **Infectious Diseases** — Explore current county-level trends for foodborne and waterborne illnesses.\n"
    "4. 🏥 **Clinics & Doctors** — Find nearby clinics, urgent care, or specialists using Google Search.\n"
    "5. 📝 **Community Reports** — Submit health and environmental reports.\n"
    "6. ❓ **Health & Wellness FAQs** — Learn about hygiene, preventive care, and wellness practices.\n\n"
    
    "⚙️ **Routing Rules:**\n"
    "- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.\n"
    "- Historical queries (years, months, seasons) → air_quality_agent.\n"
    "- Mentions of infections, outbreaks, or diseases → infectious_diseases_agent.\n"
    "- Descriptions of symptoms or being unwell (e.g., 'I feel sick', 'I have a rash') → clinic_finder_agent.\n"
    "- Mentions of 'report', 'issue', 'problem', 'alert', or 'incident' → crowdsourcing_agent.\n"
    "- General questions on hygiene, health, or prevention → health_faq_agent.\n\n"
    
    "🧠 **Process Notes:**\n"
    "1️⃣ Always greet users warmly and show the menu at the start.\n"
    "2️⃣ Respond with clear, supportive explanations — sound like a helpful health advocate, not a scientist.\n"
    "3️⃣ For reports, collect key details (location, type, severity, description) and pass them to the crowdsourcing_agent.\n"
    "4️⃣ For clinic-related issues, find nearby care options.\n"
    "5️⃣ After each response, ask: 'Is there anything else I can help you with today?'"
)

HEALTH_OFFICIAL_PROMPT = (
    "You are an analytical and professional **Public Health Intelligence Assistant**, "
    "serving local and state health officials. You provide data-driven insights, trend analysis, "
    "and operational tools for community health management.\n\n"
    
    "When a health official logs in, immediately greet them as if they've entered their digital health console.\n\n"
    
    "👋 **Welcome, Health Official.**\n"
    "Here's your current operations dashboard:\n\n"
    
    "📊 **Health Operations Console**\n"
    "1. 🌤️ **Live Air Quality** — Monitor current air quality across the united states counties via the AirNow API.\n"
    "2. 📈 **Historical Air Quality** — Analyze PM2.5 and AQI trends from EPA BigQuery data.\n"
    "3. 🦠 **Infectious Disease Trends** — Retrieve and summarize county-level foodborne & waterborne illness data.\n"
    "4. 🏥 **Clinic Locator** — Identify nearby healthcare facilities for response coordination.\n"
    "5. 📝 **Crowdsourced Reports** — Review community-submitted health or environmental reports.\n"
    "6. 🔍 **Crowdsourced Insights Dashboard** — Perform semantic search & trend detection on community reports.\n"
    "7. 📊 **Cross-Dataset Analytics** — Statistical analysis across EPA and CDC datasets with code execution.\n"
    "8. 🎥 **PSA & Outreach Videos** — Generate public-service video prompts for awareness campaigns.\n\n"
    
    "💬 **Examples of what you can ask:**\n"
    "• 'Show community health reports for Alameda County.'\n"
    "• 'Summarize summer Salmonella trends in California.'\n"
    "• 'Generate embeddings for new reports.'\n"
    "• 'Create a PSA video on wildfire smoke safety.'\n"
    "• 'Compare last month's air quality in San Diego vs Los Angeles.'\n"
    "• 'Correlate air quality with disease rates in the Bay Area.'\n\n"
    
    "⚙️ **Routing Rules:**\n"
    "- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.\n"
    "- Historical data or trends → air_quality_agent.\n"
    "- 'infection', 'disease', 'pathogen', or 'case count' → infectious_diseases_agent.\n"
    "- 'report', 'crowdsourced', or 'incident' → crowdsourcing_agent.\n"
    "- 'dashboard', 'insight', 'semantic search', or 'trend detection' → health_official_agent.\n"
    "- 'generate embeddings', 'update vectors', or 'refresh semantic index' → run `generate_report_embeddings` tool.\n"
    "- 'cross-dataset', 'correlation', 'statistical analysis', 'complex analysis' → analytics_agent.\n"
    "- 'psa', 'video', or 'campaign' → PSA video agents.\n"
    "- 'clinic', 'hospital', or 'doctor' → clinic_finder_agent.\n"
    "- 'health advice', 'prevention', or 'faq' → health_faq_agent.\n\n"
    
    "🧠 **Behavior Guidelines:**\n"
    "1️⃣ Always greet with a professional, confident tone.\n"
    "2️⃣ Respond concisely and factually, emphasizing data and trends.\n"
    "3️⃣ For insights or reports, summarize key metrics — case counts, trends, and any anomalies.\n"
    "4️⃣ When asked to generate embeddings, execute the `generate_report_embeddings` tool and report results clearly.\n"
    "5️⃣ For statistical analysis, use analytics_agent for EPA/CDC data correlations.\n"
    "6️⃣ For community report patterns, use health_official_agent for semantic search.\n"
    "7️⃣ After each analytical response, ask: 'Would you like me to generate a visualization or PSA follow-up for this trend?'"
)

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

def create_root_agent_with_context(location_context=None, time_frame=None, persona_type=None):
    """Create the root agent with dynamic context including current time, location, time frame, and persona"""
    
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
    
    # Choose persona based on LOGIN_ROLE or parameter
    if persona_type is None:
        persona_type = os.getenv("LOGIN_ROLE", "user")

    if persona_type == "health_official":
        base_instruction = HEALTH_OFFICIAL_PROMPT
        logger.info(f"[ROOT AGENT] Creating agent with HEALTH_OFFICIAL persona")
    else:
        base_instruction = USER_PROMPT
        logger.info(f"[ROOT AGENT] Creating agent with USER persona")

    # Combine all context
    global_context = f"{time_context}{location_info}{time_frame_info}"
# Build complete sub_agents list
    sub_agents_list = [
        air_quality_agent,
        live_air_quality_agent,
        infectious_diseases_agent,
        clinic_finder_agent,
        health_faq_agent,
        crowdsourcing_agent,
        health_official_agent,
    ]

    # Add analytics_agent if available (KEEP from main)
    if analytics_agent:
        sub_agents_list.append(analytics_agent)
        logger.info(f"[ROOT AGENT] Added analytics_agent to sub-agents list")

    # Add PSA video agents
    sub_agents_list.extend(psa_agents)
    logger.info(f"[ROOT AGENT] Added {len(psa_agents)} PSA video agents to sub-agents list")
    logger.info(f"[ROOT AGENT] Total sub-agents: {len(sub_agents_list)}")

    return Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant that routes queries to specialized sub-agents.",
    global_instruction=global_context,
        instruction=base_instruction,
        tools=[generate_report_embeddings],
        sub_agents=sub_agents_list
    )

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
        logger.info(f"[ROOT AGENT] Initializing session service and runner")
        _session_service = InMemorySessionService()
        _session = asyncio.run(
            _session_service.create_session(
                app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
            )
        )
        _runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=_session_service)
        logger.info(f"[ROOT AGENT] Session and runner initialized successfully")

def call_agent(query: str, location_context=None, time_frame=None, persona=None) -> str:
    """Helper function to call the agent with a query and return the response."""
    global _runner
    
    # Initialize runner if not already done
    logger.info(f"[ROOT AGENT] Starting query processing: '{query[:100]}...'")
    logger.info(f"[ROOT AGENT] Context - Persona: {persona}, Location: {location_context}, TimeFrame: {time_frame}")
    
    _initialize_session_and_runner()
    
    # Determine effective persona (frontend > env var > default)
    effective_persona = persona if persona else os.getenv("LOGIN_ROLE", "user")
    
    # Map persona names to internal types
    persona_mapping = {
        "Health Official": "health_official",
        "Community Resident": "user",
        "health_official": "health_official",
        "user": "user"
    }
    persona_type = persona_mapping.get(effective_persona, "user")
    
    print(f"[AGENT] Using persona: {persona_type} (from: {effective_persona})")
    
    # Build context string and inject it into the query instead of creating new agent
    context_prefix = ""
    
    # Get time context
    time_context = get_current_time_context()
    
    # Build location context
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
        
        if location_parts:
            location_info = f"\n[LOCATION CONTEXT: {', '.join(location_parts)}]"
    
    # Build time frame context
    time_frame_info = ""
    if time_frame:
        time_frame_info = f"\n[TIME FRAME: {time_frame.get('start_date', '')} to {time_frame.get('end_date', '')}]"
    
    # Build persona context
    persona_info = ""
    if persona_type == "health_official":
        persona_info = "\n[USER ROLE: You are speaking with a Health Official who has access to semantic search, analytics, and PSA video generation tools]"
    else:
        persona_info = "\n[USER ROLE: You are speaking with a Community Resident who can report issues and get health information]"
    
    context_prefix = f"{time_context}{location_info}{time_frame_info}{persona_info}\n\nUser Question: "
    
    # Use the default runner with context injected into query
    enhanced_query = context_prefix + query if context_prefix else query
    content = types.Content(role="user", parts=[types.Part(text=enhanced_query)])
    logger.info(f"[ROOT AGENT] Enhanced query prepared, sending to runner")
    print(content)
    events = _runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

    for event in events:
        if event.is_final_response():
            logger.info(f"[ROOT AGENT] Received final response from sub-agent")
            return event.content.parts[0].text
    logger.warning("[ROOT AGENT] No response received from agent")
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
