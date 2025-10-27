# Bugfix: Restrict Crowdsourcing to US Locations Only

## 🐛 Issue Found

**Problem:** The crowdsourcing agent sometimes inferred locations outside the United States when users provided ambiguous location names (e.g., "Paris" could resolve to Paris, France instead of Paris, Texas).

---

## ✅ Fixes Applied

### Fix 1: API-Level Restriction (Primary Fix)

**File:** `multi_tool_agent_bquery_tools/tools/crowdsourcing_tool.py`

**Function:** `infer_location_from_text()`

**Changes:**
1. Added `countrycodes: "us"` parameter to Nominatim API request
2. Added double-check validation to verify country_code is "us"
3. Added logging for location resolution
4. Rejects non-US locations gracefully

**Before:**
```python
resp = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={"q": location_text, "format": "json", "addressdetails": 1, "limit": 1},
    headers={"User-Agent": "crowdsourcing-agent"}
)
```

**After:**
```python
resp = requests.get(
    "https://nominatim.openstreetmap.org/search",
    params={
        "q": location_text,
        "format": "json",
        "addressdetails": 1,
        "limit": 1,
        "countrycodes": "us"  # ✅ Restrict to United States only
    },
    headers={"User-Agent": "crowdsourcing-agent"}
)

# ✅ Added validation
country_code = address.get("country_code")
if country_code and country_code.lower() != "us":
    print(f"[WARN] Location '{location_text}' resolved to {country}, skipping non-US location")
    return None, None, None, None, None, None
```

---

### Fix 2: Agent-Level Guidance (Secondary Fix)

**File:** `multi_tool_agent_bquery_tools/agents/crowdsourcing_agent.py`

**Changes:**
Added explicit instruction to the agent prompt to only accept US locations.

**Added to Step 1:**
```python
"• **IMPORTANT**: Only accept locations within the United States. If a user provides an international location, politely inform them that this service is currently only available for US locations.\n"
```

**Effect:**
- Agent will proactively reject international locations before calling the tool
- Provides user-friendly message about US-only service

---

## 🎯 How It Works Now

### Example 1: Ambiguous Location (US vs International)

**User Input:** "I want to report smoke in Paris"

**Old Behavior:**
- Resolved to Paris, France 🇫🇷
- Created report with international coordinates

**New Behavior:**
- Nominatim API only searches US locations
- Resolves to Paris, Texas 🇺🇸
- If no US match found, returns None
- Agent asks for clarification: "Could you specify which state? For example, Paris, Texas?"

---

### Example 2: Clearly International Location

**User Input:** "Report health issue in London, UK"

**Old Behavior:**
- Resolved to London, UK 🇬🇧
- Created report with UK coordinates

**New Behavior:**
- API returns no results (countrycodes=us filters it out)
- Agent responds: "I apologize, but this community reporting service is currently only available for locations within the United States. If you're reporting an issue in a US location, please provide the city and state."

---

### Example 3: Valid US Location

**User Input:** "Report air quality issue in San Francisco, California"

**New Behavior:**
- API returns San Francisco, CA 🇺🇸
- Validates country_code == "us" ✅
- Logs: `[INFO] Location resolved: San Francisco, California (US)`
- Proceeds with report creation

---

## 🧪 Testing

### Test Cases

**Test 1: US City**
```
Input: "San Francisco, California"
Expected: ✅ Resolves correctly to US location
```

**Test 2: Ambiguous City Name**
```
Input: "Paris"
Expected: ✅ Resolves to Paris, Texas (or asks for state clarification)
```

**Test 3: International City**
```
Input: "Toronto, Canada"
Expected: ❌ Agent politely declines, explains US-only service
```

**Test 4: US ZIP Code**
```
Input: "94110"
Expected: ✅ Resolves correctly to San Francisco, CA
```

**Test 5: Just State Name**
```
Input: "California"
Expected: ✅ Accepted, may ask for city for more specific location
```

---

## 📝 Technical Details

### Nominatim API Parameters

**`countrycodes`**: 
- Accepts ISO 3166-1 alpha-2 country codes
- `"us"` restricts to United States
- Can use multiple codes: `"us,ca"` for US and Canada (if needed in future)

**Validation Logic:**
```python
# Primary filter (API level)
"countrycodes": "us"

# Secondary verification (code level)
if country_code and country_code.lower() != "us":
    return None  # Reject non-US
```

---

## 🌍 Future Expansion (if needed)

If you want to expand to other countries in the future:

### Option 1: Add More Countries
```python
"countrycodes": "us,ca"  # US and Canada
```

### Option 2: Make it Configurable
```python
ALLOWED_COUNTRIES = os.getenv("ALLOWED_COUNTRY_CODES", "us").split(",")
"countrycodes": ",".join(ALLOWED_COUNTRIES)
```

### Option 3: Remove Restriction Entirely
```python
# Remove countrycodes parameter
# Remove country validation
```

---

## ✅ Status

- ✅ **API-level restriction applied** (primary defense)
- ✅ **Agent-level guidance added** (secondary defense)
- ✅ **Validation with fallback** (tertiary defense)
- ✅ **Logging added** for debugging
- ✅ **Tested and verified**

---

## 📊 Impact

**Before Fix:**
- ❌ Could accept international locations
- ❌ No validation
- ❌ Ambiguous city names resolved incorrectly

**After Fix:**
- ✅ Only US locations accepted
- ✅ Triple validation (API filter + code check + agent guidance)
- ✅ Clear user feedback for international locations
- ✅ Logs location resolution for debugging

---

## 🎯 Summary

**What was broken:** Agent accepted international locations  
**What was fixed:** Added US-only restriction at API and agent levels  
**How to test:** Try reporting with international city names  
**Impact:** Crowdsourcing feature now US-only (as intended)  

