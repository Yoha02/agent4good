from google.adk.agents import LlmAgent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import AgentTool

import multi_tool_agent_bquery_tools.agent

RESIDENT_PROMPT = """
You are a health advisor for people who are community resident,
You will follow instructions to provide wellness & health advise to people: 
1. Ask if user has any concerns or any symptoms. 
2. Ask their basic information, like Age, Location and so on
3. Answer user's concerns and provide health & wellness advises from the data provided via your tools
"""

HEALTH_OFFICIAL_PROMPT = """
 You are a health advisor for professional users who are public health official,
 1. Ask what they need 
 2. Use you tools to answer the their questions.
 ...
"""

def instruction_provider(context: ReadonlyContext) -> str:
    return HEALTH_OFFICIAL_PROMPT if "OFFICIAL".lower() == context.state["persona"].lower() else RESIDENT_PROMPT

health_data_agent = multi_tool_agent_bquery_tools.agent.root_agent

def before_agent(callback_context: CallbackContext):
    # runs at start of processing
    callback_context.state.setdefault("persona", "RESIDENT")

persona_aware_agent = LlmAgent(
    name="Personalized_advisor",
    model='gemini-2.5-flash',
    description="Health & Wellness Advisor based on persona",
    instruction= instruction_provider,
    before_agent_callback= before_agent, # This is for testing only, delete or comment out for
    # sub_agents=[health_data_agent]
    tools=[AgentTool(multi_tool_agent_bquery_tools.agent.air_quality_agent), AgentTool(multi_tool_agent_bquery_tools.agent.infectious_diseases_agent)]
)

