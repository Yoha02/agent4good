# Veo 3 Video PSA + Twitter Feature - Implementation Plan

## 🎯 Feature Overview

Add capability for users to:
1. Request AI-generated PSA video about health warnings
2. Review/validate video in UI
3. Post approved video to Twitter/X with proper hashtags

---

## 📊 Current Architecture Analysis

### **Existing Multi-Agent System:**

```python
root_agent (community_health_assistant)
├── air_quality_agent (queries EPA data)
├── infectious_diseases_agent (queries CDC data)
└── tools: [get_health_faq]
```

**Agent Definition Pattern**:
- Each sub-agent has: `name`, `model`, `description`, `instruction`, `tools`
- Root agent routes queries using `sub_agents=[]` parameter
- Communication via ADK Runner and InMemorySessionService

**Current Tools/Functions**:
1. `get_air_quality()` - Queries BigQuery EPA data
2. `get_infectious_disease_data()` - Queries BigQuery CDC data
3. `get_health_faq()` - Returns FAQ responses
4. `get_current_time()` - Time utility
5. `get_table_schema()` - BigQuery schema
6. `test_table_columns()` - BigQuery testing

---

## 🏗️ New Architecture Design

### **Extended Multi-Agent System:**

```python
root_agent (community_health_assistant)
├── air_quality_agent (existing)
├── infectious_diseases_agent (existing)
├── actionline_agent (NEW - Sub-Agent 3)
├── veo_prompt_agent (NEW - Sub-Agent 4)
└── twitter_agent (NEW - Sub-Agent 5)
```

### **New Workflow:**

```
User Request
    ↓
Root Agent recognizes "create video PSA" intent
    ↓
1. ActionLine Agent
   - Takes health data (AQI, disease info)
   - Generates 1-line actionable recommendation (≤12 words)
   ↓
2. VeoPrompt Agent
   - Takes the 1-liner
   - Creates Veo 3 video prompt
   - Includes scene description, timing, visual style
   ↓
3. Veo 3 API
   - Generates 8-second video
   - Saves to Google Cloud Storage
   - Returns GCS URI
   ↓
4. UI Video Player
   - Displays video for user validation
   - Shows proposed tweet text
   - User can approve/reject/edit
   ↓
5. Twitter Agent (on user approval)
   - Posts video to Twitter/X
   - Adds hashtags (#HealthAlert, #AirQuality, etc.)
   - Includes description
   - Returns tweet URL
```

---

## 📝 Implementation Steps

### **Phase 1: Create New Sub-Agents**

#### **Step 1.1: ActionLine Agent**

**File**: `multi_tool_agent_bquery_tools/agent.py`

**Function to add**:
```python
def generate_action_line(health_data: dict) -> dict:
    """
    Converts health data into a single actionable recommendation.
    
    Args:
        health_data: Dict with keys:
            - type: "air_quality" or "disease"
            - severity: "good", "moderate", "unhealthy", etc.
            - location: state/county
            - metric: AQI value or case count
            - details: additional context
    
    Returns:
        dict: {
            "status": "success",
            "action_line": "Single sentence recommendation",
            "category": "air_quality" or "disease",
            "severity": severity level
        }
    """
```

**Agent definition**:
```python
actionline_agent = Agent(
    name="actionline_agent",
    model=GEMINI_MODEL,
    description="Public health recommendation writer - converts data to action lines",
    instruction=(
        "You are ActionLine, a public-health recommendation writer. "
        "Your job: read detailed health or environmental bulletins and output "
        "one short, plain-language action the public should take right now. "
        "Rules: "
        "- Output one sentence only, ≤12 words, imperative voice "
        "- Make it immediately doable (verb + object + condition) "
        "- Be calm, non-alarmist, inclusive, specific "
        "- Prefer safest minimal action "
        "- Never mention agencies, models, datasets, links, disclaimers, emojis "
        "Examples: 'Wear a mask outside.' | 'Limit outdoor exertion.' | 'Close windows.'"
    ),
    tools=[generate_action_line],
)
```

#### **Step 1.2: VeoPrompt Agent**

**Function to add**:
```python
def create_veo_prompt(action_line: str, category: str, severity: str) -> dict:
    """
    Converts action line into Veo 3 video generation prompt.
    
    Args:
        action_line: The 1-sentence recommendation
        category: "air_quality", "disease", "water", etc.
        severity: "low", "moderate", "high", "critical"
    
    Returns:
        dict: {
            "status": "success",
            "veo_prompt": "Full Veo 3 prompt text",
            "duration": 8,
            "aspect_ratio": "1080x1920"
        }
    """
```

**Agent definition**:
```python
veo_prompt_agent = Agent(
    name="veo_prompt_agent",
    model=GEMINI_MODEL,
    description="Prompt engineer for Veo 3 video infographic generation",
    instruction=(
        "You are VeoPrompt, a prompt-engineer for Veo 3 video generation. "
        "Convert a single action line into a concise prompt for an 8-second, "
        "silent, vertical video infographic. "
        "Visual language: clean, flat vector, soft gradients, rounded shapes, "
        "high contrast, friendly, no clutter. "
        "Layout: big icon center, green check for 'do' or red caution for 'avoid', "
        "single rounded banner at bottom with action text. "
        "Duration: 8 seconds, silent, aspect: 1080×1920 vertical."
    ),
    tools=[create_veo_prompt],
)
```

#### **Step 1.3: Veo 3 Video Generation Function**

**Function to add**:
```python
def generate_psa_video(veo_prompt: str, output_prefix: str) -> dict:
    """
    Calls Google Veo 3 API to generate video.
    
    Args:
        veo_prompt: The formatted Veo prompt
        output_prefix: GCS path prefix (e.g., "gs://bucket/videos/psa-")
    
    Returns:
        dict: {
            "status": "success",
            "video_uri": "gs://bucket/path/to/video.mp4",
            "operation_id": "operation-id",
            "estimated_time": 60  # seconds
        }
    """
```

#### **Step 1.4: Twitter Agent**

**Function to add**:
```python
def post_to_twitter(video_uri: str, message: str, hashtags: list) -> dict:
    """
    Posts video and message to Twitter/X.
    
    Args:
        video_uri: GCS URI of video
        message: Tweet text
        hashtags: List of hashtags (e.g., ["HealthAlert", "AirQuality"])
    
    Returns:
        dict: {
            "status": "success",
            "tweet_url": "https://twitter.com/.../status/...",
            "tweet_id": "1234567890"
        }
    """
```

**Agent definition**:
```python
twitter_agent = Agent(
    name="twitter_agent",
    model=GEMINI_MODEL,
    description="Social media manager for posting health PSAs to Twitter/X",
    instruction=(
        "You are a social media specialist that posts community health PSAs to Twitter/X. "
        "You format tweets professionally with appropriate hashtags. "
        "Always use relevant hashtags: #PublicHealth, #HealthAlert, #CommunityWellness "
        "Keep messages clear, concise, and actionable."
    ),
    tools=[post_to_twitter],
)
```

---

### **Phase 2: Update Root Agent**

Add new sub-agents to root agent:

```python
root_agent = Agent(
    name="community_health_assistant",
    model=GEMINI_MODEL,
    description="Main community health assistant with PSA video generation",
    instruction=(
        # ... existing instructions ...
        "NEW CAPABILITIES: "
        "- Video PSA generation → Route to actionline_agent then veo_prompt_agent "
        "- Social media posting → Route to twitter_agent "
        "When user asks to 'create video' or 'generate PSA': "
        "1. Get current health data "
        "2. Call actionline_agent for recommendation "
        "3. Call veo_prompt_agent for video prompt "
        "4. Generate video with Veo 3 "
        "5. Return video for user validation "
    ),
    tools=[get_health_faq, generate_psa_video],
    sub_agents=[
        air_quality_agent,
        infectious_diseases_agent,
        actionline_agent,
        veo_prompt_agent,
        twitter_agent
    ],
)
```

---

### **Phase 3: Flask Backend Updates**

#### **New API Endpoints**:

```python
@app.route('/api/generate-psa-video', methods=['POST'])
def generate_psa_video_endpoint():
    """
    Generate PSA video from health data
    
    Request:
        {
            "location": "California",
            "data_type": "air_quality" or "disease",
            "auto_generate": true/false
        }
    
    Response:
        {
            "success": true,
            "action_line": "Wear a mask outside.",
            "veo_prompt": "Full prompt...",
            "video_uri": "gs://...",
            "preview_url": "https://...",
            "tweet_draft": {
                "text": "Health Alert for California...",
                "hashtags": ["HealthAlert", "AirQuality", "California"]
            }
        }
    """
```

```python
@app.route('/api/post-to-twitter', methods=['POST'])
def post_to_twitter_endpoint():
    """
    Post approved video to Twitter
    
    Request:
        {
            "video_uri": "gs://...",
            "message": "Tweet text",
            "hashtags": ["tag1", "tag2"]
        }
    
    Response:
        {
            "success": true,
            "tweet_url": "https://twitter.com/.../status/...",
            "tweet_id": "1234567890"
        }
    """
```

```python
@app.route('/api/check-video-status', methods=['GET'])
def check_video_status():
    """
    Check Veo 3 video generation status
    
    Request: ?operation_id=...
    
    Response:
        {
            "status": "processing" | "complete" | "error",
            "progress": 75,
            "video_uri": "gs://..." (if complete)
        }
    """
```

---

### **Phase 4: Frontend Updates**

#### **New UI Components**:

**1. Video PSA Generation Panel** (add to `templates/index.html`):
```html
<div class="psa-video-section">
    <h3>🎥 Generate PSA Video</h3>
    <button onclick="generatePSAVideo()">
        Create Health Alert Video
    </button>
    
    <div id="videoPreview" class="hidden">
        <video controls></video>
        <div class="tweet-preview">
            <textarea id="tweetText"></textarea>
            <div id="hashtags"></div>
        </div>
        <button onclick="approveAndPost()">
            ✓ Approve & Post to Twitter
        </button>
        <button onclick="regenerate()">
            🔄 Regenerate
        </button>
    </div>
</div>
```

**2. JavaScript Functions** (add to `static/js/app.js`):
```javascript
async function generatePSAVideo() {
    // Get current health data
    // Call /api/generate-psa-video
    // Poll for video completion
    // Display preview
}

async function approveAndPost() {
    // Call /api/post-to-twitter
    // Show success message with tweet URL
}
```

---

### **Phase 5: External Service Integration**

#### **5.1: Google Cloud Storage Setup**

```bash
# Create bucket for video storage
gsutil mb -l us-central1 gs://your-project-psa-videos

# Set CORS for video playback
echo '[{"origin": ["*"], "method": ["GET"], "maxAgeSeconds": 3600}]' > cors.json
gsutil cors set cors.json gs://your-project-psa-videos

# Set public read permissions
gsutil iam ch allUsers:objectViewer gs://your-project-psa-videos
```

#### **5.2: Veo 3 API Setup**

**Enable API**:
```bash
gcloud services enable aiplatform.googleapis.com
```

**Environment variables**:
```env
GOOGLE_CLOUD_LOCATION=us-central1
GCS_VIDEO_BUCKET=your-project-psa-videos
GCS_VIDEO_PREFIX=psa-videos/
```

#### **5.3: Twitter API Setup**

**Get credentials from**: https://developer.twitter.com/en/portal/dashboard

**Required**:
- API Key
- API Secret
- Access Token
- Access Token Secret
- OAuth 2.0 Client ID (for video upload)

**Environment variables**:
```env
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret
TWITTER_BEARER_TOKEN=your-bearer-token
```

**Install library**:
```bash
pip install tweepy
```

---

### **Phase 6: Dependencies to Add**

Update `requirements.txt`:
```
# Existing dependencies...

# Video generation
google-cloud-aiplatform>=1.95.0  # For Veo 3
google-cloud-storage>=2.0.0      # For GCS

# Social media
tweepy>=4.14.0                   # For Twitter API v2

# Video processing (optional)
opencv-python>=4.8.0             # For video manipulation
pillow>=10.0.0                   # For thumbnails
```

---

## 🔄 Detailed Workflow

### **User Journey:**

1. **User clicks "Generate Health Alert Video"**
   - UI shows loading state
   - Fetches current health data (air quality OR disease)

2. **Backend processes request**:
   ```
   a. Call root_agent with "Create PSA video for [location]"
   b. Root agent routes to actionline_agent
   c. ActionLine agent analyzes data → "Wear a mask outside."
   d. Root agent routes to veo_prompt_agent
   e. VeoPrompt agent creates full prompt
   f. Backend calls Veo 3 API
   g. Poll operation status (takes ~60-90 seconds)
   h. Video saved to GCS
   ```

3. **UI displays preview**:
   - Video player with generated video
   - Proposed tweet text: "Health Alert for [Location]: [Action Line]"
   - Hashtags: #HealthAlert #AirQuality #[State]
   - Approve/Reject buttons

4. **User approves**:
   - Backend calls twitter_agent
   - Video uploaded to Twitter
   - Tweet posted with hashtags
   - UI shows success + tweet URL

---

## 📁 File Structure Changes

```
agent4good/
├── app.py (UPDATE - add 3 new endpoints)
├── requirements.txt (UPDATE - add dependencies)
│
├── multi_tool_agent_bquery_tools/
│   ├── agent.py (UPDATE - add 3 new agents + 3 new functions)
│   ├── veo_integration.py (NEW - Veo 3 API wrapper)
│   └── twitter_integration.py (NEW - Twitter API wrapper)
│
├── templates/
│   └── index.html (UPDATE - add video PSA section)
│
├── static/js/
│   ├── app.js (UPDATE - add video generation functions)
│   └── psa-video.js (NEW - video player and approval logic)
│
└── static/css/
    └── style.css (UPDATE - add video player styles)
```

---

## 🔧 Implementation Checklist

### **Backend Development:**

- [ ] Create `veo_integration.py` module
  - [ ] `generate_video()` function
  - [ ] `poll_operation_status()` function
  - [ ] `get_video_url()` function

- [ ] Create `twitter_integration.py` module
  - [ ] `authenticate_twitter()` function
  - [ ] `upload_video()` function
  - [ ] `post_tweet()` function
  - [ ] `format_hashtags()` function

- [ ] Update `agent.py`:
  - [ ] Add `generate_action_line()` function
  - [ ] Add `create_veo_prompt()` function
  - [ ] Add `post_to_twitter()` function
  - [ ] Define `actionline_agent`
  - [ ] Define `veo_prompt_agent`
  - [ ] Define `twitter_agent`
  - [ ] Update `root_agent` with new sub-agents

- [ ] Update `app.py`:
  - [ ] Add `/api/generate-psa-video` endpoint
  - [ ] Add `/api/check-video-status` endpoint
  - [ ] Add `/api/post-to-twitter` endpoint
  - [ ] Add `/api/get-video-preview` endpoint

### **Frontend Development:**

- [ ] Update `index.html`:
  - [ ] Add "Generate PSA Video" button
  - [ ] Add video preview section
  - [ ] Add tweet preview/edit form
  - [ ] Add approval buttons

- [ ] Create `psa-video.js`:
  - [ ] `generatePSAVideo()` function
  - [ ] `pollVideoStatus()` function
  - [ ] `displayVideoPreview()` function
  - [ ] `approveAndPost()` function
  - [ ] `regenerateVideo()` function

- [ ] Update `style.css`:
  - [ ] Video player container styles
  - [ ] Tweet preview styles
  - [ ] Loading animations for video generation

### **Google Cloud Setup:**

- [ ] Create GCS bucket for videos
- [ ] Set CORS policy
- [ ] Set public read permissions
- [ ] Enable Vertex AI API
- [ ] Test Veo 3 API access

### **Twitter/X Setup:**

- [ ] Create Twitter Developer account
- [ ] Create app and get API credentials
- [ ] Set up OAuth 2.0
- [ ] Test video upload
- [ ] Test tweet posting

### **Testing:**

- [ ] Test ActionLine agent with various health data
- [ ] Test VeoPrompt agent output quality
- [ ] Test Veo 3 video generation
- [ ] Test video storage and retrieval
- [ ] Test Twitter posting (use test account)
- [ ] Test full end-to-end workflow
- [ ] Test error handling for each step

### **Deployment:**

- [ ] Update deployment command with new env vars
- [ ] Deploy to Cloud Run
- [ ] Verify video generation works in production
- [ ] Verify Twitter posting works
- [ ] Test on live site

---

## 📊 Data Flow Diagram

```
User clicks "Generate PSA Video"
        ↓
Frontend gathers context
(location, current AQI/disease data)
        ↓
POST /api/generate-psa-video
{location: "California", type: "air_quality"}
        ↓
Backend calls root_agent
"Create video PSA for California air quality"
        ↓
┌─────────────────────────────────┐
│  ActionLine Agent               │
│  Input: {aqi: 150, pm25: 55.4}  │
│  Output: "Limit outdoor activity."│
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  VeoPrompt Agent                │
│  Input: "Limit outdoor activity."│
│  Output: Full Veo 3 prompt      │
└────────────┬────────────────────┘
             ↓
┌─────────────────────────────────┐
│  Veo 3 API Call                 │
│  - Generate 8-sec video         │
│  - Save to GCS                  │
│  - Return operation ID          │
└────────────┬────────────────────┘
             ↓
Poll operation status (60-90 sec)
             ↓
┌─────────────────────────────────┐
│  Video Ready!                   │
│  gs://bucket/psa-video-123.mp4  │
└────────────┬────────────────────┘
             ↓
Return to frontend with preview URL
             ↓
User reviews and approves
             ↓
POST /api/post-to-twitter
{video_uri: "gs://...", message: "..."}
             ↓
┌─────────────────────────────────┐
│  Twitter Agent                  │
│  - Download video from GCS      │
│  - Upload to Twitter            │
│  - Post tweet with hashtags     │
└────────────┬────────────────────┘
             ↓
Return tweet URL to user
             ↓
UI shows success + link to tweet
```

---

## 🎨 UI/UX Design

### **Video Generation Section** (add after chat section):

```
┌────────────────────────────────────────┐
│  🎥 Public Service Announcement        │
│  Generate AI Video for Health Alerts   │
│                                        │
│  Current Status: [Good/Moderate/...]  │
│  Location: [California ▼]             │
│                                        │
│  [Generate PSA Video] 🎬              │
└────────────────────────────────────────┘
```

### **Video Preview Modal**:

```
┌────────────────────────────────────────┐
│  ✓ Video Generated!                    │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │                                  │ │
│  │     [Video Player]               │ │
│  │     8 seconds                    │ │
│  │                                  │ │
│  └──────────────────────────────────┘ │
│                                        │
│  Tweet Preview:                        │
│  ┌──────────────────────────────────┐ │
│  │ 🚨 Health Alert for California   │ │
│  │ Limit outdoor activity today.    │ │
│  │                                  │ │
│  │ #HealthAlert #AirQuality #CA     │ │
│  └──────────────────────────────────┘ │
│                                        │
│  [✓ Approve & Post]  [🔄 Regenerate]  │
│  [✕ Cancel]                           │
└────────────────────────────────────────┘
```

---

## 💾 Environment Variables Summary

**New variables needed**:

```env
# Veo 3 Configuration
GOOGLE_CLOUD_LOCATION=us-central1
GCS_VIDEO_BUCKET=your-project-psa-videos
GCS_VIDEO_PREFIX=psa-videos/
GOOGLE_GENAI_USE_VERTEXAI=TRUE  # Changed from FALSE for Veo

# Twitter/X Configuration
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-access-token-secret
TWITTER_BEARER_TOKEN=your-bearer-token

# Community Twitter Account
TWITTER_ACCOUNT_HANDLE=@CommunityHealthAlerts
```

---

## ⚠️ Critical Considerations

### **Rate Limits:**
- **Veo 3**: ~5-10 videos/minute
- **Twitter**: 50 tweets/day for free tier, 300 tweets/day for basic

### **Costs:**
- **Veo 3**: ~$0.10-0.50 per video (check current pricing)
- **GCS Storage**: ~$0.02/GB/month
- **Twitter API**: Free tier available, $100/month for Pro

### **Video Generation Time:**
- **Veo 3**: 60-90 seconds per video
- **UI needs**: Progress indicator, websocket updates

### **Error Handling:**
- Veo generation timeout (>5 min)
- Twitter API errors
- GCS upload failures
- Video format issues

---

## 🧪 Testing Strategy

### **Unit Tests:**
- Test `generate_action_line()` with various health data
- Test `create_veo_prompt()` output format
- Mock Veo 3 API responses
- Mock Twitter API responses

### **Integration Tests:**
- Test full agent chain (data → action line → prompt → video)
- Test video storage and retrieval
- Test Twitter posting with test account

### **User Acceptance Tests:**
- Generate PSA for different scenarios
- Verify video quality and messaging
- Test tweet formatting
- Verify hashtags are appropriate

---

## 📈 Success Metrics

- ✅ Video generation completes in <90 seconds
- ✅ Action lines are ≤12 words, 100% of time
- ✅ Videos properly formatted (8 sec, 1080x1920)
- ✅ Tweet posts successfully to Twitter
- ✅ User can validate before posting
- ✅ Appropriate hashtags generated

---

## 🚀 Implementation Timeline

**Day 1**: Backend agents and functions (Phase 1-2)
**Day 2**: Veo 3 integration and testing (Phase 5.2)
**Day 3**: Twitter integration (Phase 5.3)
**Day 4**: Flask endpoints (Phase 3)
**Day 5**: Frontend UI (Phase 4)
**Day 6**: Testing and debugging
**Day 7**: Deployment and documentation

**Estimated**: 7 days for full implementation

---

## 📝 Next Steps to Begin

1. ✅ Create feature branch `veo3-twitter` (DONE)
2. Review this plan
3. Set up GCS bucket for videos
4. Get Twitter API credentials
5. Test Veo 3 API access
6. Start implementing ActionLine agent
7. Build incrementally with tests

---

**This plan is ready to execute! Shall we begin with Step 1 - creating the ActionLine agent?** 🚀

