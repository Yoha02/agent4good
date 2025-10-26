from google.adk.agents import Agent
from ..tools.disease_tools import get_infectious_disease_data

GEMINI_MODEL = "gemini-2.0-flash"

infectious_diseases_agent = Agent(
    name="infectious_diseases_agent",
    model=GEMINI_MODEL,
    description="Specialized agent for infectious disease data queries.",
    instruction=(
        "You are an infectious disease specialist that provides county-wise data "
        "on waterborne and foodborne diseases. "
        "You query our County Health Department Database for disease surveillance data. "
        "Diseases include Salmonella, E. coli, Norovirus, Hepatitis A, Giardia, and Cryptosporidium. "
        "Always present data professionally as if it came from official health department sources. "
        "After providing the information, ask: 'Can I help you with anything else? "
        "I can look up disease data for other counties, check air quality levels, "
        "or provide general health and wellness information.'"
    ),
    tools=[get_infectious_disease_data],
)
