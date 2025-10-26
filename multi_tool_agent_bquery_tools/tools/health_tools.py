import datetime
from zoneinfo import ZoneInfo
from ..tools.common_utils import infer_state_from_county, handle_relative_dates
from typing import Optional, Tuple, Dict, List



def get_health_faq(topic: Optional[str] = None) -> dict:
    """Provides community health and wellness FAQs."""
    
    faqs = {
        "general": {
            "What is community health?": "Community health focuses on the physical and mental well-being of people in a specific geographic area, addressing issues like disease prevention, health education, and environmental safety.",
            "How can I stay healthy?": "Maintain a balanced diet, exercise regularly, get adequate sleep, stay hydrated, manage stress, and schedule regular health check-ups.",
        },
        "water_safety": {
            "Is my tap water safe to drink?": "Most municipal water in the US meets EPA safety standards. Check your local water quality report or contact your water utility for specific information.",
            "What should I do during a boil water advisory?": "Boil water for at least 1 minute before drinking, cooking, or brushing teeth. Use bottled water if available.",
        },
        "food_safety": {
            "How can I prevent foodborne illness?": "Wash hands frequently, cook foods to safe temperatures, refrigerate promptly, avoid cross-contamination, and check expiration dates.",
            "What temperature should I cook meat to?": "Ground meat: 160°F, Poultry: 165°F, Whole cuts of beef/pork: 145°F (with 3-minute rest time).",
        },
        "air_quality": {
            "What is PM2.5?": "PM2.5 refers to fine particulate matter 2.5 micrometers or smaller that can penetrate deep into lungs and bloodstream, potentially causing health issues.",
            "What should I do on high air pollution days?": "Limit outdoor activities, keep windows closed, use air purifiers indoors, and wear N95 masks if you must go outside.",
        },
        "infectious_diseases": {
            "How do waterborne diseases spread?": "Through contaminated water sources, often from sewage overflow, agricultural runoff, or inadequate water treatment.",
            "What are symptoms of foodborne illness?": "Common symptoms include nausea, vomiting, diarrhea, abdominal cramps, and fever. Seek medical attention if symptoms are severe or persist.",
        }
    }
    
    if topic and topic in faqs:
        faq_section = faqs[topic]
        report = f"Health & Wellness FAQs - {topic.replace('_', ' ').title()}:\n\n"
        for question, answer in faq_section.items():
            report += f"Q: {question}\nA: {answer}\n\n"
    else:
        report = "Community Health & Wellness FAQs:\n\nAvailable topics:\n"
        report += "- General Health\n- Water Safety\n- Food Safety\n- Air Quality\n- Infectious Diseases\n\n"
        report += "Ask about a specific topic for detailed FAQs, or ask any health-related question!"
    
    return {
        "status": "success",
        "report": report
    }


def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    if city.lower() == "new york":
        tz_identifier = "America/New_York"
    else:
        return {
            "status": "error",
            "error_message": f"Sorry, I don't have timezone information for {city}.",
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    return {"status": "success", "report": report}

