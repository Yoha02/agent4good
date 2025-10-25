# ./agents/clinic_finder_agent.py
import random
from google.adk.agents import Agent

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

clinic_finder_agent = Agent(
    name="clinic_finder_agent",
    model=GEMINI_MODEL,
    description="Sub-agent that returns mock clinic results.",
    instruction=(
        "You are a compassionate Clinic Finder Assistant.\n\n"
        "When users describe a symptom or ask for a doctor, infer the type of specialist "
        "(e.g., rash → dermatologist, cough → pulmonologist, toothache → dentist). "
        "If they provide a location (city, county, or ZIP), pick 3-5 sample clinics from the pool "
        "or fabricate realistic names.\n"
        "For known test cities (Dublin CA, Brooklyn NY, San Jose CA) use the pre-defined examples.\n"
        "Otherwise invent reasonable clinic names.\n\n"
        "Format results as a friendly list and end with: "
        "'Would you like me to look up another location or specialist?'"
    ),
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
