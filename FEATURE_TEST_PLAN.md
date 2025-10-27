# 🧪 Feature Testing Plan

## 🎯 **Test Objectives**

Verify ALL critical features work in BOTH chat interfaces (Main Page + Officials Dashboard)

---

## ✅ **Test Checklist**

### **1. Main Page Chat (Community Resident)**

#### 1.1 Location Context ✅
- [ ] Test with ZIP code
- [ ] Test with city + state
- [ ] Test with full location object
- [ ] Verify location appears in messages

#### 1.2 Persona System ✅
- [ ] Verify persona defaults to "Community Resident"
- [ ] Test persona passing to backend
- [ ] Check that agent recognizes correct role

#### 1.3 Environmental Data ✅
- [ ] Air quality data loads correctly
- [ ] Weather data displays
- [ ] Historical data shows trends
- [ ] Real-time vs historical distinction

#### 1.4 Chat Functionality ✅
- [ ] Send message
- [ ] Receive response
- [ ] Message appears in chat
- [ ] Multiple messages work

---

### **2. Officials Dashboard Chat (Health Official)**

#### 2.1 Persona System ✅
- [ ] Login as health official
- [ ] Verify persona = "Health Official"
- [ ] Test agent recognizes role with tools
- [ ] Logout returns to Community Resident

#### 2.2 Chat Widget ✅
- [ ] Chat toggle button appears
- [ ] Chat widget opens
- [ ] Input box visible
- [ ] Input box doesn't disappear
- [ ] Can send messages

#### 2.3 Video Generation ✅
- [ ] Request PSA video
- [ ] Video task created
- [ ] Status shows "generating_video"
- [ ] Status updates correctly
- [ ] Completes with video URL
- [ ] All statuses recognized (initializing, generating_action_line, creating_prompt, generating_video, processing, complete)

#### 2.4 Twitter Posting ✅
- [ ] Post button appears after video
- [ ] Click post to Twitter
- [ ] Retry logic works (3 attempts)
- [ ] Success message shows
- [ ] Tweet URL displays
- [ ] Tweet URL wraps correctly in message box
- [ ] No duplicate posts (flag prevents)

#### 2.5 Quick Actions ✅
- [ ] Quick action buttons work
- [ ] Pre-populate questions
- [ ] Send message with quick action

#### 2.6 Location Context ✅
- [ ] Dashboard filters update chat location
- [ ] State filter passed to chat
- [ ] City filter passed to chat
- [ ] County filter passed to chat

---

### **3. Enhanced Features (New)**

#### 3.1 CDC Data Endpoints ✅
- [ ] /api/wildfires
- [ ] /api/covid
- [ ] /api/respiratory
- [ ] /api/respiratory-timeseries
- [ ] /api/respiratory-disease-rates
- [ ] /api/covid-hospitalizations
- [ ] /api/infectious-disease-dashboard
- [ ] /api/alerts

#### 3.2 Improved Context Formatting ✅
- [ ] Context shows "CURRENT REAL-TIME AIR QUALITY DATA"
- [ ] Historical data marked separately
- [ ] Priority labels work
- [ ] AI uses correct data sources

#### 3.3 County Filtering ✅
- [ ] County parameter extracted
- [ ] Passed to BigQuery
- [ ] Filtering works correctly

---

## 🔍 **Testing Commands**

### **Manual Testing:**

1. **Start the app:**
   ```bash
   python app_local.py
   ```

2. **Open browser:**
   - Main page: `http://localhost:8080/`
   - Officials login: `http://localhost:8080/officials-login`
   - Officials dashboard: `http://localhost:8080/officials-dashboard`

3. **Test scenarios:**
   - Send chat messages
   - Request PSA videos
   - Post to Twitter
   - Check console logs
   - Monitor network requests

---

## 📊 **Expected Results**

### **✅ All Features Should Work:**
- ✅ No errors in console
- ✅ No UnboundLocalError
- ✅ No "message is required" errors
- ✅ No connection reset errors
- ✅ Twitter URLs wrap correctly
- ✅ Input boxes stay visible
- ✅ Video generation completes
- ✅ All personas work correctly

---

**Ready to test! 🚀**

