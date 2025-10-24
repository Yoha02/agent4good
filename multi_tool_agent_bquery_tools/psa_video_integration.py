"""
PSA Video Feature Integration Point
This file integrates PSA video agents into the main system
Teammates can create similar integration files for their features
"""
from typing import List, Optional
from google.adk.agents import Agent


def integrate_psa_video_feature(existing_sub_agents: List[Agent], model: str) -> tuple:
    """
    Integrates PSA video agents into the multi-agent system.
    Returns (updated_sub_agents, additional_tools, success_flag)
    
    This function is OPTIONAL - if it fails, the main system continues working
    
    Args:
        existing_sub_agents: Current list of sub-agents
        model: Gemini model name
    
    Returns:
        tuple: (new_sub_agents_list, additional_tools_list, was_successful)
    """
    try:
        from .agents.psa_video import create_psa_video_agents
        from .tools.video_gen import generate_action_line, create_veo_prompt
        from .tools.social_media import post_to_twitter, format_health_tweet
        
        # Create PSA video agents
        psa_agents = create_psa_video_agents(model, tools_module=None)
        
        # Add to existing agents
        updated_agents = existing_sub_agents + psa_agents
        
        # Additional tools for root agent
        additional_tools = [
            generate_action_line,
            create_veo_prompt,
            post_to_twitter,
            format_health_tweet
        ]
        
        print("[PSA_VIDEO] [OK] PSA Video feature loaded successfully")
        print(f"[PSA_VIDEO] Added {len(psa_agents)} agents: ActionLine, VeoPrompt, Twitter")
        
        return (updated_agents, additional_tools, True)
        
    except Exception as e:
        print(f"[PSA_VIDEO] Feature not available: {e}")
        print("[PSA_VIDEO] Continuing without PSA video capabilities")
        return (existing_sub_agents, [], False)


def get_psa_video_instructions() -> str:
    """
    Returns additional instructions for root agent about PSA video feature.
    Can be appended to existing root agent instructions.
    """
    return """

NEW CAPABILITY - PSA Video Generation:
When user asks to 'create a video PSA' or 'generate health alert video':
1. Gather current health data (air quality OR disease data for the location)
2. Route to actionline_agent to get a single action recommendation
3. Route to veo_prompt_agent to create video generation prompt
4. Use video generation tools to create 8-second PSA video
5. Return video preview URL for user validation
6. If user approves, route to twitter_agent to post to social media

Example user requests:
- "Create a PSA video about air quality in California"
- "Generate a health alert video for the current situation"
- "Make a video warning about the disease outbreak"
"""


# Feature flag
PSA_VIDEO_FEATURE_ENABLED = True  # Set to False to disable

