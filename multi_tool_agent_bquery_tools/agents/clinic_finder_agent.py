# ./agents/clinic_finder_agent.py
import random
from google.adk.agents import Agent
from google.adk.tools import google_search, AgentTool

GEMINI_MODEL = "gemini-2.0-flash"

# --- small fake data pool ---
CLINIC_DATA = {
    "dublin": [
        "California Skin Institute – 4000 Dublin Blvd, Dublin, CA",
        "Tri-Valley Urgent Care – 7450 San Ramon Rd, Dublin, CA",
        "Sutter Health Clinic – Dublin Center, Dublin, CA",
    ],
    "brooklyn": [
        "Brooklyn Hospital Center – 121 DeKalb Ave, Brooklyn, NY",
        "CityMD Urgent Care – Atlantic Ave, Brooklyn, NY",
        "NewYork-Presbyterian Brooklyn Methodist Hospital – Park Slope, Brooklyn, NY",
    ],
    "san jose": [
        "Kaiser Permanente San Jose Medical Center – 250 Hospital Pkwy, San Jose, CA",
        "Good Samaritan Hospital – 2425 Samaritan Dr, San Jose, CA",
        "Valley Health Center Downtown – 777 E Santa Clara St, San Jose, CA",
    ],
}

def _mock_results(location: str):
    loc = location.lower().strip()
    if loc in CLINIC_DATA:
        return CLINIC_DATA[loc]
    # fabricate
    fake_names = [
        "Community Wellness Clinic",
        "Downtown Family Health Center",
        "CarePlus Urgent Care",
        "Neighborhood Medical Group",
        "Healthy Life Clinic",
    ]
    return [f"{random.choice(fake_names)} – {location.title()}"]

google_search_agent= Agent(
    name="google_search_agent",
    model=GEMINI_MODEL,
    description="Agent to answer questions using Google Search.",
    instruction="You are agent that can search user query from Internet via tool 'google-search.",
    tools=[google_search]
)

clinic_finder_agent = Agent(
    name="clinic_finder_agent",
    model=GEMINI_MODEL,
    description="Sub-agent that returns mock clinic results.",
    instruction=(
        "You are a compassionate Clinic Finder Assistant.\n\n"
        "When users describe a symptom or ask for a doctor, infer the type of specialist "
        "(e.g., rash → dermatologist, cough → pulmonologist, toothache → dentist). "
        "Ask them to provide location info (city, county, or ZIP)"
        "Use tool 'google_search_agent' to search online for top 3-5 clinics which can help on user's issue"
        "List the recommended clinic with reason, for example, this clinic is close, it's 24 hours, it has specialist for the symptom and so on  "
        # "pick 3-5 sample clinics from the pool "
        # "or fabricate realistic names.\n"
        # "For known test cities (Dublin CA, Brooklyn NY, San Jose CA) use the pre-defined examples.\n"
        # "Otherwise invent reasonable clinic names.\n\n"
        "Format results as a friendly list and end with: "
        "'Would you like me to look up another location or specialist?'"
    ),
    tools=[AgentTool(google_search_agent)]
)

# simple helper the model can call internally
def find_mock_clinics(problem: str = None, location: str = None) -> str:
    problem = (problem or "health issue").lower()
    location = location or "your area"
    results = _mock_results(location)
    lines = [f"- {r}" for r in results]
    header = f"Here are some clinics that can help with {problem} in {location.title()}:\n"
    return header + "\n".join(lines) + \
        "\n\nWould you like me to look up another location or specialist?"
