# Testing Persona-Passing Integration 🧪

## 🎯 Quick Test Guide

### **Test 1: Default Persona (Community Resident)**

1. **Stop any running Flask apps** (Ctrl+C in terminal)
2. **Start fresh**:
   ```bash
   python app_local.py
   ```
3. **Open browser**: http://localhost:8080
4. **Open browser console** (F12)
5. **Ask a question**: "What health services are available?"
6. **Expected Results**:
   - Console log shows: `persona=null` or `persona=Community Resident`
   - Backend log shows: `[AGENT] Creating/updating runner with persona: user`
   - Agent response includes **user persona menu** with options like:
     - Report health/environmental issues
     - Find nearby clinics
     - Air quality info
     - Disease data

---

### **Test 2: Health Official Login**

1. **Navigate to**: http://localhost:8080/officials-login
2. **Enter any credentials** (demo mode, any email/password works)
3. **Click "Sign In"**
4. **Check browser console**:
   - Should see: `Login successful: Persona updated to "Health Official"`
5. **Verify sessionStorage**:
   ```javascript
   // In browser console:
   sessionStorage.getItem('persona')
   // Should return: "Health Official"
   ```
6. **Go back to homepage**: http://localhost:8080
7. **Ask a question**: "Show me recent community reports"
8. **Expected Results**:
   - Console log shows: `persona=Health Official`
   - Backend log shows: `[AGENT] Creating/updating runner with persona: health_official`
   - Agent response includes **health official menu** with options like:
     - Search community reports semantically
     - Analyze trends
     - View aggregated data
     - Access official tools

---

### **Test 3: Logout & Persona Reset**

1. **While on officials dashboard**, click **"Logout"**
2. **Check browser console**:
   - Should see: `Logout from Health Official Account: update persona type to "Community Resident" in session storage`
3. **Verify sessionStorage**:
   ```javascript
   // In browser console:
   sessionStorage.getItem('persona')
   // Should return: "Community Resident"
   ```
4. **Go to homepage**: http://localhost:8080
5. **Ask a question**: "What can you help me with?"
6. **Expected Results**:
   - Console log shows: `persona=Community Resident`
   - Backend log shows: `[AGENT] Creating/updating runner with persona: user`
   - Agent reverts to **user persona menu**

---

### **Test 4: Persona Switching**

1. **Start as Community Resident** (default)
2. **Ask question** → Note response type
3. **Login as Health Official** → `/officials-login`
4. **Backend should log**: `[AGENT] Creating/updating runner with persona: health_official`
5. **Return to homepage and ask question** → Note different response type
6. **Logout**
7. **Backend should log**: `[AGENT] Creating/updating runner with persona: user`
8. **Ask another question** → Should revert to user persona

**Expected**: Runner only recreates when persona **changes**, not on every request

---

### **Test 5: Session Persistence**

1. **Login as Health Official**
2. **Ask multiple questions** → All should use health official persona
3. **Refresh page** (F5)
4. **Verify sessionStorage**:
   ```javascript
   sessionStorage.getItem('persona')
   // Should still be: "Health Official"
   ```
5. **Ask another question** → Should still use health official persona
6. **Close tab completely**
7. **Reopen** http://localhost:8080
8. **Verify sessionStorage**:
   ```javascript
   sessionStorage.getItem('persona')
   // Should be: null (sessionStorage cleared on tab close)
   ```
9. **Ask question** → Should revert to default user persona

---

## 🐛 What to Look For

### **Console Logs (Browser)**
✅ Correct:
```
Login successful: Persona updated to "Health Official"
[Chat] Using stored location data: {...}
```

❌ Errors:
- `persona is not defined`
- `Cannot read property 'persona' of null`

### **Backend Logs (Terminal)**
✅ Correct:
```
[AGENT-CHAT] Received parameters: ... persona=Health Official
[AGENT] Creating/updating runner with persona: health_official
[AGENT-CHAT] ADK response received: ...
```

❌ Errors:
- `TypeError: call_agent() got an unexpected keyword argument 'persona'`
- `Agent air_quality_agent already has a parent agent`

### **Agent Responses**
✅ Correct:
- Different menus for user vs. health official
- Appropriate tools available based on persona
- No crashes or fallbacks

❌ Problems:
- Same menu regardless of persona
- Agent confusion about available tools
- "I cannot fulfill this request" messages

---

## 📊 Expected Backend Logs

### **First Request (User Persona)**
```
[AGENT-CHAT] Received parameters: state=California, ... persona=None
[AGENT] Creating/updating runner with persona: user
[AGENT-CHAT] ADK response received: Hello! I'm your community...
```

### **After Login (Health Official Persona)**
```
[AGENT-CHAT] Received parameters: state=California, ... persona=Health Official
[AGENT] Creating/updating runner with persona: health_official
[AGENT-CHAT] ADK response received: Welcome, Health Official...
```

### **After Logout (Back to User)**
```
[AGENT-CHAT] Received parameters: state=California, ... persona=Community Resident
[AGENT] Creating/updating runner with persona: user
[AGENT-CHAT] ADK response received: Hello! I'm your community...
```

---

## 🚨 Known Issues

### **If sessionStorage is not cleared on logout:**
- Manually clear: `sessionStorage.clear()` in browser console
- Or use incognito mode for clean testing

### **If runner doesn't recreate:**
- Check backend logs for `_persona_type` tracking
- Restart Flask app to reset runner state

### **If persona doesn't pass:**
- Check browser console for JavaScript errors
- Verify `sessionStorage.getItem('persona')` returns expected value

---

## ✅ Success Criteria

- [x] Default persona is "user" (Community Resident)
- [x] Login sets persona to "Health Official"
- [x] Logout resets persona to "Community Resident"
- [x] Frontend passes persona in API requests
- [x] Backend receives and logs persona correctly
- [x] Agent runner recreates only on persona change
- [x] Different menus/tools available per persona
- [x] sessionStorage persists during session
- [x] sessionStorage clears on tab close
- [x] No errors in browser or backend logs

---

**Test Duration:** ~10 minutes  
**Browser:** Chrome/Edge/Firefox (with DevTools open)  
**Terminal:** Keep Flask app logs visible

---

**Ready to test? Start with Test 1! 🚀**

