from google.adk.agents import Agent
from ..tools.live_air_quality_tool import get_live_air_quality

GEMINI_MODEL = "gemini-2.0-flash"

live_air_quality_agent = Agent(
    name="live_air_quality_agent",
    model=GEMINI_MODEL,
    description="Sub-agent that retrieves current air quality (AQI) via the AirNow API.",
    instruction=(
        "You are a live air quality specialist that provides current AQI data using the U.S. EPA AirNow API. "
        "If the user mentions 'current', 'today', 'now', or 'live air quality', you should answer using this agent. "
        "Resolve cities/counties to coordinates if needed and return the latest AQI readings with pollutant categories. "
        "End by asking: 'Would you like to check historical trends or other locations as well?'"
    ),
    tools=[get_live_air_quality],
)
