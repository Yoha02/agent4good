# Unified Feature Plan: Merging Main + Recovered Branch

## 🎯 Goal
Create a **unified system** that combines ALL features from both branches without losing anything.

---

## 📊 Complete Feature Inventory

### Current Main Branch Features

| # | Agent/Feature | Purpose | Status | Action |
|---|--------------|---------|--------|--------|
| 1 | `air_quality_agent` | Historical EPA air quality data | ✅ Active | ✅ **KEEP** |
| 2 | `live_air_quality_agent` | Real-time AirNow API data | ✅ Active | ✅ **KEEP** |
| 3 | `infectious_diseases_agent` | CDC disease tracking | ✅ Active | ✅ **KEEP + ENHANCE** prompt |
| 4 | `clinic_finder_agent` | Find nearby clinics | ✅ Active | ✅ **KEEP + ENHANCE** prompt |
| 5 | `health_faq_agent` | General health Q&A | ✅ Active | ✅ **KEEP** |
| 6 | **`analytics_agent`** | Cross-dataset analysis, code execution | ✅ Active | ✅ **KEEP** (not in recovered) |
| 7 | PSA video agents | Video generation with Veo 3 | ✅ Active | ✅ **KEEP** |
| 8 | `get_current_time_context()` | Time-aware responses | ✅ Active | ✅ **KEEP** |
| 9 | `create_root_agent_with_context()` | Dynamic context injection | ✅ Active | ✅ **KEEP + ENHANCE** |
| 10 | `call_agent()` with context | Location/time context | ✅ Active | ✅ **KEEP** |
| 11 | BigQuery fixes | Standard client vs ADK toolset | ✅ Active | ✅ **KEEP** |
| 12 | Twitter integration | Post PSA videos | ✅ Active | ✅ **KEEP** |
| 13 | `app_local.py` | Primary Flask app | ✅ Active | ✅ **KEEP** |

**Total Main Features: 13**

---

### Recovered Branch New Features

| # | Agent/Feature | Purpose | Status | Action |
|---|--------------|---------|--------|--------|
| 14 | `crowdsourcing_agent` | Community report submission | 🆕 New | ✅ **ADD** |
| 15 | `health_official_agent` | Semantic search & analytics | 🆕 New | ✅ **ADD** |
| 16 | `crowdsourcing_tool.py` | BigQuery insert + GCS upload | 🆕 New | ✅ **ADD** |
| 17 | `embedding_tool.py` | Generate embeddings | 🆕 New | ✅ **ADD** |
| 18 | `semantic_query_tool.py` | Vector similarity search | 🆕 New | ✅ **ADD** |
| 19 | User persona prompt | Citizen-friendly interface | 🆕 New | ✅ **ADD** |
| 20 | Health official persona prompt | Professional dashboard | 🆕 New | ✅ **ADD** |
| 21 | `LOGIN_ROLE` env var | Persona switching | 🆕 New | ✅ **ADD** |

**Total New Features: 8**

---

## 🚨 CRITICAL: What Recovered Branch DELETED

| Feature | Status in Main | Status in Recovered | Risk | Action |
|---------|---------------|---------------------|------|--------|
| **`analytics_agent`** | ✅ Exists | ❌ **DELETED** | 🔴 **HIGH** | ✅ **MUST KEEP** |
| `analytics_prompts.py` | ✅ Exists | ❌ **DELETED** | 🔴 **HIGH** | ✅ **MUST KEEP** |
| Context injection logic | ✅ Exists | ❌ **REMOVED** | 🔴 **HIGH** | ✅ **MUST KEEP** |
| `app_local.py` | ✅ Exists | ❌ **DELETED** | 🔴 **CRITICAL** | ✅ **MUST KEEP** |
| BigQuery fixes | ✅ Exists | ❌ **REVERTED** | 🔴 **HIGH** | ✅ **MUST KEEP** |

---

## 🎯 Unified Architecture

### Complete Agent List (Main + Recovered)

```python
# All agents that will be registered in the unified system:

ROOT_AGENT
├── air_quality_agent              # Historical EPA data
├── live_air_quality_agent         # Real-time AirNow API
├── infectious_diseases_agent      # CDC disease tracking (enhanced prompt)
├── clinic_finder_agent            # Clinic locator (enhanced prompt)
├── health_faq_agent               # General health Q&A
├── analytics_agent                # Cross-dataset analysis (KEEP from main)
├── crowdsourcing_agent            # Community reports (NEW from recovered)
├── health_official_agent          # Semantic search (NEW from recovered)
└── PSA Video Agents               # Video generation
    ├── psa_video_script_agent
    ├── psa_video_generation_agent
    └── psa_video_posting_agent
```

**Total: 12 agents (13 if you count PSA suite separately)**

---

## 🧩 Agent Purpose & Interaction Matrix

### Agent Responsibilities (No Overlap)

| Agent | Primary Purpose | Data Sources | Unique Features |
|-------|----------------|--------------|----------------|
| **analytics_agent** | Statistical analysis across EPA + CDC data | EPA BigQuery + CDC BigQuery | Code execution, correlations, trends |
| **health_official_agent** | Semantic search on community reports | Crowdsourced reports (embedding DB) | Vector search, pattern detection |

**Key Point:** These agents serve **DIFFERENT** purposes:
- `analytics_agent` → Analyzes **official government data** (EPA, CDC)
- `health_official_agent` → Analyzes **community-submitted reports** (crowdsourced)

**Decision:** ✅ **KEEP BOTH** - They complement each other!

---

## 📋 Unified Feature Map

### For Regular Users (User Persona)

```
🩺 Community Health Menu
1. 🌤️ Live Air Quality          → live_air_quality_agent
2. 📊 Historical Air Quality     → air_quality_agent
3. 🦠 Infectious Diseases        → infectious_diseases_agent
4. 🏥 Clinics & Doctors          → clinic_finder_agent
5. 📝 Community Reports          → crowdsourcing_agent (NEW)
6. ❓ Health & Wellness FAQs     → health_faq_agent
```

### For Health Officials (Health Official Persona)

```
📊 Health Operations Console
1. 🌤️ Live Air Quality                      → live_air_quality_agent
2. 📈 Historical Air Quality                 → air_quality_agent
3. 🦠 Infectious Disease Trends              → infectious_diseases_agent
4. 🏥 Clinic Locator                         → clinic_finder_agent
5. 📝 Crowdsourced Reports                   → crowdsourcing_agent (NEW)
6. 🔍 Crowdsourced Insights Dashboard        → health_official_agent (NEW)
7. 📊 Cross-Dataset Analytics                → analytics_agent (KEEP)
8. 🎥 PSA & Outreach Videos                  → PSA video agents
```

**Key Difference:**
- Users: 6 features (simplified)
- Officials: 8 features (full access including analytics)

---

## 🔧 Implementation Strategy

### Phase 1: Add New Files (5 files)
✅ No conflicts, pure additions:
1. `multi_tool_agent_bquery_tools/agents/crowdsourcing_agent.py`
2. `multi_tool_agent_bquery_tools/agents/health_official_agent.py`
3. `multi_tool_agent_bquery_tools/tools/crowdsourcing_tool.py`
4. `multi_tool_agent_bquery_tools/tools/embedding_tool.py`
5. `multi_tool_agent_bquery_tools/tools/semantic_query_tool.py`

### Phase 2: Update `agent.py` with Unified System

#### Step 2.1: Keep ALL Existing Imports
```python
# === Import all sub-agents and tools ===
from .agents.air_quality_agent import air_quality_agent
from .agents.live_air_quality_agent import live_air_quality_agent
from .agents.infectious_diseases_agent import infectious_diseases_agent
from .agents.clinic_finder_agent import clinic_finder_agent
from .agents.health_faq_agent import health_faq_agent
from .agents.psa_video import create_psa_video_agents
from .tools.health_tools import get_health_faq

# NEW: Add crowdsourcing imports
from .agents.crowdsourcing_agent import crowdsourcing_agent
from .agents.health_official_agent import health_official_agent
from .tools.embedding_tool import generate_report_embeddings

# KEEP: Analytics agent (not in recovered branch)
try:
    from .agents.analytics_agent import analytics_agent
except Exception as e:
    print(f"[WARNING] Analytics agent not available: {e}")
    analytics_agent = None
```

#### Step 2.2: Add Persona Prompts
```python
# === Persona Definitions ===
USER_PROMPT = """
You are a friendly and approachable **Community Health & Wellness Assistant**.

Your goal is to help everyday citizens with their local health, environment, and wellness needs.

Always start every new session by showing this clear and easy-to-read main menu:

🩺 **Community Health Menu**
1. 🌤️ **Live Air Quality** — Check current air quality via the AirNow API.
2. 📊 **Historical Air Quality** — View past PM2.5 and AQI data from the EPA BigQuery database.
3. 🦠 **Infectious Diseases** — Explore current county-level trends for foodborne and waterborne illnesses.
4. 🏥 **Clinics & Doctors** — Find nearby clinics, urgent care, or specialists using Google Search.
5. 📝 **Community Reports** — Submit health and environmental reports.
6. ❓ **Health & Wellness FAQs** — Learn about hygiene, preventive care, and wellness practices.

⚙️ **Routing Rules:**
- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.
- Historical queries (years, months, seasons) → air_quality_agent.
- Mentions of infections, outbreaks, or diseases → infectious_diseases_agent.
- Descriptions of symptoms or being unwell (e.g., 'I feel sick', 'I have a rash') → clinic_finder_agent.
- Mentions of 'report', 'issue', 'problem', 'alert', or 'incident' → crowdsourcing_agent.
- General questions on hygiene, health, or prevention → health_faq_agent.

🧠 **Process Notes:**
1️⃣ Always greet users warmly and show the menu at the start.
2️⃣ Respond with clear, supportive explanations — sound like a helpful health advocate, not a scientist.
3️⃣ For reports, collect key details (location, type, severity, description) and pass them to the crowdsourcing_agent.
4️⃣ For clinic-related issues, find nearby care options.
5️⃣ After each response, ask: 'Is there anything else I can help you with today?'
"""

HEALTH_OFFICIAL_PROMPT = """
You are an analytical and professional **Public Health Intelligence Assistant**, 
serving local and state health officials. You provide data-driven insights, trend analysis, 
and operational tools for community health management.

When a health official logs in, immediately greet them as if they've entered their digital health console.

👋 **Welcome, Health Official.**
Here's your current operations dashboard:

📊 **Health Operations Console**
1. 🌤️ **Live Air Quality** — Monitor current air quality across California counties via the AirNow API.
2. 📈 **Historical Air Quality** — Analyze PM2.5 and AQI trends from EPA BigQuery data.
3. 🦠 **Infectious Disease Trends** — Retrieve and summarize county-level foodborne & waterborne illness data.
4. 🏥 **Clinic Locator** — Identify nearby healthcare facilities for response coordination.
5. 📝 **Crowdsourced Reports** — Review community-submitted health or environmental reports.
6. 🔍 **Crowdsourced Insights Dashboard** — Perform semantic search & trend detection on community reports.
7. 📊 **Cross-Dataset Analytics** — Statistical analysis across EPA and CDC datasets with code execution.
8. 🎥 **PSA & Outreach Videos** — Generate public-service video prompts for awareness campaigns.

⚙️ **Routing Rules:**
- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.
- Historical data or trends → air_quality_agent.
- 'infection', 'disease', 'pathogen', or 'case count' → infectious_diseases_agent.
- 'report', 'crowdsourced', or 'incident' → crowdsourcing_agent.
- 'dashboard', 'insight', 'semantic search', or 'trend detection' → health_official_agent.
- 'generate embeddings', 'update vectors', or 'refresh semantic index' → run `generate_report_embeddings` tool.
- 'cross-dataset', 'correlation', 'statistical analysis', 'complex analysis' → analytics_agent.
- 'psa', 'video', or 'campaign' → PSA video agents.
- 'clinic', 'hospital', or 'doctor' → clinic_finder_agent.
- 'health advice', 'prevention', or 'faq' → health_faq_agent.

🧠 **Behavior Guidelines:**
1️⃣ Always greet with a professional, confident tone.
2️⃣ Respond concisely and factually, emphasizing data and trends.
3️⃣ For insights or reports, summarize key metrics — case counts, trends, and any anomalies.
4️⃣ When asked to generate embeddings, execute the `generate_report_embeddings` tool and report results clearly.
5️⃣ For statistical analysis, use analytics_agent for EPA/CDC data correlations.
6️⃣ For community report patterns, use health_official_agent for semantic search.
7️⃣ After each analytical response, ask: 'Would you like me to generate a visualization or PSA follow-up for this trend?'
"""
```

#### Step 2.3: Update `create_root_agent_with_context()` Function
```python
def create_root_agent_with_context(location_context=None, time_frame=None, persona_type=None):
    """Create the root agent with dynamic context including current time, location, time frame, and persona"""
    
    # KEEP: Get current time context
    time_context = get_current_time_context()
    
    # KEEP: Build location context if provided
    location_info = ""
    if location_context:
        location_parts = []
        if location_context.get('city'):
            location_parts.append(f"City: {location_context['city']}")
        if location_context.get('state'):
            location_parts.append(f"State: {location_context['state']}")
        if location_context.get('county'):
            location_parts.append(f"County: {location_context['county']}")
        if location_context.get('zipCode'):
            location_parts.append(f"ZIP Code: {location_context['zipCode']}")
        if location_context.get('formattedAddress'):
            location_parts.append(f"Address: {location_context['formattedAddress']}")
        
        if location_parts:
            location_info = f"""
USER LOCATION CONTEXT:
- {', '.join(location_parts)}
- Coordinates: {location_context.get('coordinates', {}).get('lat', 'N/A')}, {location_context.get('coordinates', {}).get('lng', 'N/A')}
"""
    
    # KEEP: Build time frame context if provided
    time_frame_info = ""
    if time_frame:
        time_frame_info = f"""
DATA TIME FRAME CONTEXT:
- Start Date: {time_frame.get('start_date', 'Not specified')}
- End Date: {time_frame.get('end_date', 'Not specified')}
- Analysis Period: {time_frame.get('period', 'Not specified')}
"""
    
    # NEW: Choose persona based on LOGIN_ROLE or parameter
    if persona_type is None:
        persona_type = os.getenv("LOGIN_ROLE", "user")
    
    if persona_type == "health_official":
        base_instruction = HEALTH_OFFICIAL_PROMPT
    else:
        base_instruction = USER_PROMPT
    
    # Combine all context
    global_context = f"{time_context}{location_info}{time_frame_info}"
    
    # NEW: Build complete sub_agents list
    sub_agents_list = [
        air_quality_agent,
        live_air_quality_agent,
        infectious_diseases_agent,
        clinic_finder_agent,
        health_faq_agent,
        crowdsourcing_agent,        # NEW
        health_official_agent,       # NEW
    ]
    
    # Add analytics_agent if available (KEEP from main)
    if analytics_agent:
        sub_agents_list.append(analytics_agent)
    
    # Add PSA video agents
    sub_agents_list.extend(psa_agents)
    
    return Agent(
        name="community_health_assistant",
        model=GEMINI_MODEL,
        description="Main community health assistant that routes queries to specialized sub-agents.",
        global_instruction=global_context,  # KEEP: Context injection
        instruction=base_instruction,        # NEW: Persona-based instruction
        tools=[generate_report_embeddings],  # NEW: Embedding tool
        sub_agents=sub_agents_list           # UNIFIED: All agents
    )
```

### Phase 3: Update Agent Prompts (2 files)
1. `clinic_finder_agent.py` - Enhanced prompt from recovered
2. `infectious_diseases_agent.py` - Enhanced prompt from recovered + model change

### Phase 4: Environment Variables
Add to `.env` and Cloud Run:
```bash
LOGIN_ROLE=user  # or "health_official"
```

### Phase 5: Update Documentation
- Document both personas
- Document analytics_agent vs health_official_agent differences
- Update deployment guide

---

## 🧪 Testing Matrix

### Test Existing Features (Must Work)
- [ ] Air quality queries (live & historical) with context injection
- [ ] Disease tracking with current year context
- [ ] Clinic finder
- [ ] Health FAQ
- [ ] **Analytics agent** - Cross-dataset EPA/CDC analysis
- [ ] PSA video generation
- [ ] Twitter posting
- [ ] Location context injection
- [ ] Time context injection
- [ ] Time frame context injection

### Test New Features (Must Work)
- [ ] Community report submission
- [ ] Report semantic search
- [ ] Embedding generation
- [ ] User persona display
- [ ] Health official persona display
- [ ] Persona switching via LOGIN_ROLE

### Test Agent Interactions (Must Work)
- [ ] User persona routes correctly to all agents
- [ ] Health official persona routes correctly to all agents
- [ ] Analytics agent available in health official persona
- [ ] Analytics agent hidden in user persona (optional)
- [ ] Both analytics_agent and health_official_agent coexist
- [ ] No routing conflicts between agents

---

## 📊 Final Agent Count

| Category | Count | Agents |
|----------|-------|--------|
| **Core Health** | 5 | air_quality, live_air_quality, diseases, clinic_finder, health_faq |
| **Analytics** | 2 | analytics_agent (EPA/CDC), health_official_agent (community reports) |
| **Community** | 1 | crowdsourcing_agent |
| **Outreach** | 3 | PSA video agents (script, generation, posting) |
| **Total** | **11-12** | All agents unified |

---

## ✅ Success Criteria

### Feature Completeness
- ✅ All 13 features from main branch preserved
- ✅ All 8 new features from recovered branch added
- ✅ **Total: 21 features** (no losses)

### Agent Completeness
- ✅ All 6 original agents kept
- ✅ Analytics agent KEPT (not deleted)
- ✅ 2 new agents added (crowdsourcing, health_official)
- ✅ PSA video agents kept
- ✅ **Total: 11-12 agents**

### Context Injection
- ✅ Time context preserved
- ✅ Location context preserved
- ✅ Time frame context preserved

### Persona System
- ✅ User persona added
- ✅ Health official persona added
- ✅ Both personas work with context injection

---

## 🎯 Summary

**This unified plan ensures:**
1. ✅ **ZERO feature loss** from main branch
2. ✅ **ALL new features** from recovered branch added
3. ✅ **analytics_agent PRESERVED** (serves different purpose than health_official_agent)
4. ✅ **Context injection KEPT** (time, location, time_frame)
5. ✅ **Dual personas ADDED** (user & health official)
6. ✅ **BigQuery fixes KEPT** (no reversions)
7. ✅ **app_local.py KEPT** (primary application)

**Result:** Best of both worlds with 21 total features and 11-12 agents! 🎉

