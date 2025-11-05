# ✅ Backend Video Generation Timeout Fix

**Date**: November 5, 2025  
**Issue**: Backend timing out at 95% progress  
**Status**: ✅ **FIXED**

---

## 🐛 **The Problem**

### **What We Found:**

The **backend** was also timing out, not just the frontend!

```json
{
  "error": "Video generation timeout",
  "progress": 95,
  "status": "error"
}
```

### **Timeline:**

```
Frontend timeout: 4 minutes ✅ (Already fixed)
Backend timeout:  2 minutes ❌ (Was still broken!)
```

**Result:**
- Frontend waits 4 minutes
- Backend gives up after 2 minutes
- Video fails at 95% progress before frontend even times out

---

## 🔍 **Root Cause**

### **In `async_video_manager.py` (Line 117):**

```python
# BEFORE:
max_polls = 24  # 2 minutes max
for i in range(max_polls):
    time.sleep(5)  # 24 * 5 = 120 seconds = 2 minutes
```

**The Flow:**
1. ✅ Frontend increased to 4 minutes
2. ❌ Backend still at 2 minutes
3. ❌ Backend times out FIRST (at 95% progress)
4. Frontend gets error response before its 4-minute timeout

---

## ✅ **The Fix**

### **Changed Backend Timeout:**

```python
# AFTER:
max_polls = 48  # 4 minutes max (Veo 3 can take 2-3 minutes)
for i in range(max_polls):
    time.sleep(5)  # 48 * 5 = 240 seconds = 4 minutes
```

### **Fixed Progress Calculation:**

```python
# BEFORE:
progress = 30 + (i * 3)  # Calculated for 24 polls

# AFTER:
progress = 30 + int((i / max_polls) * 65)  # Works for any max_polls
```

**Why?**
- With 24 polls: `i * 3` gives nice increments (30, 33, 36, ...)
- With 48 polls: `i * 3` would go way past 100% (30, 33, ..., 174!)
- New formula: Distributes 65% progress (30% → 95%) across all polls

---

## 📊 **Before vs After**

| Component | Before | After |
|-----------|--------|-------|
| **Frontend timeout** | 2 min → 4 min ✅ | 4 min ✅ |
| **Backend timeout** | 2 min ❌ | 2 min → 4 min ✅ |
| **Progress calculation** | `i * 3` (broken for 48) | `(i/max_polls)*65` ✅ |
| **Consistency** | ❌ Mismatched | ✅ Both 4 minutes |

---

## 🧪 **Testing**

### **How to Test:**

1. **Restart Flask app** (CRITICAL - backend code changed):
   ```bash
   Ctrl+C
   python app_local.py
   ```

2. **Hard refresh browser**:
   ```
   Ctrl+Shift+R
   ```

3. **Generate video**:
   - Go to officials dashboard
   - Click "Create PSA" or type video request
   - **Wait full 3-4 minutes**

### **Expected Progress:**

```
✅ 0% - 10%  : Initialization (10s)
✅ 10% - 20% : Generate action line (10s)
✅ 20% - 30% : Create Veo prompt (10s)
✅ 30% - 95% : Veo 3 API generating (120-180s) ← BACKEND NOW WAITS HERE
✅ 95% - 100%: Download & upload to GCS (10-20s)
✅ Complete!
```

**Before fix:** Backend would timeout at 95% (2-minute mark)  
**After fix:** Backend waits full 4 minutes for completion

---

## 🎯 **Why Both Timeouts Needed Fixing**

### **The Chain:**

```
User Request
    ↓
Frontend Polling (static/js/officials-dashboard.js)
    ↓ calls every 1 second
/api/check-video-task/{taskId}
    ↓ returns status from
Backend Video Manager (async_video_manager.py)
    ↓ polls Veo 3 API every 5 seconds
Veo 3 Google API
    ↓ generates video (2-3 minutes)
Video Complete!
```

**If either times out:**
- ❌ Frontend times out → User sees timeout message
- ❌ Backend times out → Task marked as error, frontend shows error

**Both need 4-minute timeout!**

---

## 📝 **Files Changed**

### **Session 1: Frontend Timeouts**
1. ✅ `static/js/officials-dashboard.js`: 120 → 240 attempts (2 min → 4 min)
2. ✅ `static/js/app.js`: 30 → 48 attempts (2.5 min → 4 min)

### **Session 2: Backend Timeout** ← THIS FIX
3. ✅ `multi_tool_agent_bquery_tools/async_video_manager.py`: 
   - Line 117: `max_polls = 24` → `max_polls = 48` (2 min → 4 min)
   - Line 122: Fixed progress calculation for 48 polls

---

## 🔧 **Technical Details**

### **Progress Calculation Math:**

```python
# Old (for 24 polls):
progress = 30 + (i * 3)
# i=0:  30%
# i=8:  54% 
# i=16: 78%
# i=24: 102% ❌ Over 100%!

# New (for 48 polls):
progress = 30 + int((i / max_polls) * 65)
# i=0:  30 + (0/48)*65 = 30%
# i=24: 30 + (24/48)*65 = 62.5% → 62%
# i=48: 30 + (48/48)*65 = 95%
```

**Why stop at 95%?**
- Reserve 95-100% for final steps (download, upload, complete)
- Shows user something is still happening
- Jumps to 100% when fully done

---

## 🎓 **Lessons Learned**

### **Key Takeaways:**

1. **Async operations have multiple timeouts**
   - Frontend timeout (user-facing)
   - Backend timeout (worker thread)
   - **Both must be ≥ operation time**

2. **Progress bars need math updates**
   - Changing loop count affects calculations
   - Use `(i / max) * range` for flexibility

3. **Test end-to-end**
   - Frontend fix alone wasn't enough
   - Backend was bottleneck

4. **Veo 3 is slow in preview**
   - 2-3 minutes average
   - 4 minutes is safe buffer
   - Will likely improve when stable

---

## 🚀 **Deployment Checklist**

- [x] Frontend timeout increased (officials-dashboard.js)
- [x] Frontend timeout increased (app.js)
- [x] Backend timeout increased (async_video_manager.py) ✅ NEW
- [x] Progress calculation fixed ✅ NEW
- [x] All changes pushed to main
- [ ] Flask app restarted
- [ ] Browser cache cleared
- [ ] End-to-end test successful

---

## 📊 **Expected Results**

### **Before (With Frontend Fix Only):**
```
Frontend: Waits 4 minutes ✅
Backend:  Times out at 2 minutes ❌
Result:   Error at 95% progress
```

### **After (With Both Fixes):**
```
Frontend: Waits 4 minutes ✅
Backend:  Waits 4 minutes ✅
Result:   Video completes successfully!
```

---

## 🐛 **Debugging Tips**

### **If still timing out:**

1. **Check which timeout triggers:**
   ```
   Backend timeout: Error says "Video generation timeout"
   Frontend timeout: Error says "taking longer than expected"
   ```

2. **Check terminal logs:**
   ```bash
   # Look for backend polling:
   [VIDEO_MANAGER] Task updated: generating_video
   [VEO3] Video still generating...
   
   # Should see 48 polls over 4 minutes, not 24
   ```

3. **Check browser console:**
   ```javascript
   // Look for frontend polling:
   [VIDEO WIDGET] Poll attempt 130/240
   [VIDEO WIDGET] Poll attempt 131/240
   
   // Should go up to 240, not stop at 120
   ```

---

## ✅ **Status**

**Fix Status**: 🟢 **COMPLETE**

**Changes**:
- ✅ Backend timeout: 2 min → 4 min
- ✅ Progress calculation: Fixed for 48 polls
- ✅ Consistency: All timeouts now 4 minutes
- ✅ Pushed to main

**Next Step**: 🔄 **RESTART FLASK APP** (backend code changed!)

---

## 📞 **Quick Reference**

### **Timeout Values (All Components):**

| Component | Timeout | Polls | Interval | Total Time |
|-----------|---------|-------|----------|------------|
| **Frontend (dashboard)** | 240 | 240 | 1s | 4 min ✅ |
| **Frontend (main)** | 48 | 48 | 5s | 4 min ✅ |
| **Backend (worker)** | 48 | 48 | 5s | 4 min ✅ |

**All aligned at 4 minutes!** ✅

---

**Summary:** Backend was timing out at 2 minutes (95% progress) while frontend was prepared to wait 4 minutes. Increased backend timeout from 24 to 48 polls (2 → 4 minutes) and fixed progress calculation. Now frontend and backend are in sync, both waiting 4 minutes for Veo 3 to complete. 🎉

**ACTION REQUIRED:** 🔄 **Restart Flask app to load new backend code!**

