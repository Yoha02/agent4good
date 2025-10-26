# PSA Video Integration Plan: app.py → app_local.py

## 📋 Goal
Merge PSA video generation and Twitter posting functionality from `app.py` into `app_local.py` without breaking existing functionality.

## 🔍 Current State Analysis

### app.py (Our PSA Video App)
**Endpoints:**
- `/` - Homepage
- `/api/air-quality` - Air quality data
- `/api/analyze` - AI analysis
- `/api/health-recommendations` - Health recommendations
- `/api/agent-chat` - **ADK agent chat WITH PSA video trigger detection**
- `/acknowledgements` - Acknowledgements page
- **`/api/generate-psa-video`** - Generate PSA video ✅ (UNIQUE)
- **`/api/approve-and-post`** - Approve and post video ✅ (UNIQUE)
- **`/api/check-video-task/<task_id>`** - Check video generation status ✅ (UNIQUE)
- **`/api/post-to-twitter`** - Post video to Twitter ✅ (UNIQUE)
- `/health` - Health check

**Unique Features:**
1. PSA video generation workflow (4 endpoints)
2. Async video task manager
3. Twitter OAuth integration
4. Video keyword detection in agent chat
5. Enhanced ADK agent with PSA sub-agents

### app_local.py (Team's Enhanced App)
**Endpoints (28 total):**
- `/` - Homepage
- **Location Services (7 endpoints):** ✅ (UNIQUE)
  - `/api/locations/states`
  - `/api/locations/cities/<state_code>`
  - `/api/locations/counties/<state_code>/<city_name>`
  - `/api/locations/zipcodes/<state_code>`
  - `/api/locations/search`
  - `/api/locations/reverse-geocode`
  - `/api/locations` (legacy)
- `/api/air-quality` - EPA air quality
- `/api/analyze` - AI analysis
- `/api/health-recommendations` - Health recommendations
- `/api/agent-chat` - **ADK agent chat WITHOUT PSA video**
- **`/api/text-to-speech`** - Google TTS ✅ (UNIQUE)
- **Officials Dashboard (3 endpoints):** ✅ (UNIQUE)
  - `/officials-login`
  - `/officials-dashboard`
  - `/api/community-reports`
- **`/api/export-reports/<format>`** - Export reports ✅ (UNIQUE)
- **`/report`** - Community report form ✅ (UNIQUE)
- **`/api/submit-report`** - Submit community report ✅ (UNIQUE)
- **`/api/update-report`** - Update report ✅ (UNIQUE)
- **`/api/air-quality-detailed`** - Detailed pollutant data ✅ (UNIQUE)
- **Weather & Pollen APIs** ✅ (UNIQUE)
- `/acknowledgements` - Acknowledgements page
- `/health` - Health check

**Unique Features:**
1. Comprehensive location services
2. Google Cloud TTS integration
3. Community reporting system with AI analysis
4. Officials dashboard
5. GCS file uploads
6. Weather & Pollen APIs
7. Detailed air quality pollutant data

---

## ✅ **CRITICAL FINDING: app_local.py Already Has Everything!**

**Comparison Result:**
- ✅ `AirQualityAgent` class - EXISTS in both
- ✅ `/api/air-quality` - EXISTS in both (app_local uses EPA API, app.py uses custom dataset)
- ✅ `/api/analyze` - EXISTS in both  
- ✅ `/api/health-recommendations` - EXISTS in both
- ✅ `/api/agent-chat` - EXISTS in both (but needs PSA video trigger)
- ✅ `/acknowledgements` - EXISTS in both
- ❌ PSA video endpoints - ONLY in app.py (need to add)

**Conclusion:** We ONLY need to add PSA video features! All other functionality already exists in `app_local.py`.

## 🎯 Integration Strategy

### Phase 1: Add PSA Video Infrastructure (Non-Breaking)

**What to add to `app_local.py`:**

#### 1. **Import PSA Video Modules** (Top of file)
```python
# Add after existing imports
from multi_tool_agent_bquery_tools.async_video_manager import AsyncVideoManager
```

#### 2. **Initialize Async Video Manager** (After service initialization)
```python
# Add after location_service, weather_service, pollen_service initialization
try:
    video_manager = AsyncVideoManager()
    print("[OK] Async Video Manager initialized")
    VIDEO_MANAGER_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] Video Manager initialization failed: {e}")
    video_manager = None
    VIDEO_MANAGER_AVAILABLE = False
```

#### 3. **Add 4 New PSA Video Endpoints** (After existing endpoints)
```python
# Add these 4 endpoints from app.py (lines 432-605):
@app.route('/api/generate-psa-video', methods=['POST'])
def generate_psa_video_endpoint():
    # Copy from app.py line 433-479

@app.route('/api/approve-and-post', methods=['POST'])
def approve_and_post_video():
    # Copy from app.py line 481-505

@app.route('/api/check-video-task/<task_id>')
def check_video_task(task_id):
    # Copy from app.py line 507-529

@app.route('/api/post-to-twitter', methods=['POST'])
def post_to_twitter():
    # Copy from app.py line 531-604
```

#### 4. **Enhance `/api/agent-chat` Endpoint** (Minimal change)
Add PSA video trigger detection to existing `agent_chat()` function:

```python
# In app_local.py line 959, add after getting question:
# Check for PSA video generation keywords
video_keywords = [
    'create video', 'generate video', 'make video', 'produce video',
    'create psa', 'generate psa', 'make psa',
    'psa video', 'public service announcement', 'health alert video',
    'create announcement', 'make announcement'
]

wants_video = any(keyword in question.lower() for keyword in video_keywords)

if wants_video and VIDEO_MANAGER_AVAILABLE:
    # Create video generation task
    task_id = video_manager.create_task({
        'question': question,
        'state': state,
        'city': city,
        'zipcode': zipcode
    })
    
    return jsonify({
        'success': True,
        'response': "I'll generate a health alert video for you. This takes about 60 seconds. You can continue chatting while I work on this. I'll notify you when it's ready! Is there anything else I can help you with?",
        'agent': 'PSA Video Generator',
        'location': location_context,
        'task_id': task_id  # Frontend will poll with this
    })

# Continue with normal agent chat flow...
```

---

### Phase 2: Frontend Integration (Non-Breaking)

**What to add to `static/js/app.js`:**

Already done! ✅ We added:
- `lastVideoData` variable
- `isTwitterApproval()` function
- `postToTwitter()` function
- `pollForVideoCompletion()` function
- Video task_id detection in `askAI()`
- Video player in `addMessage()`

---

## 📁 File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `app_local.py` | **ADD** | 4 new PSA video endpoints |
| `app_local.py` | **MODIFY** | Add video trigger detection to `/api/agent-chat` (10 lines) |
| `app_local.py` | **ADD** | Initialize `AsyncVideoManager` (5 lines) |
| `app_local.py` | **ADD** | Import video manager (1 line) |
| `static/js/app.js` | ✅ **DONE** | PSA video frontend code already added |
| `multi_tool_agent_bquery_tools/agent.py` | ✅ **DONE** | PSA agents already integrated |
| `multi_tool_agent_bquery_tools/agents/psa_video.py` | ✅ **EXISTS** | PSA sub-agents |

---

## ✅ Integration Checklist

### Pre-Integration
- [x] Validate `app.py` works independently ✅
- [x] Validate `app_local.py` works independently ✅
- [x] Fix BigQuery issues (disease + air quality tools) ✅
- [x] Document both apps' features ✅

### Integration Steps
- [ ] Create integration branch `integrate-psa-to-app-local`
- [ ] Add `AsyncVideoManager` import to `app_local.py`
- [ ] Initialize video manager in `app_local.py`
- [ ] Copy 4 PSA endpoints to `app_local.py`
- [ ] Add video trigger detection to `agent_chat()` in `app_local.py`
- [ ] Test PSA video generation in `app_local.py`
- [ ] Test Twitter posting in `app_local.py`
- [ ] Test all existing `app_local.py` features still work
- [ ] Validate no regression in team features
- [ ] Clean up: Archive or rename `app.py`
- [ ] Update documentation

---

## 🚨 Risk Mitigation

### Low Risk Changes
✅ Adding new endpoints (no existing code affected)  
✅ Adding new imports (no conflicts expected)  
✅ Adding initialization code (separate try-except blocks)

### Medium Risk Changes
⚠️ Modifying `/api/agent-chat` endpoint
- **Mitigation:** Add video check BEFORE existing logic, don't modify existing flow
- **Testing:** Verify non-video queries still work identically

### No Risk
✅ Frontend already has PSA code (added earlier)  
✅ ADK agents already have PSA sub-agents  
✅ All PSA tools already exist in `multi_tool_agent_bquery_tools/`

---

## 🧪 Testing Plan

### 1. PSA Video Features (New)
- [ ] Ask: "Create a PSA video about air quality in California"
- [ ] Verify: Video generates and polling works
- [ ] Verify: Video appears with player
- [ ] Verify: Twitter posting prompt appears
- [ ] Test: Post to Twitter

### 2. Existing Features (Regression Test)
- [ ] Test: Air quality queries
- [ ] Test: Infectious disease queries  
- [ ] Test: Location search
- [ ] Test: Weather & pollen data
- [ ] Test: Community reporting
- [ ] Test: Officials dashboard
- [ ] Test: Text-to-speech
- [ ] Test: Export reports

### 3. ADK Agent Chat (Critical)
- [ ] Test: General health questions
- [ ] Test: Historical air quality
- [ ] Test: Live air quality
- [ ] Test: Disease tracking
- [ ] Test: Clinic finder

---

## 📦 Post-Integration

### Decision: What to do with `app.py`?
**Option A:** Rename to `app_legacy.py` (keep for reference)  
**Option B:** Delete `app.py` (clean slate)  
**Option C:** Move to `archive/` folder  

**Recommendation:** Option A - Keep as reference during testing

### Documentation Updates
- Update README to point to `app_local.py`
- Update deployment instructions
- Document PSA video feature
- Update API documentation

---

## 🎯 Success Criteria

✅ All 4 PSA video endpoints work in `app_local.py`  
✅ PSA video generation triggers correctly from chat  
✅ Twitter posting works  
✅ ALL existing `app_local.py` features work unchanged  
✅ No regressions in team features  
✅ ADK agent responds correctly to all query types  
✅ Frontend polls correctly for video completion  

---

## 🚀 Next Steps

1. **Review this plan** - Does it look good?
2. **Create integration branch** - `integrate-psa-to-app-local`
3. **Execute Phase 1** - Add PSA infrastructure to `app_local.py`
4. **Test thoroughly** - Both new and existing features
5. **Merge to main** - After validation
6. **Deploy** - One unified app!

---

**Estimated Time:** 30-45 minutes  
**Complexity:** Low (additive changes, minimal modifications)  
**Risk Level:** Low (well-isolated changes with fallbacks)

