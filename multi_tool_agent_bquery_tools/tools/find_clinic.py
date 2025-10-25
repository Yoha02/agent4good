# ./tools/clinic_finder_tool.py
from google.adk.tools import google_search
from typing import Optional

def find_clinic(problem: Optional[str] = None, location: Optional[str] = None):
    """
    Smart clinic finder that uses Gemini's built-in Google Search grounding.
    It forms a natural search query like 'dermatologist near Dublin, CA'.
    """
    # Step 1: Map some common health issues to likely specialists
    mapping = {
        "rash": "dermatologist",
        "skin": "dermatologist",
        "fever": "urgent care",
        "cold": "urgent care",
        "pain": "clinic",
        "tooth": "dentist",
        "eye": "optometrist",
        "child": "pediatrician",
        "chest": "hospital",
        "breath": "emergency room",
        "ear": "ENT specialist",
        "mental": "psychologist",
        "stress": "mental health counselor",
        "cut": "urgent care",
        "dizzy": "doctor",
        "burn": "burn center",
        "infection": "clinic",
    }

    specialty = None
    if problem:
        for k, v in mapping.items():
            if k in problem.lower():
                specialty = v
                break

    # Step 2: If no location, politely request it
    if not location:
        return "Please tell me your city, county, or ZIP code so I can find nearby clinics."

    # Step 3: Build the search query
    search_query = f"{specialty or problem or 'clinic'} near {location}"
    print(f"[Clinic Finder] Query → {search_query}")

    # Step 4: Use Google Search grounding
    return f"Search for: {search_query}"
