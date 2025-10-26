import os
from google.adk.agents import Agent
from .analytics_prompts import return_instructions_analytics

# Import tools from other agents to get data
from ..tools.air_quality_tool import get_air_quality
from ..tools.live_air_quality_tool import get_live_air_quality
from ..tools.disease_tools import get_infectious_disease_data

GEMINI_MODEL = "gemini-2.0-flash"

# Try to use VertexAI code executor, fall back to None if not available
# (Agent will still work without code executor for basic data retrieval)
code_executor = None
try:
    # Check if running with Google AI Studio (no VertexAI needed)
    use_vertex_ai = os.getenv('GOOGLE_GENAI_USE_VERTEXAI', '').lower() == 'true'
    
    if use_vertex_ai:
        from google.adk.code_executors import VertexAiCodeExecutor
        code_executor = VertexAiCodeExecutor(
            optimize_data_file=True,
            stateful=True,
        )
        print("[OK] Analytics agent using VertexAI code executor")
    else:
        print("[INFO] Running with Google AI Studio - code executor disabled")
        print("[INFO] Analytics agent will work without code execution (data retrieval only)")
except Exception as e:
    print(f"[WARNING] VertexAI code executor not available: {e}")
    print("[INFO] Analytics agent will work without code execution (data retrieval only)")
    code_executor = None

analytics_agent = Agent(
    name="analytics_agent",
    model=GEMINI_MODEL,
    description="Analytics agent that performs cross-dataset analysis across air quality and disease data. Provides statistical analysis, correlations, and insights.",
    instruction=return_instructions_analytics(),
    code_executor=code_executor,
    tools=[get_air_quality, get_live_air_quality, get_infectious_disease_data],
)
