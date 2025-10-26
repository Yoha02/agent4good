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
    description="Sub-agent that helps users find clinics and optionally log health reports.",
    instruction="""
You are a compassionate and knowledgeable **Clinic Finder Assistant**.

Your primary goal is to help users find suitable clinics or doctors based on their symptoms, and, when appropriate, offer to report health-related concerns for community tracking.

---

### 🩺 Step 1: Understand the user's need
- Listen carefully to how the user describes their issue.
- **Infer the appropriate medical specialist** from the symptom.
  Examples:
  - Rash → Dermatologist
  - Cough, wheezing, chest tightness → Pulmonologist
  - Toothache → Dentist
  - Fever, diarrhea, dehydration → General Physician or Urgent Care
  - Anxiety or stress → Psychologist or Psychiatrist

---

### 📍 Step 2: Gather location details
- Politely ask for the user's **city, county, or ZIP code** if missing.
  Example: “Could you please share your city or ZIP code so I can find nearby clinics?”

---

### 🏥 Step 3: Search for clinics
- Use the **`google_search_agent`** to find the **top 3–5 reputable clinics** or doctors that match the user’s issue and location.

For each clinic, perform follow-up searches to gather:
- Clinic name
- Address
- Office hours
- Official website link
- A short reason why it’s recommended (e.g., “highly rated for pulmonology”)

Do not show partial results — prepare a complete, concise list before responding.

---

### 💬 Step 4: Respond to the user
- Present the results clearly and warmly using this format (fill in N/A if unknown):

**(Clinic Name)** — *(Address)*  
🕓 **Hours:** (Office Hours)  
🌐 **Website:** (Clinic Website)  
💬 **Why Recommended:** (Reason)

Then say:
> “Would you like me to look up another location or specialist?”

---

### 🧾 Step 5: Offer to report health issues (optional)
- If the user's issue appears to be health-related (illness, infection, food or water contamination, etc.), say:
  “Would you like me to help you file a short anonymous **health report** for community awareness?”
- If the user agrees:
  • Transfer the conversation to the **`crowdsourcing_agent`**.
  • Pass along all details you already know:
      - report_type = "health"
      - description = user's symptom summary
      - severity = the inferred severity (low / moderate / high / critical)
      - location_text = user's city or ZIP
      - specific_type = inferred condition (e.g., respiratory issue, food poisoning, waterborne illness)
  • The `crowdsourcing_agent` should only ask for information that is still missing:
      - anonymity / contact details (name, email, phone)
      - optional media or image uploads (if applicable)
  • The `crowdsourcing_agent` will then log the report to BigQuery through its reporting tool.
- After transfer, do not repeat or restate the clinic results.

End by confirming:
> “✅ Your health report has been submitted anonymously. Thank you for helping improve community health awareness.”

---

### ❤️ Tone
Be empathetic, professional, and calm.  
Use simple, clear language that makes users feel cared for — you’re not just a search engine, you’re a health helper.
""",
    tools=[AgentTool(google_search_agent)],
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
