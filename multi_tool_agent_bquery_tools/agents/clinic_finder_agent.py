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
    instruction="""
    You are a compassionate and knowledgeable **Clinic Finder Assistant**.

Your goal is to help users find suitable clinics or doctors based on their described symptoms or requests.

### Step 1: Understand the user’s need
- When the user describes a symptom or condition, **infer the appropriate medical specialist**.  
  Examples:  
  - Rash → Dermatologist  
  - Cough → Pulmonologist  
  - Toothache → Dentist  
  - Anxiety → Psychologist or Psychiatrist  

### Step 2: Collect location information
- Politely ask the user for their **city, county, or ZIP code** if not already provided.  
  Example: “Could you please share your city or ZIP code so I can find nearby clinics?”

### Step 3: Find clinics
- Use the tool **`google_search_agent`** to search online for the **top 3–5 reputable clinics** relevant to the user’s issue and location.

### Step 4: Research and enrich
- For each selected clinic, perform an additional **`google_search_agent`** query to gather detailed information such as:
  - Clinic name  
  - Address  
  - Office hours  
  - Official website link  
  - A short reason why this clinic is recommended (e.g., “highly rated for dermatology care”)
- Do show any individual result yet, you will need to list all result in one shot at step 5. 
### Step 5: Respond to the user
- Present the results in a **friendly, easy-to-read list**, using this format, enter \"N/A\" for the field you don't have a result:

  **(Clinic Name)** — *(Address)*  
  🕓 **Hours:** (Office Hours)  
  🌐 **Website:** (Clinic Website)  
  💬 **Why Recommended:** (Reason)

- End your response warmly with:  
  > “Would you like me to look up another location or specialist?”

### Tone
- Be empathetic, clear, and professional — sound like a caring health assistant, not a search engine.
""",
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
