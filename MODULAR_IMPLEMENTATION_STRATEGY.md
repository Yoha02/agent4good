# Modular Implementation Strategy - Veo 3 + Twitter Feature

## 🎯 Goal: Zero Conflicts with Team Development

**Challenge**: Multiple team members adding sub-agents to the same `agent.py` file  
**Solution**: Create separate modules that can be independently developed and imported

---

## 🏗️ Modular Architecture

### **New File Structure:**

```
multi_tool_agent_bquery_tools/
├── agent.py                    # CORE - minimal changes only
├── __init__.py                 # Main imports
│
├── agents/                     # NEW - Separate agent modules
│   ├── __init__.py
│   ├── air_quality.py         # Existing agent (extract from agent.py)
│   ├── disease.py             # Existing agent (extract from agent.py)
│   ├── psa_video.py           # NEW - Your feature
│   └── [teammate_feature].py  # For other team members
│
├── tools/                      # NEW - Function tools
│   ├── __init__.py
│   ├── health_data.py         # get_air_quality, get_disease_data
│   ├── video_gen.py           # NEW - Veo 3 functions
│   └── social_media.py        # NEW - Twitter functions
│
└── integrations/               # NEW - External APIs
    ├── __init__.py
    ├── veo3_client.py         # NEW - Veo 3 API wrapper
    └── twitter_client.py      # NEW - Twitter API wrapper
```

---

## 🔌 Plugin Pattern Implementation

### **Step 1: Create Agent Registry**

**File**: `multi_tool_agent_bquery_tools/agents/__init__.py`

```python
"""
Agent Registry - Automatically loads all available sub-agents
"""
from typing import List
from google.adk.agents import Agent

# Import existing agents
from .air_quality import create_air_quality_agent
from .disease import create_disease_agent

# Import new agents (optional - won't break if missing)
try:
    from .psa_video import create_psa_video_agents
    PSA_VIDEO_AVAILABLE = True
except ImportError:
    PSA_VIDEO_AVAILABLE = False

# Registry of all available agents
def get_all_sub_agents(model: str) -> List[Agent]:
    """Returns list of all available sub-agents"""
    agents = [
        create_air_quality_agent(model),
        create_disease_agent(model),
    ]
    
    # Add PSA video agents if available
    if PSA_VIDEO_AVAILABLE:
        agents.extend(create_psa_video_agents(model))
    
    return agents

def get_all_tools() -> List:
    """Returns list of all tools for root agent"""
    from ..tools.health_data import get_health_faq
    
    tools = [get_health_faq]
    
    # Add video tools if available
    if PSA_VIDEO_AVAILABLE:
        from ..tools.video_gen import generate_psa_video
        tools.append(generate_psa_video)
    
    return tools
```

### **Step 2: Extract Existing Agents**

**File**: `multi_tool_agent_bquery_tools/agents/air_quality.py`

```python
"""Air Quality Agent - Queries EPA data"""
from google.adk.agents import Agent
from ..tools.health_data import get_air_quality

def create_air_quality_agent(model: str) -> Agent:
    """Factory function to create air quality agent"""
    return Agent(
        name="air_quality_agent",
        model=model,
        description="Specialized agent for EPA air quality data queries.",
        instruction=(
            "You are an air quality specialist that answers questions about "
            "PM2.5 air quality data from the EPA Historical Air Quality Dataset..."
        ),
        tools=[get_air_quality],
    )
```

**File**: `multi_tool_agent_bquery_tools/agents/disease.py`

```python
"""Infectious Disease Agent - Queries CDC data"""
from google.adk.agents import Agent
from ..tools.health_data import get_infectious_disease_data

def create_disease_agent(model: str) -> Agent:
    """Factory function to create disease agent"""
    return Agent(
        name="infectious_diseases_agent",
        model=model,
        description="Specialized agent for infectious disease data queries.",
        instruction=(
            "You are an infectious disease specialist that provides "
            "county-wise data on waterborne and foodborne diseases..."
        ),
        tools=[get_infectious_disease_data],
    )
```

### **Step 3: Create Your PSA Video Module** (ISOLATED!)

**File**: `multi_tool_agent_bquery_tools/agents/psa_video.py`

```python
"""
PSA Video Generation Agents - Veo 3 + Twitter
This module is independent and won't conflict with other team features
"""
from google.adk.agents import Agent
from ..tools.video_gen import (
    generate_action_line,
    create_veo_prompt,
    generate_video
)
from ..tools.social_media import post_to_twitter

def create_psa_video_agents(model: str) -> list:
    """
    Factory function to create PSA video sub-agents.
    Returns list of agents that can be added to root agent.
    """
    
    # Agent 1: ActionLine Generator
    actionline_agent = Agent(
        name="actionline_agent",
        model=model,
        description="Converts health data into single actionable recommendation",
        instruction=(
            "You are ActionLine, a public-health recommendation writer. "
            "Read detailed health/environmental bulletins and output one short, "
            "plain-language action the public should take right now. "
            "Rules: "
            "- One sentence only, ≤12 words, imperative voice "
            "- Immediately doable (verb + object + condition) "
            "- Calm, non-alarmist, inclusive, specific "
            "- No numbers, stats, dates, agencies, disclaimers, emojis "
            "Examples: 'Wear a mask outside.' | 'Limit outdoor exertion.' | 'Close windows.'"
        ),
        tools=[generate_action_line],
    )
    
    # Agent 2: Veo Prompt Generator
    veo_prompt_agent = Agent(
        name="veo_prompt_agent",
        model=model,
        description="Creates Veo 3 prompts for 8-second health PSA videos",
        instruction=(
            "You are VeoPrompt, a prompt-engineer for Veo 3 video generation. "
            "Convert a single action line into a concise prompt for an 8-second, "
            "silent, vertical (1080×1920) video infographic. "
            "Visual: clean, flat vector, soft gradients, rounded shapes, high contrast. "
            "Layout: big icon center, green check/'do' or red caution/'avoid', "
            "single rounded banner at bottom with action text. "
            "Animation: 0-2s fade in, 2-6s demonstrate action, 6-8s hold with text."
        ),
        tools=[create_veo_prompt, generate_video],
    )
    
    # Agent 3: Twitter Poster
    twitter_agent = Agent(
        name="twitter_agent",
        model=model,
        description="Posts health PSA videos to Twitter/X with hashtags",
        instruction=(
            "You are a social media specialist for community health. "
            "Post PSA videos to Twitter/X with professional formatting. "
            "Always include: #PublicHealth #HealthAlert #CommunityWellness "
            "Add location-specific hashtags. Keep messages clear and actionable."
        ),
        tools=[post_to_twitter],
    )
    
    return [actionline_agent, veo_prompt_agent, twitter_agent]
```

### **Step 4: Update Main agent.py (MINIMAL CHANGES)**

**File**: `multi_tool_agent_bquery_tools/agent.py`

**Only change needed at the end:**

```python
# OLD CODE (lines 738-739):
# sub_agents=[air_quality_agent, infectious_diseases_agent],

# NEW CODE (minimal, modular):
from .agents import get_all_sub_agents, get_all_tools

root_agent = Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant that routes queries to specialized sub-agents.",
    instruction=(
        # ... existing instructions UNCHANGED ...
        # Automatically updates when new agents are added
    ),
    tools=get_all_tools(),
    sub_agents=get_all_sub_agents(GEMINI_MODEL),
)
```

**That's it!** Only 2 lines changed in the main file.

---

## 🎯 Benefits of This Approach

### **1. Zero Merge Conflicts:**
- Each team member works in their own `agents/[feature].py` file
- No editing the same lines in `agent.py`
- Registry automatically loads all available agents

### **2. Optional Features:**
- PSA video feature can be disabled by not importing the module
- Other features won't break if one fails to load
- Easy to enable/disable features via environment variables

### **3. Clean Testing:**
- Test your agents in isolation
- Mock external APIs easily
- Unit test each module separately

### **4. Easy Code Review:**
- Reviewers only look at your new files
- No confusion about what changed in shared files
- Clear ownership of code

### **5. Parallel Development:**
- You work on `agents/psa_video.py`
- Teammate works on `agents/their_feature.py`
- Both merge cleanly into main

---

## 📝 Implementation Priority

### **Your Files (Create These):**

**Priority 1** (Core Logic):
```
multi_tool_agent_bquery_tools/
├── agents/psa_video.py          # Your 3 agents
├── tools/video_gen.py           # Action line + Veo functions
└── tools/social_media.py        # Twitter functions
```

**Priority 2** (External Integrations):
```
multi_tool_agent_bquery_tools/
├── integrations/veo3_client.py  # Veo 3 API wrapper
└── integrations/twitter_client.py # Twitter API wrapper
```

**Priority 3** (Refactoring - Optional):
```
multi_tool_agent_bquery_tools/
├── agents/__init__.py           # Registry
├── agents/air_quality.py        # Extract existing
├── agents/disease.py            # Extract existing
└── tools/health_data.py         # Extract existing functions
```

---

## 🚀 Recommended Start

### **Option A: Full Modular (Best for Team)**
1. Create the `agents/`, `tools/`, `integrations/` structure
2. Extract existing agents into modules
3. Add your PSA video modules
4. Update main `agent.py` to use registry

### **Option B: Hybrid (Faster Start)**
1. Keep existing agents in `agent.py` as-is
2. Create only YOUR new modules:
   - `agents/psa_video.py`
   - `tools/video_gen.py`
   - `tools/social_media.py`
3. Add a simple import at end of `agent.py`:
   ```python
   # Add PSA video agents if available
   try:
       from .agents.psa_video import create_psa_video_agents
       psa_agents = create_psa_video_agents(GEMINI_MODEL)
       # Recreate root_agent with additional agents
   except ImportError:
       pass  # PSA feature not available
   ```

---

## 💡 **Recommendation**

**Start with Option B** (Hybrid):
- ✅ Faster to implement
- ✅ Your code is isolated in separate files
- ✅ Won't break existing functionality
- ✅ Easy to merge
- ✅ Can refactor to full modular later

**Then migrate to Option A** when team agrees on structure.

---

**Ready to start coding? Which option would you prefer?** 🚀

