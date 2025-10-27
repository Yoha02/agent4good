# Exact Changes to `multi_tool_agent_bquery_tools/agent.py`

## 🎯 Goal
Add crowdsourcing and health official agents while keeping ALL existing functionality intact.

---

## 📝 Change 1: Add New Imports (After line 33)

**Location:** After `from .tools.health_tools import get_health_faq` (line 33)

**Add these lines:**

```python
# Crowdsourcing and health official agents
from .agents.crowdsourcing_agent import crowdsourcing_agent
from .agents.health_official_agent import health_official_agent
from .tools.embedding_tool import generate_report_embeddings
```

**Result:**
```python
# Line 26-40 will look like:
# === Import all sub-agents and tools ===
from .agents.air_quality_agent import air_quality_agent
from .agents.live_air_quality_agent import live_air_quality_agent
from .agents.infectious_diseases_agent import infectious_diseases_agent
from .agents.clinic_finder_agent import clinic_finder_agent
from .agents.health_faq_agent import health_faq_agent
from .agents.psa_video import create_psa_video_agents
from .tools.health_tools import get_health_faq

# Crowdsourcing and health official agents
from .agents.crowdsourcing_agent import crowdsourcing_agent
from .agents.health_official_agent import health_official_agent
from .tools.embedding_tool import generate_report_embeddings

# Try to import analytics agent, use None if it fails
try:
    from .agents.analytics_agent import analytics_agent
except Exception as e:
    print(f"[WARNING] Analytics agent not available: {e}")
    analytics_agent = None
```

---

## 📝 Change 2: Update Welcome Menu (Lines 112-122)

**Location:** Inside `create_root_agent_with_context()` function, the instruction string

**BEFORE:**
```python
            "\"Welcome to the Community Health & Wellness Assistant!\n\n"
        "I can help you with:\n"
            "1. [LIVE AIR QUALITY] Check current air quality via the AirNow API\n"
            "2. [HISTORICAL AIR QUALITY] View past PM2.5 data from EPA BigQuery\n"
            "3. [DISEASES] Infectious Disease Tracking - County-level CDC data\n"
            "4. [CLINICS] Find nearby clinics or doctors using Google Search\n"
            "5. [HEALTH] General wellness, hygiene, and preventive care advice\n"
            "6. [ANALYTICS] Cross-dataset analysis across air quality and disease data\n"
            "7. [PSA VIDEOS] Generate and share public health announcement videos\n\n"
        "What would you like to know about today?\"\n\n"
```

**AFTER:**
```python
            "\"Welcome to the Community Health & Wellness Assistant!\n\n"
        "I can help you with:\n"
            "1. [LIVE AIR QUALITY] Check current air quality via the AirNow API\n"
            "2. [HISTORICAL AIR QUALITY] View past PM2.5 data from EPA BigQuery\n"
            "3. [DISEASES] Infectious Disease Tracking - County-level CDC data\n"
            "4. [CLINICS] Find nearby clinics or doctors using Google Search\n"
            "5. [HEALTH] General wellness, hygiene, and preventive care advice\n"
            "6. [ANALYTICS] Cross-dataset analysis across air quality and disease data\n"
            "7. [PSA VIDEOS] Generate and share public health announcement videos\n"
            "8. [COMMUNITY REPORTS] Submit health and environmental incident reports\n"
            "9. [REPORT INSIGHTS] Search and analyze community reports (for officials)\n\n"
        "What would you like to know about today?\"\n\n"
```

---

## 📝 Change 3: Add New Routing Rules (Lines 124-133)

**Location:** After the existing routing rules, before "Process:"

**BEFORE:**
```python
            "Routing Rules:\n"
            "- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.\n"
            "- Questions mentioning years, months, or historical data → air_quality_agent.\n"
            "- Mentions of infections, outbreaks, or diseases → infectious_diseases_agent.\n"
            "- If the user describes symptoms or feeling unwell "
            "(e.g., 'I have a rash', 'I feel dizzy', 'my tooth hurts', 'I cut my hand', "
            "'my child is sick'), route to clinic_finder_agent."
            "- General health, hygiene, prevention, wellness, or safety advice → health_faq_agent.\n"
            "- Analytical questions spanning multiple datasets, correlations, trends, or complex analysis → analytics_agent.\n"
            "- Requests to create PSA videos, announcements, or post to social media → PSA video agents.\n\n"
            "Process:\n"
```

**AFTER:**
```python
            "Routing Rules:\n"
            "- Mentions of 'live', 'today', 'current', or 'now' → live_air_quality_agent.\n"
            "- Questions mentioning years, months, or historical data → air_quality_agent.\n"
            "- Mentions of infections, outbreaks, or diseases → infectious_diseases_agent.\n"
            "- If the user describes symptoms or feeling unwell "
            "(e.g., 'I have a rash', 'I feel dizzy', 'my tooth hurts', 'I cut my hand', "
            "'my child is sick'), route to clinic_finder_agent."
            "- General health, hygiene, prevention, wellness, or safety advice → health_faq_agent.\n"
            "- Analytical questions spanning multiple datasets, correlations, trends, or complex analysis → analytics_agent.\n"
            "- Requests to create PSA videos, announcements, or post to social media → PSA video agents.\n"
            "- Mentions of 'report', 'submit report', 'file incident', 'log issue', 'report problem' → crowdsourcing_agent.\n"
            "- Mentions of 'search reports', 'report trends', 'community insights', 'semantic search', 'report analytics' → health_official_agent.\n"
            "- Requests to 'generate embeddings', 'update embeddings', 'refresh semantic index' → call generate_report_embeddings tool directly.\n\n"
            "Process:\n"
```

---

## 📝 Change 4: Add New Sub-Agents (Lines 141-147)

**Location:** Inside the `sub_agents` list

**BEFORE:**
```python
        sub_agents=[
            air_quality_agent,
            live_air_quality_agent,
            infectious_diseases_agent,
            clinic_finder_agent,
            health_faq_agent,
        ] + ([analytics_agent] if analytics_agent else []) + psa_agents  # Add analytics agent (if available) and PSA video agents
```

**AFTER:**
```python
        sub_agents=[
            air_quality_agent,
            live_air_quality_agent,
            infectious_diseases_agent,
            clinic_finder_agent,
            health_faq_agent,
            crowdsourcing_agent,
            health_official_agent,
        ] + ([analytics_agent] if analytics_agent else []) + psa_agents  # Add analytics agent (if available) and PSA video agents
```

---

## 📝 Change 5: Add Tools to Root Agent (Line 106-110)

**Location:** Where the Agent is created in `create_root_agent_with_context()`

**BEFORE:**
```python
    return Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant that routes queries to specialized sub-agents.",
        global_instruction=global_context,
    instruction=(
```

**AFTER:**
```python
    return Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant that routes queries to specialized sub-agents.",
        global_instruction=global_context,
        tools=[generate_report_embeddings],  # Add embedding generation tool
    instruction=(
```

---

## 📊 Summary of Changes

| Change | Lines | Type | Risk |
|--------|-------|------|------|
| Add imports | After 33 | Addition | ✅ Low - pure addition |
| Update welcome menu | 112-122 | Modification | ✅ Low - just text |
| Add routing rules | 124-133 | Addition | ✅ Low - adding rules |
| Add sub-agents | 141-147 | Addition | ✅ Low - adding to list |
| Add tools | 106-110 | Addition | ✅ Low - adding tool |

**Total lines modified:** ~15 lines  
**Total lines added:** ~10 lines  
**Total lines deleted:** 0 lines

**Risk assessment:** ✅ **VERY LOW**
- All changes are additive
- No existing code is removed
- No existing logic is modified
- All existing context injection logic preserved
- All existing sub-agents preserved

---

## ✅ Validation Checklist

After making changes, verify:

- [ ] File still imports correctly (`python -c "from multi_tool_agent_bquery_tools.agent import root_agent"`)
- [ ] All existing sub-agents still registered
- [ ] New sub-agents imported successfully
- [ ] `crowdsourcing_agent` accessible
- [ ] `health_official_agent` accessible
- [ ] `generate_report_embeddings` tool accessible
- [ ] No syntax errors
- [ ] No import errors
- [ ] Context injection logic unchanged
- [ ] `call_agent()` function unchanged

---

## 🔧 Testing After Changes

**Test 1: Verify existing functionality**
```python
from multi_tool_agent_bquery_tools.agent import call_agent

# Test air quality
response = call_agent("What's the air quality in San Francisco?")
print(response)
```

**Test 2: Verify new crowdsourcing agent**
```python
response = call_agent("I want to report a health issue in my area")
print(response)
```

**Test 3: Verify new health official agent**
```python
response = call_agent("Show me community health reports from last week")
print(response)
```

**Test 4: Verify embedding tool**
```python
response = call_agent("Generate embeddings for new reports")
print(response)
```

---

## 🚨 Rollback Plan

If anything breaks:

```bash
# Revert agent.py changes
git checkout main -- multi_tool_agent_bquery_tools/agent.py

# Remove new files
git rm multi_tool_agent_bquery_tools/agents/crowdsourcing_agent.py
git rm multi_tool_agent_bquery_tools/agents/health_official_agent.py
git rm multi_tool_agent_bquery_tools/tools/crowdsourcing_tool.py
git rm multi_tool_agent_bquery_tools/tools/embedding_tool.py
git rm multi_tool_agent_bquery_tools/tools/semantic_query_tool.py
```

---

## 📌 Notes

1. The `create_root_agent_with_context()` function is ONLY used for dynamic agent creation - it's not the default
2. The default `root_agent` (line 154) will automatically get updated when we change the function
3. All context injection logic remains untouched
4. This is a **zero-risk** change - purely additive

