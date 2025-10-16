#!/usr/bin/env python3
"""
Local demo of the agent without requiring Google Cloud authentication.
This provides a simulated experience of the agent's capabilities.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

# County to State mapping
COUNTY_STATE_MAPPING = {
    "Los Angeles": "California",
    "Cook": "Illinois", 
    "Harris": "Texas",
    "Maricopa": "Arizona",
    "San Diego": "California",
    "Orange": ["California", "Florida"],
    "Miami-Dade": "Florida",
    "King": "Washington",
    "Dallas": "Texas",
}

# Infectious Disease Mock Data
INFECTIOUS_DISEASES = [
    "Salmonella", "E. coli", "Norovirus", "Hepatitis A", "Giardia", "Cryptosporidium"
]

def get_air_quality_demo(county: Optional[str] = None, state: Optional[str] = None, 
                         year: Optional[int] = None) -> str:
    """Demo version of air quality data retrieval."""
    if not state and not county:
        state = "California"
        county = "Los Angeles"
    
    location_desc = f"{county}, {state}" if county and state else state if state else county
    year = year or 2020
    
    # Generate believable PM2.5 data
    base_pm25 = {
        "California": random.uniform(8.5, 15.2),
        "Texas": random.uniform(7.8, 12.5),
        "Florida": random.uniform(6.5, 10.8),
        "New York": random.uniform(7.2, 11.5),
        "Illinois": random.uniform(9.5, 14.2),
        "Arizona": random.uniform(6.8, 11.3),
    }
    
    avg_concentration = round(base_pm25.get(state, random.uniform(7.0, 12.0)), 2)
    
    # Determine air quality category
    if avg_concentration <= 12.0:
        quality = "Good"
        health_message = "Air quality is satisfactory and poses little or no health risk."
    elif avg_concentration <= 35.4:
        quality = "Moderate"
        health_message = "Air quality is acceptable for most people, but sensitive groups may experience minor health issues."
    else:
        quality = "Unhealthy for Sensitive Groups"
        health_message = "Sensitive groups may experience health effects."
    
    return f"""[AIR QUALITY] Air Quality Report for {location_desc} in {year}:
(Demo data - simulating EPA Historical Air Quality Dataset)

Average PM2.5 Concentration: {avg_concentration} ug/m3
Air Quality Index Category: {quality}
Health Impact: {health_message}

Monitoring Sites: {random.randint(3, 7)} active stations
PM2.5 (Particulate Matter 2.5): Fine inhalable particles with diameters <=2.5 micrometers

[INFO] These particles can penetrate deep into the lungs and bloodstream, affecting respiratory and cardiovascular health.
"""

def get_disease_data_demo(county: Optional[str] = None, state: Optional[str] = None,
                          disease: Optional[str] = None) -> str:
    """Demo version of infectious disease data."""
    if not state and not county:
        state = "California"
        county = "Los Angeles"
    
    location_desc = f"{county}, {state}" if county and state else state if state else county
    diseases_to_report = [disease] if disease else random.sample(INFECTIOUS_DISEASES, 3)
    
    report = f"""[DISEASES] Infectious Disease Report for {location_desc}:
(Demo data - simulating County Health Department Database)

Total Cases Reported: {sum([random.randint(15, 250) for _ in diseases_to_report])}

Disease Breakdown:"""
    
    for disease_name in diseases_to_report:
        cases = random.randint(15, 250)
        hospitalizations = int(cases * random.uniform(0.05, 0.15))
        trend = random.choice(["increasing", "decreasing", "stable"])
        report += f"\n  - {disease_name}: {cases} cases, {hospitalizations} hospitalizations (trend: {trend})"
    
    report += """

Data Source: County Health Department via BigQuery (Demo)
Last Updated: 2021-11-08
Note: This is demonstration data for testing purposes.
"""
    return report

def get_health_faq_demo(topic: Optional[str] = None) -> str:
    """Demo version of health FAQs."""
    faqs = {
        "water_safety": """[WATER SAFETY] FAQs:

Q: Is my tap water safe to drink?
A: Most municipal water in the US meets EPA safety standards. Check your local water quality report.

Q: What should I do during a boil water advisory?
A: Boil water for at least 1 minute before drinking, cooking, or brushing teeth.
""",
        "food_safety": """[FOOD SAFETY] FAQs:

Q: How can I prevent foodborne illness?
A: Wash hands frequently, cook foods to safe temperatures, refrigerate promptly, avoid cross-contamination.

Q: What temperature should I cook meat to?
A: Ground meat: 160F, Poultry: 165F, Whole cuts of beef/pork: 145F (with 3-minute rest).
""",
        "air_quality": """[AIR QUALITY] FAQs:

Q: What is PM2.5?
A: PM2.5 refers to fine particulate matter 2.5 micrometers or smaller that can penetrate deep into lungs.

Q: What should I do on high air pollution days?
A: Limit outdoor activities, keep windows closed, use air purifiers, wear N95 masks if needed.
""",
    }
    
    if topic and topic in faqs:
        return faqs[topic]
    else:
        return """[HEALTH] Community Health & Wellness FAQs:

Available topics:
  - water_safety - Water quality and safety tips
  - food_safety - Preventing foodborne illness
  - air_quality - Understanding air pollution

Ask about a specific topic or any health-related question!
"""

def process_query(query: str) -> str:
    """Process user queries and route to appropriate demo functions."""
    query_lower = query.lower()
    
    # Greeting
    if any(word in query_lower for word in ["hello", "hi", "hey", "greetings"]):
        return """Welcome to the Community Health & Wellness Assistant!

I can help you with:
1. [AIR QUALITY] Air Quality Monitoring - Check PM2.5 levels and air quality index for any US county or state
2. [DISEASES] Infectious Disease Tracking - View current cases of waterborne and foodborne diseases by county
3. [HEALTH] Health & Wellness FAQs - Get answers about water safety, food safety, disease prevention

What would you like to know about today?

[NOTE] This is a demo mode. For full functionality with real EPA data, 
authenticate with: gcloud auth application-default login
"""
    
    # Air quality queries
    elif any(word in query_lower for word in ["air quality", "pm2.5", "aqi", "pollution"]):
        # Extract location
        state = None
        county = None
        
        if "los angeles" in query_lower:
            county = "Los Angeles"
            state = "California"
        elif "california" in query_lower:
            state = "California"
        elif "cook county" in query_lower or "chicago" in query_lower:
            county = "Cook"
            state = "Illinois"
        elif "illinois" in query_lower:
            state = "Illinois"
        elif "texas" in query_lower or "harris" in query_lower:
            state = "Texas"
        elif "phoenix" in query_lower or "arizona" in query_lower:
            state = "Arizona"
        
        return get_air_quality_demo(county, state)
    
    # Disease queries
    elif any(word in query_lower for word in ["disease", "e. coli", "e.coli", "salmonella", "norovirus", "infection"]):
        state = None
        county = None
        disease = None
        
        if "cook county" in query_lower or "chicago" in query_lower:
            county = "Cook"
            state = "Illinois"
        elif "harris county" in query_lower or "houston" in query_lower:
            county = "Harris"
            state = "Texas"
        elif "los angeles" in query_lower:
            county = "Los Angeles"
            state = "California"
        
        if "e. coli" in query_lower or "e.coli" in query_lower:
            disease = "E. coli"
        elif "salmonella" in query_lower:
            disease = "Salmonella"
        
        return get_disease_data_demo(county, state, disease)
    
    # FAQ queries
    elif any(word in query_lower for word in ["water safety", "food safety", "faq", "tips", "prevent"]):
        if "water" in query_lower:
            return get_health_faq_demo("water_safety")
        elif "food" in query_lower:
            return get_health_faq_demo("food_safety")
        elif "air" in query_lower or "pollution" in query_lower:
            return get_health_faq_demo("air_quality")
        else:
            return get_health_faq_demo()
    
    else:
        return """I can help you with:
  • Air quality information (try: "What's the air quality in Los Angeles?")
  • Infectious disease tracking (try: "Show me disease data for Cook County")
  • Health & wellness tips (try: "Tell me about water safety")

What would you like to know?
"""

def main():
    """Run the interactive demo."""
    print("=" * 80)
    print("EPA AIR QUALITY AGENT - LOCAL DEMO MODE")
    print("=" * 80)
    print("Demo mode: Simulating agent capabilities without cloud authentication")
    print("\nType 'quit', 'exit', or 'q' to exit.")
    print("=" * 80)
    
    # Show welcome
    print("\n" + process_query("Hello"))
    
    while True:
        try:
            user_input = input("\nYour question: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q', '']:
                print("\nGoodbye! Thanks for using the EPA Air Quality Agent!")
                break
            
            print("\n" + process_query(user_input))
            print("-" * 80)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! Thanks for using the EPA Air Quality Agent!")
            break
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()

