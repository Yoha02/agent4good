# 🧪 Agent Workflow Visualization - Testing Guide

## 🚀 Quick Start

### **1. Start the Application**

```bash
cd /Users/abhiram/Desktop/projects/a2i/agent4good
python app.py
```

### **2. Open in Browser**

Navigate to: `http://localhost:5000`

---

## 🎯 Test Scenarios

### **Test 1: Basic Agent Workflow** ✅

1. **Scroll down** to the "AI-Powered Health Advisor" chat section
2. **Look for** the green button that says **"Show Agent Workflow [NEW]"**
3. **Type a question:** "What's the air quality in California?"
4. **Press Send** or hit Enter

**Expected Result:**
- ✅ Panel automatically opens
- ✅ You see steps appearing in real-time:
  - ▶️ "Starting..." (blue)
  - 🤖 "Air Quality Agent" (emerald with pulsing dot)
  - 🔧 "Tool: Get Air Quality" (purple)
  - ✅ "Complete" (green)
- ✅ Final response appears in chat
- ✅ Smooth animations on each step

---

### **Test 2: Toggle Panel** ✅

1. **Click** the "Hide Agent Workflow" button
2. **Panel should close** smoothly
3. **Ask another question:** "What's the COVID rate?"
4. **Panel should auto-open** and show new workflow

**Expected Result:**
- ✅ Panel closes with animation
- ✅ Button text changes to "Show Agent Workflow"
- ✅ Panel reopens automatically on new query
- ✅ Previous workflow is cleared

---

### **Test 3: Multiple Agent Types** ✅

Try different questions that trigger different agents:

#### **Air Quality Agent:**
```
"Show me air quality data for San Francisco"
```
**Expected:** 🤖 Air Quality Agent → 🔧 Get Air Quality

#### **Disease Agent:**
```
"What's the flu rate in California?"
```
**Expected:** 🤖 Infectious Diseases Agent → 🔧 Get Disease Data

#### **Health FAQ Agent:**
```
"What are the symptoms of respiratory illness?"
```
**Expected:** 🤖 Health FAQ Agent

#### **Analytics Agent:**
```
"Show me correlations between air quality and disease rates"
```
**Expected:** 🤖 Analytics Agent → Multiple tool calls

---

### **Test 4: Complex Multi-Agent Query** ✅

**Question:**
```
"Compare air quality and COVID rates in California over the last 30 days"
```

**Expected Workflow:**
- ▶️ Starting
- 🤖 Root Agent
- 🤖 Analytics Agent (activated)
- 🔧 Get Air Quality
- 🔧 Get Disease Data
- 🧠 Processing (agent thinking)
- ✅ Complete

---

### **Test 5: Video Generation** 🎥

**Question:**
```
"Create a PSA video about air quality in California"
```

**Expected Workflow:**
- ▶️ Starting
- 🤖 PSA Video Agent
- 🔧 Video Generation Tool
- 🧠 Processing (this takes ~60 seconds)
- ✅ Complete

**Note:** The workflow panel shows the agent handoff, then you'll see a separate polling message for video generation.

---

### **Test 6: Error Handling** ⚠️

**Question:**
```
"Show me air quality for InvalidPlace123456789"
```

**Expected Result:**
- ✅ Workflow starts normally
- ⚠️ Error step appears (red) if data not found
- ✅ Error message in chat
- ✅ Panel remains functional for next query

---

### **Test 7: Scrolling & Timestamps** 📜

1. **Ask a complex question** that generates many steps
2. **Panel should auto-scroll** to show latest events
3. **Each step should show** a timestamp (HH:MM:SS)
4. **Hover over steps** to see hover effects

**Expected:**
- ✅ Auto-scroll works smoothly
- ✅ All timestamps are accurate
- ✅ Hover effect: step slides right with shadow
- ✅ Custom emerald scrollbar appears

---

## 🎨 Visual Checks

### **Colors**
- ✅ Start events: **Blue**
- ✅ Agent active: **Emerald/Green**
- ✅ Tool calls: **Purple**
- ✅ Thinking: **Amber/Yellow**
- ✅ Complete: **Green**
- ✅ Error: **Red**

### **Animations**
- ✅ Steps fade in from bottom
- ✅ Elastic bounce effect on entry
- ✅ Smooth panel open/close
- ✅ Pulsing dots for active agents

### **Typography**
- ✅ Agent names are clean (no underscores)
- ✅ Tool names are readable
- ✅ Timestamps are formatted properly
- ✅ Status messages are clear

---

## 🔍 Browser Console Checks

### **Open Developer Tools** (F12 or Cmd+Opt+I)

### **Console Tab - Look for:**
```
[Chat Stream] Using stored location data: {...}
[Stream Event] {type: 'start', ...}
[Stream Event] {type: 'agent_active', agent: 'air_quality_agent', ...}
[Stream Event] {type: 'tool_call', tool: 'get_air_quality', ...}
[Stream Event] {type: 'final_response', content: '...'}
```

### **Network Tab - Look for:**
- Request to `/api/agent-chat-stream` (POST)
- Type: `text/event-stream`
- Status: `200 OK`
- Response streaming in real-time

### **No Errors:**
- ❌ No red errors in console
- ❌ No failed network requests
- ❌ No JavaScript exceptions

---

## 📱 Mobile/Responsive Test

### **Resize Browser Window**

1. **Make window narrow** (< 768px)
2. **Panel should still work**
3. **Scrolling should be smooth**
4. **Button should be visible**

**Expected:**
- ✅ Panel adjusts to narrow width
- ✅ Steps remain readable
- ✅ Touch scrolling works
- ✅ No horizontal overflow

---

## 🐛 Known Behaviors (Not Bugs)

### **1. Panel Auto-Opens**
When you send a message with streaming enabled, the panel **automatically opens**. This is intentional to show the workflow.

**To disable:** Set `useStreaming = false` in `app.js` line 1577

### **2. Video Generation**
Video generation may show fewer workflow steps because it uses a different async pattern. This is normal.

### **3. Thinking Steps**
Some agents may not emit "thinking" events. This depends on the ADK framework's event emission.

### **4. Fast Queries**
For very fast queries (< 1 second), some steps may appear almost instantly. This is expected.

---

## 🎯 Performance Checks

### **Test with 10 consecutive queries:**

1. Send 10 different questions quickly
2. Check if panel updates correctly each time
3. Check memory usage in browser

**Expected:**
- ✅ Each query clears previous workflow
- ✅ No memory leaks
- ✅ Browser remains responsive
- ✅ Animations stay smooth

---

## 🔧 Troubleshooting

### **Problem: Panel doesn't open**

**Solutions:**
1. Check console for JavaScript errors
2. Verify `useStreaming = true` in app.js
3. Check if button exists with ID `workflowToggleBtn`
4. Try manually clicking "Show Agent Workflow"

### **Problem: No events appear**

**Solutions:**
1. Check Network tab for `/api/agent-chat-stream` request
2. Verify ADK agent is loaded (check startup logs)
3. Check Python logs for `[ROOT AGENT STREAM]` messages
4. Try a simple question like "Hello"

### **Problem: Streaming endpoint fails**

**Solutions:**
1. Check if `call_adk_agent_stream` was imported in app.py
2. Verify Python dependencies are installed
3. Check if agent.py has the new function
4. Look for Python exceptions in terminal

### **Problem: Animations don't work**

**Solutions:**
1. Verify anime.js is loaded (check Network tab)
2. Check console for anime-related errors
3. Animations are optional - functionality still works
4. Try hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

---

## ✅ Acceptance Criteria

### **Feature is working if:**

- [x] Panel appears below chat input
- [x] Toggle button is visible with "NEW" badge
- [x] Clicking toggle shows/hides panel
- [x] Sending a message auto-opens panel
- [x] Events appear in real-time during agent processing
- [x] Events are color-coded correctly
- [x] Timestamps are accurate
- [x] Final response appears in chat
- [x] Panel can be closed and reopened
- [x] No console errors
- [x] Animations are smooth
- [x] Works for different types of queries

---

## 🎉 Success Indicators

**You'll know it's working perfectly when:**

1. **Visual Flow** - You can literally watch the AI thinking
2. **Real-Time Updates** - Events appear as they happen (not all at once)
3. **Beautiful Animations** - Smooth, elastic entrance animations
4. **Color Coordination** - Different colors for different event types
5. **Professional Polish** - Looks like a production feature

---

## 📊 Test Results Template

```markdown
## Test Session: [Date/Time]

### Environment
- Browser: [Chrome/Firefox/Safari]
- OS: [macOS/Windows/Linux]
- Screen: [Desktop/Mobile]

### Test 1: Basic Workflow ✅/❌
- Panel opens: ✅
- Events appear: ✅
- Animations work: ✅
- Response displays: ✅

### Test 2: Toggle Panel ✅/❌
- Opens smoothly: ✅
- Closes smoothly: ✅
- State persists: ✅

### Test 3: Multiple Agents ✅/❌
- Air Quality: ✅
- Diseases: ✅
- Analytics: ✅

### Issues Found
1. [None / Describe issue]

### Overall: PASS ✅ / FAIL ❌
```

---

## 🎬 Demo Script

**For showing this to others:**

> "Let me show you something cool. When you ask the AI a question, you can now see exactly what's happening behind the scenes."
> 
> *Clicks "Show Agent Workflow"*
> 
> "Watch this panel as I ask about air quality..."
> 
> *Types: "What's the air quality in California?"*
> 
> "See? The system is:
> 1. Starting the workflow
> 2. Activating the Air Quality agent
> 3. Calling the data retrieval tool
> 4. Processing the response
> 5. Delivering the final answer
> 
> All of this happens in real-time with beautiful animations. It's not just a loading spinner - you can see exactly which AI agent is working and what tools they're using.
> 
> This makes the AI transparent and trustworthy. Users can learn how multi-agent systems work just by using the chat!"

---

## 🚀 Next Steps

**If testing is successful:**

1. ✅ Deploy to staging environment
2. ✅ Gather user feedback
3. ✅ Consider adding D3.js graph visualization
4. ✅ Add performance metrics (timing)
5. ✅ Create user documentation

**If issues are found:**

1. 🐛 Document the issue
2. 🔍 Check console and logs
3. 🛠️ Fix and retest
4. ✅ Verify fix works

---

*Ready to test? Start with Test 1 and work through the scenarios!* 🎯

*Questions? Check the main implementation doc: `AGENT_WORKFLOW_VISUALIZATION_COMPLETE.md`*


