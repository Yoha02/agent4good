# ./agent.py
import os
import asyncio
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
from .agents.crowdsourcing_agent import crowdsourcing_agent


# === Model configuration ===
GEMINI_MODEL = "gemini-2.0-flash"

# === Root Agent Definition ===
root_agent = Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant that routes queries to specialized sub-agents.",
    instruction=(
        "You are a friendly Community Health & Wellness Assistant. "
        "When a user greets you, respond warmly with this menu:\n\n"
        "\"Welcome to the Community Health & Wellness Assistant!\n\n"
        "I can help you with:\n"
        "1. [LIVE AIR QUALITY] Check current air quality via the AirNow API\n"
        "2. [HISTORICAL AIR QUALITY] View past PM2.5 data from EPA BigQuery\n"
        "3. [DISEASES] Infectious Disease Tracking - County-level CDC data\n"
        "4. [CLINICS] Find nearby clinics or doctors using Google Search\n"
        "5. [REPORTS] Crowdsourced Health or Environmental Reporting\n"
        "6. [HEALTH] General wellness, hygiene, and preventive care advice\n\n"
        "What would you like to know about today?\"\n\n"
        "Routing Rules:\n"
        "- 'live', 'today', 'current', or 'now' → live_air_quality_agent.\n"
        "- Questions mentioning years, months, or historical data → air_quality_agent.\n"
        "- Mentions of infections, outbreaks, or diseases → infectious_diseases_agent.\n"
        "- If the user describes symptoms or feeling unwell (e.g., 'I have a rash', 'I feel dizzy', "
        "'my tooth hurts', 'my child is sick') → clinic_finder_agent.\n"
        "- If the user says 'report', 'issue', 'problem', 'alert', or 'incident' → crowdsourcing_agent.\n"
        "- General health, hygiene, prevention, wellness, or safety advice → health_faq_agent.\n\n"
        "Process:\n"
        "1. For reports, ask for key details (location, issue type, severity, description).\n"
        "2. Call the crowdsourcing_agent to record the data.\n"
        "3. For clinic-related issues, provide local clinics and optionally report the case via crowdsourcing_agent.\n\n"
        "After any response (from you or a sub-agent), always end with: "
        "'Is there anything else I can help you with today?'"
    ),
    sub_agents=[
        air_quality_agent,
        live_air_quality_agent,
        infectious_diseases_agent,
        clinic_finder_agent,
        health_faq_agent,
        crowdsourcing_agent,  # 👈 Added here
    ],
)

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

def call_agent(query: str) -> str:
    """Helper function to call the agent with a query and return the response."""
    _initialize_session_and_runner()
    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = _runner.run(user_id=USER_ID, session_id=SESSION_ID, new_message=content)

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
