# Persona Changes from Recovered Branch

## 🎭 Major Discovery: Dual-Persona System

The `recovered_agent_code` branch has implemented a **dual-persona system** that provides different experiences for:
1. **Regular users** (citizens)
2. **Health officials** (public health professionals)

This is controlled by the `LOGIN_ROLE` environment variable.

---

## 🔍 What's Different?

### Current Main Branch:
- Single persona: "Community Health & Wellness Assistant"
- Uses `create_root_agent_with_context()` function with dynamic context injection
- Menu shown in instruction string
- Has sophisticated time/location context injection

### Recovered Branch:
- **Dual persona system**:
  - `user_prompt` - For everyday citizens
  - `health_official_prompt` - For public health officials
- Simplified agent creation (no dynamic context function)
- Role determined by `LOGIN_ROLE` env var
- Different menus and routing for each role

---

## 📋 Two Distinct Personas

### Persona 1: User (Citizen) Prompt

**Tone:** Friendly, approachable, supportive  
**Menu:**
1. Live Air Quality
2. Historical Air Quality
3. Infectious Diseases
4. Clinics & Doctors
5. **Community Reports** ← NEW
6. Health & Wellness FAQs

**Key Features:**
- Warm, welcoming tone
- Simplified explanations
- Focus on immediate health needs
- Encourages community reporting
- "Sound like a helpful health advocate, not a scientist"

**Example Questions:**
- "Check air quality in San Jose"
- "Report a smoke issue in my area"
- "Find a clinic for skin rash in Dublin"
- "Is Salmonella common during summer?"

---

### Persona 2: Health Official Prompt

**Tone:** Analytical, professional, data-driven  
**Menu:**
1. Live Air Quality
2. Historical Air Quality
3. Infectious Disease Trends
4. Clinic Locator
5. **Crowdsourced Reports** ← NEW
6. **Crowdsourced Insights Dashboard** ← NEW
7. **PSA & Outreach Videos** ← NEW

**Key Features:**
- Professional, confident tone
- Data-driven insights
- Trend analysis and metrics
- Semantic search capabilities
- "Phrase insights like a field report"

**Example Questions:**
- "Show community health reports for Alameda County"
- "Summarize summer Salmonella trends in California"
- "Generate embeddings for new reports"
- "Create a PSA video on wildfire smoke safety"
- "Compare last month's air quality in San Diego vs Los Angeles"

---

## 🤔 Integration Decision Required

### Option 1: Adopt Dual-Persona System (Recommended)
**Pros:**
- ✅ Better user experience (tailored to audience)
- ✅ Health officials get advanced analytics features
- ✅ Regular users get simplified, friendly interface
- ✅ Aligns with recovered branch design
- ✅ Cleaner separation of concerns

**Cons:**
- ⚠️ Requires removing `create_root_agent_with_context()` function
- ⚠️ Loses dynamic context injection (time, location, time_frame)
- ⚠️ More complex to maintain two personas
- ⚠️ Need to add `LOGIN_ROLE` env var to Cloud Run

**Changes Required:**
- Replace entire persona/instruction system in `agent.py`
- Add `user_prompt` and `health_official_prompt` variables
- Add `LOGIN_ROLE` logic
- Remove `create_root_agent_with_context()` function
- Update `call_agent()` to work without context injection

---

### Option 2: Hybrid Approach (Merge Both)
**Keep our current system BUT add persona switching**

**Pros:**
- ✅ Keeps sophisticated context injection
- ✅ Adds dual-persona benefits
- ✅ Best of both worlds
- ✅ More flexibility

**Cons:**
- ⚠️ More complex code
- ⚠️ Need to update both prompts to include context injection
- ⚠️ Requires careful merging

**Changes Required:**
- Keep `create_root_agent_with_context()` function
- Modify it to accept `persona_type` parameter
- Create two persona strings (user & health official)
- Inject context into chosen persona prompt
- Add `LOGIN_ROLE` logic

---

### Option 3: Keep Current System, Ignore Personas
**Just add new agents without persona changes**

**Pros:**
- ✅ Simplest integration
- ✅ No risk to existing functionality
- ✅ Keeps context injection

**Cons:**
- ❌ Misses improved UX from recovered branch
- ❌ Single persona for all users
- ❌ Less aligned with recovered branch vision

**Changes Required:**
- Just add new agents and routing rules to existing prompt
- No persona system changes

---

## 💡 Recommended Approach: **Option 2 (Hybrid)**

### Why Hybrid is Best:
1. **Preserves our bug fixes** (context injection, BigQuery fixes)
2. **Adds persona benefits** (better UX for different users)
3. **Future-proof** (can be deployed with or without persona switching)
4. **Backward compatible** (defaults to user persona if no LOGIN_ROLE set)

### Implementation Plan:

```python
# Add persona prompts as variables
USER_PROMPT = """
[User-friendly prompt from recovered branch]
"""

HEALTH_OFFICIAL_PROMPT = """
[Professional prompt from recovered branch]
"""

def create_root_agent_with_context(location_context=None, time_frame=None, persona_type=None):
    """Create the root agent with dynamic context AND persona"""
    
    # Get current time context
    time_context = get_current_time_context()
    
    # Build location context
    location_info = ""
    if location_context:
        # ... existing location context code ...
    
    # Build time frame context
    time_frame_info = ""
    if time_frame:
        # ... existing time frame context code ...
    
    # Choose persona based on LOGIN_ROLE or parameter
    if persona_type is None:
        persona_type = os.getenv("LOGIN_ROLE", "user")
    
    if persona_type == "health_official":
        base_instruction = HEALTH_OFFICIAL_PROMPT
    else:
        base_instruction = USER_PROMPT
    
    # Combine context with persona
    global_context = f"{time_context}{location_info}{time_frame_info}"
    
    return Agent(
        name="community_health_assistant",
        model=GEMINI_MODEL,
        description="Main community health assistant that routes queries to specialized sub-agents.",
        global_instruction=global_context,
        instruction=base_instruction,
        tools=[generate_report_embeddings],
        sub_agents=[
            air_quality_agent,
            live_air_quality_agent,
            infectious_diseases_agent,
            clinic_finder_agent,
            health_faq_agent,
            crowdsourcing_agent,
            health_official_agent,
        ] + ([analytics_agent] if analytics_agent else []) + psa_agents
    )

# Default root agent with user persona
root_agent = create_root_agent_with_context()
```

---

## 📝 Updated Changes Required

### 1. Add Persona Prompts (After imports, before functions)
```python
# === Persona Definitions ===
USER_PROMPT = """
[Full user prompt from recovered branch]
"""

HEALTH_OFFICIAL_PROMPT = """
[Full health official prompt from recovered branch]
"""
```

### 2. Update `create_root_agent_with_context()` Function
- Add `persona_type=None` parameter
- Add persona selection logic
- Use selected persona as instruction

### 3. Update `call_agent()` Function (Optional)
- Add `persona_type=None` parameter if we want to override per-call

### 4. Add Environment Variable
- Add `LOGIN_ROLE=user` (or `health_official`) to `.env` and Cloud Run

---

## 🎯 Key Differences in Persona Prompts

| Feature | User Prompt | Health Official Prompt |
|---------|-------------|------------------------|
| **Tone** | Friendly, warm | Professional, analytical |
| **Menu Items** | 6 basic features | 7 advanced features (includes insights & PSA) |
| **Routing** | Simplified | More detailed |
| **Examples** | Simple queries | Complex analytical queries |
| **Closing** | "Is there anything else I can help you?" | "Would you like a visualization or PSA follow-up?" |
| **Language** | "Sound like a health advocate" | "Phrase insights like a field report" |
| **Community Reports** | "Submit reports" | "Submit + Analyze reports" |
| **PSA Videos** | Not mentioned | Explicitly offered |

---

## ✅ Decision Needed

**Which approach should we use?**

**Option 2 (Hybrid)** is recommended because:
- ✅ Keeps all our bug fixes
- ✅ Adds better UX via personas
- ✅ Can be deployed incrementally
- ✅ Backward compatible

**Next Steps if Option 2:**
1. Add `USER_PROMPT` and `HEALTH_OFFICIAL_PROMPT` variables
2. Update `create_root_agent_with_context()` to support personas
3. Add persona selection logic
4. Test with both personas
5. Document `LOGIN_ROLE` env var in deployment guide

---

## 🚦 What's Your Preference?

1. **Option 2 (Hybrid)** - Best of both worlds ← Recommended
2. **Option 1 (Full Adopt)** - Replace with dual-persona system
3. **Option 3 (Ignore)** - Keep current, skip persona changes

Let me know which you prefer and I'll update the integration plan accordingly! 🎯

