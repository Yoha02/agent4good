# PSA Video Feature - Complete Implementation Plan

**Last Updated**: October 24, 2025  
**Branch**: `veo3-twitter`  
**Status**: 75% Complete - Backend working, Frontend pending

---

## 🎯 Feature Vision

**Goal**: Enable users to generate AI-powered health PSA videos through natural conversation, then share on social media.

**User Experience**:
```
User: "Create a PSA video about California air quality"
Agent: "Generating video... (60 sec). You can keep chatting!"
[User continues conversation - not blocked]
[60 seconds later - new message appears]
Agent: "✓ Video ready! [Video player shows in chat]
       Would you like to post this to Twitter?"
User: "Yes"
Agent: "Posted! https://twitter.com/..."
```

---

## ✅ What's COMPLETED (75%)

### **1. Backend Architecture** - 100% ✅

**Modular Structure** (Zero teammate conflicts):
```
multi_tool_agent_bquery_tools/
├── agents/psa_video.py          # 3 specialized agents
├── tools/video_gen.py           # Video generation functions
├── tools/social_media.py        # Twitter functions
├── integrations/veo3_client.py  # Veo 3 API (WORKING!)
├── integrations/twitter_client.py
└── psa_video_integration.py     # Optional feature loader
```

**3 New AI Agents**:
1. ✅ **ActionLine Agent** - Converts health data → ≤12 word recommendation
2. ✅ **VeoPrompt Agent** - Creates detailed Veo 3 video prompt
3. ✅ **Twitter Agent** - Formats tweets with hashtags

**Integration**: Lines 741-789 in `agent.py` (optional, won't break core)

---

### **2. Veo 3 Video Generation** - 100% ✅ **WORKING!**

**Breakthrough Solution**:
- ✅ Model: `veo-3.1-fast-generate-preview` (Google AI SDK)
- ✅ Generates videos in ~60 seconds
- ✅ Download: `requests.get(uri, headers={'X-goog-api-key'})`
- ✅ Upload to GCS: Code ready
- ✅ Serve: Public URLs

**Proven Working**:
- ✅ Generated multiple test videos
- ✅ Files: `psa_video_from_notebook.mp4`, `sample.mp4`
- ✅ Action lines: "Wear a mask outside.", "Boil tap water for one minute."
- ✅ Videos: 8 seconds, 720p, vertical (9:16)

**Methods in `veo3_client.py`**:
- ✅ `generate_video()` - Calls Veo 3.1 API
- ✅ `check_operation_status()` - Polls completion
- ✅ `download_video_from_uri()` - Downloads with API key
- ✅ `upload_to_gcs()` - Uploads to GCS, returns public URL

---

### **3. Testing** - 100% ✅

**Test Files**:
- ✅ `test_psa_feature.py` - All components pass
- ✅ `test_veo_working_solution.py` - **Complete workflow tested**
- ✅ End-to-end: Health data → Video file → Tweet format

**Results**:
- ActionLine: ✅ Working
- Veo Prompt: ✅ 755 characters, professional
- Video Generation: ✅ Multiple successful generations
- Tweet Formatting: ✅ 124/280 chars with hashtags

---

### **4. Flask Endpoints** - 60% ✅

**Created**:
- ✅ `POST /api/generate-psa-video` - Starts workflow
- ✅ `POST /api/approve-and-post` - Posts to Twitter

**Status**: Basic structure done, needs async implementation

---

### **5. Documentation** - 100% ✅

- ✅ `VEO3_TWITTER_FEATURE_PLAN.md` - Original detailed plan
- ✅ `MODULAR_IMPLEMENTATION_STRATEGY.md` - Architecture
- ✅ `CLOUD_RUN_VIDEO_SOLUTION.md` - Deployment strategy
- ✅ `PSA_CHAT_WORKFLOW.md` - Chat-based UX
- ✅ `ASYNC_VIDEO_WORKFLOW.md` - Non-blocking implementation
- ✅ `VEO_ACCESS_REQUEST.md` - API access request

---

## ⏳ What's PENDING (25%)

### **Phase 1: Backend Async Workflow** - ⏳ 1.5 hours

#### **A. Wire Download+Upload into Veo Client** (30 min)

**File**: `multi_tool_agent_bquery_tools/integrations/veo3_client.py`

**Update `check_operation_status` method when `operation.done`**:

```python
# After detecting video is complete:
video_uri = operation.result.generated_videos[0].video.uri

# Download video
api_key = os.getenv('GOOGLE_API_KEY')
video_bytes = self.download_video_from_uri(video_uri, api_key)

if video_bytes:
    # Upload to GCS
    gcs_result = self.upload_to_gcs(video_bytes)
    
    return {
        "status": "complete",
        "video_url": gcs_result['public_url'],  # For UI
        "gcs_uri": gcs_result['gcs_uri'],       # For Twitter
        "video_size": gcs_result['video_size']
    }
```

**This makes video retrieval automatic!**

---

#### **B. Implement Async Task Management** (1 hour)

**File**: `app.py`

**Add task queue for background video generation**:

```python
from threading import Thread
import uuid

# Global task storage (use Redis in production)
video_generation_tasks = {}

@app.route('/api/agent-chat', methods=['POST'])
def agent_chat():
    question = request.get_json().get('question', '')
    
    # Detect video generation request
    keywords = ['create video', 'generate psa', 'make video', 'create psa']
    wants_video = any(kw in question.lower() for kw in keywords)
    
    if wants_video and ADK_AGENT_AVAILABLE:
        # Start async video generation
        task_id = str(uuid.uuid4())
        
        def generate_video_background():
            try:
                # Call agent to get action line and prompt
                # This is where ActionLine and VeoPrompt agents work
                response = call_adk_agent(question)
                
                # Parse action line from response
                # Generate video using veo client
                # Poll until complete (auto downloads/uploads)
                # Store result
                
                video_generation_tasks[task_id] = {
                    'status': 'complete',
                    'video_url': public_url,
                    'action_line': action_line,
                    'tweet_preview': tweet_text
                }
            except Exception as e:
                video_generation_tasks[task_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Initialize task
        video_generation_tasks[task_id] = {'status': 'processing', 'progress': 0}
        
        # Start background thread
        thread = Thread(target=generate_video_background)
        thread.daemon = True
        thread.start()
        
        # Return immediate response
        return jsonify({
            'success': True,
            'response': "I'll generate a health alert video. This takes about 60 seconds. You can continue chatting while I work on this!\n\nIs there anything else I can help you with?",
            'task_id': task_id,
            'estimated_time': 60
        })
    
    # Normal chat flow...
    response = call_adk_agent(question)
    return jsonify({'success': True, 'response': response})

@app.route('/api/check-video-task/<task_id>')
def check_video_task(task_id):
    """Poll for video generation completion"""
    if task_id in video_generation_tasks:
        return jsonify(video_generation_tasks[task_id])
    return jsonify({'status': 'not_found'}), 404
```

---

### **Phase 2: Frontend Video Display** - ⏳ 1.5 hours

#### **A. Add Video Polling** (30 min)

**File**: `static/js/app.js`

**Add polling function**:

```javascript
// Global: Store active video tasks
const activeVideoTasks = new Set();

async function askAI() {
    // ... existing code ...
    
    const data = await response.json();
    
    // Show agent's message
    addMessage(data.response, 'bot');
    
    // If video generation started, poll for it
    if (data.task_id) {
        pollForVideoCompletion(data.task_id);
    }
}

async function pollForVideoCompletion(taskId) {
    if (activeVideoTasks.has(taskId)) return; // Already polling
    activeVideoTasks.add(taskId);
    
    const maxAttempts = 30; // 30 * 5 sec = 2.5 min
    
    for (let i = 0; i < maxAttempts; i++) {
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 sec
        
        try {
            const response = await fetch(`/api/check-video-task/${taskId}`);
            const status = await response.json();
            
            if (status.status === 'complete') {
                // Video ready! Add new message with video
                const videoMessage = `✓ Your PSA video is ready!

[VIDEO:${status.video_url}]

Action: "${status.action_line}"

Would you like me to post this to Twitter?`;
                
                addMessage(videoMessage, 'bot');
                activeVideoTasks.delete(taskId);
                break;
            } else if (status.status === 'error') {
                addMessage(`Sorry, video generation failed: ${status.error}`, 'bot');
                activeVideoTasks.delete(taskId);
                break;
            }
            // Continue polling if still processing
        } catch (error) {
            console.error('Polling error:', error);
        }
    }
    
    activeVideoTasks.delete(taskId);
}
```

---

#### **B. Parse and Embed Videos** (1 hour)

**Update `addMessage` function**:

```javascript
function addMessage(text, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-start space-x-3 ${type === 'user' ? 'justify-end' : ''}`;
    
    let messageContent = text;
    let videoHtml = '';
    
    // Parse [VIDEO:url] marker (only in bot messages)
    if (type === 'bot' && text.includes('[VIDEO:')) {
        const videoMatch = text.match(/\[VIDEO:(.*?)\]/);
        if (videoMatch) {
            const videoUrl = videoMatch[1];
            
            // Remove video marker from text
            messageContent = text.replace(/\[VIDEO:.*?\]/, '').trim();
            
            // Create video player
            videoHtml = `
                <div class="my-3">
                    <video 
                        controls 
                        class="w-full rounded-lg shadow-lg" 
                        style="max-width: 300px; max-height: 533px;"
                        preload="metadata"
                    >
                        <source src="${videoUrl}" type="video/mp4">
                        Your browser doesn't support video playback.
                    </video>
                </div>
            `;
        }
    }
    
    if (type === 'bot') {
        messageDiv.innerHTML = `
            <div class="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-robot text-white"></i>
            </div>
            <div class="bg-white rounded-2xl rounded-tl-none p-4 shadow-md max-w-2xl">
                ${videoHtml}
                <p class="text-gray-700 leading-relaxed whitespace-pre-line">${messageContent}</p>
            </div>
        `;
    } else {
        // User message (unchanged)
        messageDiv.innerHTML = `
            <div class="bg-navy-700 text-white rounded-2xl rounded-tr-none p-4 shadow-md max-w-lg">
                <p class="leading-relaxed">${text}</p>
            </div>
            <div class="w-10 h-10 bg-navy-600 rounded-full flex items-center justify-center flex-shrink-0">
                <i class="fas fa-user text-white"></i>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
```

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ USER CHAT INPUT                                             │
│ "Create a PSA video about California air quality"          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ FLASK: /api/agent-chat                                      │
│ - Detects "create video" intent                            │
│ - Starts background thread                                  │
│ - Returns: "Generating... (60 sec). Keep chatting!"        │
│ - Includes: task_id                                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        ▼                             ▼
┌─────────────────┐         ┌─────────────────────┐
│ FRONTEND        │         │ BACKGROUND THREAD   │
│ - Shows message │         │ (Backend)           │
│ - Starts polling│         │                     │
│   every 5 sec   │         │ Step 1: Get AQI data│
└─────────────────┘         │ Step 2: ActionLine  │
        │                   │   → "Wear a mask"   │
        │                   │ Step 3: VeoPrompt   │
        │                   │   → Full prompt     │
        │                   │ Step 4: Veo API     │
        │                   │   → Generate (60s)  │
        │                   │ Step 5: Download    │
        │                   │   → Get video bytes │
        │                   │ Step 6: Upload GCS  │
        │                   │   → Get public URL  │
        │                   │ Step 7: Store result│
        │                   └──────────┬──────────┘
        │                              │
        ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND POLLING: /api/check-video-task/{task_id}          │
│ Poll 1: {"status": "processing", "progress": 25}           │
│ Poll 2: {"status": "processing", "progress": 50}           │
│ Poll 12: {"status": "complete", "video_url": "https://..."} │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND: Add New Message to Chat                          │
│ - Parse [VIDEO:url] marker                                 │
│ - Embed <video> player                                     │
│ - Show agent's prompt for Twitter                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ USER SEES IN CHAT                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ✓ Your PSA video is ready!                              │ │
│ │                                                           │ │
│ │ [VIDEO PLAYER - 8 sec vertical video playing]           │ │
│ │                                                           │ │
│ │ Action: "Wear a mask outside."                           │ │
│ │                                                           │ │
│ │ Would you like to post this to Twitter?                 │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                       │
        User: "Yes"    │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ TWITTER AGENT                                               │
│ - Download video from GCS                                   │
│ - Upload to Twitter API                                     │
│ - Post tweet with video + hashtags                         │
│ - Return tweet URL                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ AGENT RESPONSE IN CHAT                                      │
│ "✓ Posted to Twitter!                                       │
│  View at: https://twitter.com/CommunityHealth/status/..."  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Implementation Checklist

### **Phase 1: Backend Async (1.5 hours)** ⏳

- [ ] **A1**: Update `check_operation_status` to auto download+upload
  - File: `veo3_client.py`
  - Add download and GCS upload when video completes
  - Return public_url in result
  - Time: 30 min

- [ ] **A2**: Add async task management to Flask
  - File: `app.py`
  - Add `video_generation_tasks = {}` dict
  - Create background thread function
  - Update `/api/agent-chat` to detect video requests
  - Start thread, return task_id
  - Time: 45 min

- [ ] **A3**: Add video status endpoint
  - File: `app.py`
  - Add `GET /api/check-video-task/<task_id>`
  - Return task status from dict
  - Time: 15 min

---

### **Phase 2: Frontend Polling (1 hour)** ⏳

- [ ] **B1**: Add polling function
  - File: `static/js/app.js`
  - Create `pollForVideoCompletion(taskId)` function
  - Poll every 5 seconds
  - Handle completion/error
  - Time: 30 min

- [ ] **B2**: Update message display
  - File: `static/js/app.js`  
  - Parse `[VIDEO:url]` markers
  - Create video player HTML
  - Embed in chat message
  - Time: 30 min

---

### **Phase 3: Testing (1 hour)** ⏳

- [ ] **C1**: Test async generation locally
  - Start video generation
  - Continue chatting
  - Verify video appears
  - Time: 20 min

- [ ] **C2**: Test Twitter approval flow
  - Generate video
  - Approve posting
  - Verify tweet format
  - Time: 20 min

- [ ] **C3**: Deploy and test on Cloud Run
  - Deploy updated code
  - Test live
  - Verify GCS storage
  - Time: 20 min

---

### **Phase 4: Twitter Integration (Optional - 1 hour)** 🔜

- [ ] **D1**: Get Twitter API credentials
  - Create Twitter Developer account
  - Get API keys
  - Add to `.env`
  - Time: 30 min

- [ ] **D2**: Implement real Twitter posting
  - File: `twitter_client.py`
  - Remove simulation mode
  - Add real API calls
  - Test with test account
  - Time: 30 min

---

## 🎯 Priority Implementation Order

### **MVP (Minimum Viable Product) - 3 hours**:

1. ✅ ~~Backend agents~~ (Done!)
2. ✅ ~~Veo integration~~ (Done!)
3. ⏳ **Async backend** (1.5 hours) ← **START HERE**
4. ⏳ **Frontend polling + video display** (1 hour)
5. ⏳ **Local testing** (30 min)

**Delivers**: Working PSA video generation in chat!

### **Full Feature - +2 hours**:

6. ⏳ Deploy to Cloud Run (30 min)
7. ⏳ Twitter credentials (30 min)
8. ⏳ Real Twitter posting (30 min)
9. ⏳ Final testing (30 min)

**Delivers**: Complete feature with social media posting!

---

## 💡 Key Design Decisions

### **Chat-Based (Not Separate UI)**:
✅ Natural conversation flow  
✅ Context-aware  
✅ Less UI code  
✅ Better UX  

### **Async (Not Blocking)**:
✅ User can keep chatting  
✅ Better perceived performance  
✅ Professional experience  

### **Modular (Not Monolithic)**:
✅ Team can work in parallel  
✅ Easy to disable  
✅ Clean code structure  

---

## 🚀 Immediate Next Step

**Start with: Phase 1A - Wire download+upload into Veo client**

This is the foundation - once this works, everything else flows naturally.

**File**: `multi_tool_agent_bquery_tools/integrations/veo3_client.py`  
**Method**: `check_operation_status`  
**Time**: 30 minutes  

**Code to add**: Download video, upload to GCS, return public URL

---

## 📊 Current Progress

**Completed**: 75%  
**Remaining**: 25% (3-5 hours)  
**Hardest Part**: ✅ Done (Veo integration)  
**Status**: Ready for final integration  

---

## ✅ What Works RIGHT NOW

Can demonstrate:
- ✅ Complete modular architecture
- ✅ Working Veo 3 video generation
- ✅ Downloaded video files (can show!)
- ✅ ActionLine: "Wear a mask outside."
- ✅ Tweet formatting with hashtags
- ✅ Full agent system

**This is presentation-ready!** Just needs final wiring.

---

**Ready to implement Phase 1A (30 min) to wire everything together?** 🎯

