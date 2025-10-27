# Chatbot Interface Integration Plan for Officials Dashboard

## 🎯 Goal
Add a chatbot interface to the `officials_dashboard.html` page that reuses the existing chatbot functionality from `index.html` and `app.js`.

---

## 📋 Current State Analysis

### **Main Page (`index.html`) - What We Have:**
1. **Chat UI Structure** (Lines 707-833):
   - Header with AI avatar and title
   - Scrollable messages container
   - Clear chat button
   - Voice selection dropdown
   - Input controls:
     - Microphone button (voice input)
     - Text input field
     - Speaker button (voice output toggle)
     - Send button
   - Location context display

2. **Chat Functionality in `app.js`**:
   - `askAI()` - Main function to send questions to backend
   - `addMessage(text, type)` - Add messages to chat UI
   - `clearChat()` - Reset chat history
   - `toggleVoiceInput()` - Microphone/speech recognition
   - `toggleSpeechOutput()` - Enable/disable text-to-speech
   - `speakText(text)` - Google Cloud TTS integration
   - `changeVoice(voiceName)` - Voice selection
   - `previewVoice()` - Test voice
   - Video generation polling and display
   - Twitter post approval

3. **Styling:**
   - Tailwind CSS with custom classes
   - Glass morphism effects
   - Responsive design
   - Smooth animations

### **Officials Dashboard (`officials_dashboard.html`) - Current Layout:**
1. **Top Navigation** (Lines 133-178):
   - Logo and title
   - Navigation links
   - Logout button

2. **Main Content** (Lines 181-726):
   - Welcome section
   - Filters section (location, time period)
   - Dashboard grid:
     - Critical alerts (2 columns)
     - Quick stats (1 column)
   - Charts section:
     - AQI chart
     - Disease chart
     - Time series chart
     - Location chart
   - Community reports table (full width)

3. **No chat interface currently exists**

---

## 🎨 Proposed Design

### **Option 1: Fixed Bottom-Right Chat Widget (Recommended)**
**Similar to live chat support widgets on websites**

**Pros:**
- ✅ Doesn't disrupt existing dashboard layout
- ✅ Always accessible
- ✅ Can be minimized/expanded
- ✅ Floats above content
- ✅ Mobile-friendly

**Visual:**
```
┌──────────────────────────────────────────────┐
│  Navigation Bar                              │
├──────────────────────────────────────────────┤
│  Filters                                     │
├──────────────────────────────────────────────┤
│  Dashboard Content                           │
│  ┌─────────┐  ┌─────────┐                   │
│  │ Alerts  │  │  Stats  │          ┌────────┐
│  └─────────┘  └─────────┘          │        │
│  ┌─────────┐  ┌─────────┐          │  Chat  │
│  │ Charts  │  │ Charts  │          │ Widget │
│  └─────────┘  └─────────┘          │        │
│  ┌──────────────────────┐          └────────┘
│  │  Reports Table       │         (Expandable)
│  └──────────────────────┘
└──────────────────────────────────────────────┘
```

---

### **Option 2: Dedicated Chat Tab in Navigation**
**Add "AI Assistant" tab that shows full-screen chat**

**Pros:**
- ✅ Full-screen chat experience
- ✅ Separate from data views
- ✅ Can include all chat features

**Cons:**
- ❌ Requires navigation away from dashboard
- ❌ Can't monitor data while chatting

---

### **Option 3: Slide-Out Panel**
**Chat panel slides in from right side**

**Pros:**
- ✅ Doesn't obstruct view when closed
- ✅ More space than widget
- ✅ Modern UI pattern

**Cons:**
- ❌ Partially covers dashboard when open
- ❌ More complex implementation

---

## ✅ Recommended Approach: Option 1 (Fixed Bottom-Right Widget)

### **Why This Works Best:**
1. Officials can ask questions **while viewing data**
2. Non-intrusive - minimizes when not in use
3. Quick access - always one click away
4. Familiar UX pattern (like customer support chats)
5. Can use **Health Official persona** automatically

---

## 🛠️ Implementation Plan

### **Step 1: Create Reusable Chat Component** 
**File:** `static/js/chat-widget.js` (NEW)

**Purpose:** Extract chatbot functions from `app.js` into a reusable module

**Functions to Extract:**
- `createChatWidget(containerElement, options)` - Initialize chat UI
- `askAIChatWidget()` - Send message
- `addMessageWidget(text, type)` - Display message
- `clearChatWidget()` - Reset
- Voice controls (optional for officials dashboard)

**Options:**
```javascript
{
    persona: 'Health Official',  // or 'Community Resident'
    enableVoice: false,           // Disable for officials (office setting)
    enableVideo: true,            // Allow PSA video generation
    welcomeMessage: 'Custom welcome for officials',
    theme: 'professional'         // vs 'casual' for main page
}
```

---

### **Step 2: Add Chat Widget HTML to Officials Dashboard**
**File:** `templates/officials_dashboard.html`

**Location:** Before `</body>` tag (Line ~1425)

**Structure:**
```html
<!-- Chat Widget Toggle Button (Always Visible) -->
<button id="chatToggleBtn" class="fixed bottom-6 right-6 z-50 ...">
    <i class="fas fa-comments"></i>
    <span class="badge">AI Assistant</span>
</button>

<!-- Chat Widget Container (Hidden by default) -->
<div id="chatWidget" class="fixed bottom-6 right-6 z-50 hidden ...">
    <!-- Chat Header -->
    <div class="chat-header">
        <h4>Health Official AI Assistant</h4>
        <button onclick="minimizeChatWidget()">-</button>
        <button onclick="closeChatWidget()">×</button>
    </div>
    
    <!-- Chat Messages -->
    <div id="chatWidgetMessages" class="chat-messages"></div>
    
    <!-- Chat Input -->
    <div class="chat-input">
        <input type="text" id="chatWidgetInput" placeholder="Ask about reports, trends, or get recommendations..." />
        <button onclick="sendChatWidgetMessage()">
            <i class="fas fa-paper-plane"></i>
        </button>
    </div>
</div>
```

**Dimensions:**
- Minimized button: 60px × 60px (bottom-right)
- Expanded widget: 400px × 600px (bottom-right)
- Mobile: Full screen overlay

---

### **Step 3: Add Chat Widget Styles**
**File:** `templates/officials_dashboard.html` (in `<style>` section)

**Styles:**
```css
/* Chat Widget */
#chatToggleBtn {
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #10b981, #059669);
    border-radius: 30px;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    transition: all 0.3s;
}

#chatToggleBtn:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
}

#chatWidget {
    width: 400px;
    height: 600px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

#chatWidget.minimized {
    height: 60px;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    background: #f9fafb;
}

/* Mobile responsive */
@media (max-width: 768px) {
    #chatWidget {
        width: calc(100vw - 32px);
        height: calc(100vh - 100px);
        bottom: 16px;
        right: 16px;
    }
}
```

---

### **Step 4: Add Chat Widget JavaScript**
**File:** `static/js/officials-dashboard.js`

**Add at the end:**
```javascript
// ========================================
// CHAT WIDGET FUNCTIONALITY
// ========================================

let chatWidgetOpen = false;

function toggleChatWidget() {
    const widget = document.getElementById('chatWidget');
    const button = document.getElementById('chatToggleBtn');
    
    chatWidgetOpen = !chatWidgetOpen;
    
    if (chatWidgetOpen) {
        widget.classList.remove('hidden');
        button.classList.add('hidden');
        initializeChatWidget();
    } else {
        widget.classList.add('hidden');
        button.classList.remove('hidden');
    }
}

function initializeChatWidget() {
    const messagesDiv = document.getElementById('chatWidgetMessages');
    if (messagesDiv.children.length === 0) {
        addChatMessage(
            'Hello! I'm your Health Official AI Assistant. I can help you analyze community reports, identify trends, and provide data-driven recommendations.',
            'bot'
        );
    }
}

async function sendChatWidgetMessage() {
    const input = document.getElementById('chatWidgetInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    // Add user message
    addChatMessage(question, 'user');
    input.value = '';
    
    // Show loading
    const loadingMsg = addChatMessage('Analyzing...', 'bot');
    
    try {
        // Get current location filters
        const locationContext = {
            state: currentFilters.state,
            city: currentFilters.city,
            county: currentFilters.county,
            zipCode: currentFilters.zipcode
        };
        
        // Call AI agent with Health Official persona
        const response = await fetch('/api/agent-chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                location_context: locationContext,
                persona: 'Health Official',  // Always use Health Official persona
                state: currentFilters.state,
                days: 30  // Default to 30 days for officials
            })
        });
        
        const data = await response.json();
        
        // Remove loading
        loadingMsg.remove();
        
        if (data.success) {
            addChatMessage(data.response, 'bot');
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    } catch (error) {
        loadingMsg.remove();
        console.error('Chat widget error:', error);
        addChatMessage('Sorry, I could not connect to the AI service.', 'bot');
    }
}

function addChatMessage(text, type) {
    const messagesDiv = document.getElementById('chatWidgetMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message chat-message-${type}`;
    
    if (type === 'bot') {
        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">${text}</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-content">${text}</div>
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
    }
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    return messageDiv;
}

function clearChatWidget() {
    const messagesDiv = document.getElementById('chatWidgetMessages');
    messagesDiv.innerHTML = '';
    initializeChatWidget();
}

function minimizeChatWidget() {
    const widget = document.getElementById('chatWidget');
    widget.classList.toggle('minimized');
}

function closeChatWidget() {
    toggleChatWidget();
}

// Event listeners
document.getElementById('chatToggleBtn')?.addEventListener('click', toggleChatWidget);
document.getElementById('chatWidgetInput')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendChatWidgetMessage();
});
```

---

### **Step 5: Connect to Existing Backend**
**No changes needed!** The existing `/api/agent-chat` endpoint already supports:
- ✅ `persona` parameter (we'll pass `"Health Official"`)
- ✅ `location_context` (from dashboard filters)
- ✅ All agent capabilities

---

### **Step 6: Enhanced Features for Officials**

**Context-Aware Queries:**
- Automatically include current dashboard filters (state, city, time period)
- Pass report statistics to AI for better context

**Quick Actions:**
```javascript
const quickActions = [
    'Summarize critical reports',
    'What are the top health trends?',
    'Analyze reports from last week',
    'Generate PSA video for current alerts',
    'Search reports about respiratory issues'
];
```

**Display these as clickable chips above the input field**

---

## 📊 Feature Comparison

| Feature | Main Page Chat | Officials Dashboard Chat |
|---------|---------------|--------------------------|
| **Layout** | Full section | Bottom-right widget |
| **Persona** | Community Resident | Health Official |
| **Voice Input** | ✅ Yes | ❌ No (office setting) |
| **Voice Output** | ✅ Yes | ❌ No (office setting) |
| **Video Generation** | ✅ Yes | ✅ Yes (PSA videos) |
| **Quick Actions** | ❌ No | ✅ Yes (report queries) |
| **Context** | User location | Dashboard filters |
| **Welcome Message** | Casual/helpful | Professional/analytical |
| **Priority** | Health info | Data analysis |

---

## 🎯 Code Reuse Strategy

### **What We'll Reuse:**
1. ✅ `askAI()` logic (with modifications for widget)
2. ✅ `addMessage()` structure (with widget-specific styling)
3. ✅ API call structure to `/api/agent-chat`
4. ✅ Persona passing mechanism
5. ✅ Error handling patterns
6. ✅ Video generation and display logic

### **What We'll Modify:**
1. 🔧 Remove voice features (not suitable for office)
2. 🔧 Simplify UI (compact widget vs. full section)
3. 🔧 Add quick action buttons
4. 🔧 Auto-fill location context from dashboard filters
5. 🔧 Change welcome message and persona

### **What We'll Add:**
1. ➕ Toggle/minimize/close functionality
2. ➕ Widget positioning and animations
3. ➕ Mobile-responsive full-screen mode
4. ➕ Integration with dashboard filter state
5. ➕ Professional styling

---

## 📝 Implementation Steps Summary

1. **Step 1:** Add HTML structure for chat widget
2. **Step 2:** Add CSS styles for widget
3. **Step 3:** Copy and adapt chat functions to `officials-dashboard.js`
4. **Step 4:** Connect to dashboard filter state
5. **Step 5:** Test with Health Official persona
6. **Step 6:** Add quick action buttons
7. **Step 7:** Test on mobile
8. **Step 8:** Polish animations and UX

---

## ⏱️ Estimated Time
- **Step 1-2 (HTML/CSS):** 30 minutes
- **Step 3 (JavaScript):** 45 minutes
- **Step 4-6 (Integration/Features):** 30 minutes
- **Step 7-8 (Testing/Polish):** 30 minutes
- **Total:** ~2.5 hours

---

## 🚀 Benefits

### **For Health Officials:**
1. ✅ **Contextual Analysis**: Ask questions about current filtered data
2. ✅ **Quick Insights**: Get summaries without leaving dashboard
3. ✅ **Report Search**: Semantic search through community reports
4. ✅ **Trend Detection**: AI identifies patterns in data
5. ✅ **PSA Generation**: Create public health announcements
6. ✅ **Always Accessible**: Widget stays available while viewing charts

### **For Development:**
1. ✅ **Code Reuse**: 70% of chat functionality already exists
2. ✅ **Modular**: Widget can be added to other pages
3. ✅ **No Backend Changes**: Uses existing API endpoints
4. ✅ **Maintainable**: Separated widget code from main app logic

---

## 🎨 Visual Mockup

### **Minimized State:**
```
Dashboard Content
                                    ┌────────┐
                                    │   💬   │
                                    │  Chat  │
                                    └────────┘
```

### **Expanded State:**
```
Dashboard Content (slightly dimmed)
                    ┌──────────────────────────┐
                    │ 🤖 Health Official AI    │ ─┐
                    ├──────────────────────────┤  │
                    │ Bot: Hello! I can help   │  │
                    │      with reports...     │  │
                    │                          │  │ 600px
                    │ You: What are top trends?│  │
                    │                          │  │
                    │ Bot: Based on current... │  │
                    ├──────────────────────────┤  │
                    │ [Quick Actions]          │  │
                    │ ┌────────────────────┐   │  │
                    │ │ Type message...    │📤 │  │
                    │ └────────────────────┘   │ ─┘
                    └──────────────────────────┘
                         400px (mobile: full)
```

---

## ✅ Acceptance Criteria

- [ ] Chat widget appears in bottom-right corner
- [ ] Toggle button shows/hides widget
- [ ] Minimize button collapses widget to header only
- [ ] Close button hides widget completely
- [ ] Messages display correctly (user right, bot left)
- [ ] AI responds with Health Official persona
- [ ] Dashboard filter context is passed to AI
- [ ] Quick action buttons work
- [ ] Enter key sends message
- [ ] Scrolling works in message area
- [ ] Mobile: Widget goes full-screen
- [ ] No console errors
- [ ] Accessible via keyboard navigation

---

**Ready to implement?** Let's start with Step 1! 🚀

