# 🎥 Video Generation Error Fix

**Date**: November 5, 2025  
**Issue**: Video generation failing with `'dict' object has no attribute 'message'`  
**Status**: ✅ **FIXED**

---

## 🐛 **Problem**

### **User Report:**
Video generation was failing in the officials dashboard with this error in the network response:

```json
{
  "error": "'Status check error: 'dict' object has no attribute 'message'",
  "status": "error"
}
```

### **Console Logs:**
```
[VIDEO WIDGET] Video generation failed
```

---

## 🔍 **Root Cause Analysis**

### **Video Generation Flow:**

1. **User requests video** → `sendChatWidgetMessage()` in `officials-dashboard.js`
2. **Backend creates task** → `/api/agent-chat` endpoint in `app_local.py`
3. **Background thread starts** → `VideoGenerationManager.start_video_generation()`
4. **Calls Veo 3 API** → `veo_client.generate_video()` in `veo3_client.py`
5. **Polls for completion** → `veo_client.check_operation_status()`
6. **Frontend polls** → `/api/check-video-task/{taskId}` every 1 second
7. **Video complete** → Returns public URL

###  **Where It Failed:**

**File**: `multi_tool_agent_bquery_tools/integrations/veo3_client.py`  
**Line**: 163  
**Function**: `check_operation_status()`

```python
# ❌ BEFORE (Line 163-167):
if operation.error:
    print(f"[VEO3] Generation failed: {operation.error.message}")
    return {
        "status": "error",
        "error_message": operation.error.message  # ❌ Fails here!
    }
```

### **Why It Failed:**

The Google AI SDK's `operation.error` can be:
- **A dict**: `{'message': '...', 'code': 400}`
- **An object**: With `.message` attribute
- **A string**: Just the error text

The code assumed it was always an **object**, but in this case it was a **dict**, causing:
```python
AttributeError: 'dict' object has no attribute 'message'
```

---

## ✅ **Solution**

Updated error handling to support **all 3 formats**:

```python
# ✅ AFTER (Line 162-174):
if operation.error:
    # Handle error - operation.error can be dict or object
    error_msg = str(operation.error)  # Fallback to string
    if hasattr(operation.error, 'message'):
        error_msg = operation.error.message  # Object format
    elif isinstance(operation.error, dict) and 'message' in operation.error:
        error_msg = operation.error['message']  # Dict format
    
    print(f"[VEO3] Generation failed: {error_msg}")
    return {
        "status": "error",
        "error_message": error_msg
    }
```

### **Logic:**
1. **Default**: Convert error to string `str(operation.error)`
2. **Check for object**: If has `.message` attribute → use it
3. **Check for dict**: If is dict with `'message'` key → use it
4. **Return error**: Properly formatted error message

---

## 🧪 **Testing**

### **To Test the Fix:**

1. **Restart your Flask app** (Ctrl+C, then `python app_local.py`)
2. **Go to Officials Dashboard** → Login
3. **Open chat widget** → Click "Create PSA" button
4. **Request video**: Type "create a PSA video for air quality in California"
5. **Observe**:
   - ✅ Video should generate successfully OR
   - ✅ Error message should be clear (not AttributeError)

### **Expected Behavior:**

#### **Success Case:**
```
[VIDEO WIDGET] Video still generating_video (progress: 36%)
[VIDEO WIDGET] Video still generating_video (progress: 39%)
...
[VIDEO WIDGET] Video ready: https://storage.googleapis.com/...
```

#### **Error Case (if quota exceeded, etc.):**
```
[VEO3] Generation failed: Quota exceeded for model veo-3.0-fast-generate-001
[VIDEO WIDGET] Video generation failed
```

**No more** `'dict' object has no attribute 'message'` errors!

---

## 📊 **Impact**

### **Files Changed:**
- `multi_tool_agent_bquery_tools/integrations/veo3_client.py` (Line 162-174)

### **What's Fixed:**
- ✅ Video generation error handling robust
- ✅ Supports all Google AI SDK error formats
- ✅ Clear error messages for debugging
- ✅ No more AttributeError crashes

### **What's NOT Affected:**
- Video generation success path (unchanged)
- Twitter posting (unchanged)
- UI polling logic (unchanged)

---

## 🎯 **Additional Notes**

### **Why This Error Occurred:**
The Google AI SDK may return different error formats depending on:
- API version
- Error type (quota, validation, network)
- Response format

Our code now handles **all cases** gracefully.

### **Related Components:**

1. **Video Manager** (`async_video_manager.py`):
   - Creates tasks
   - Polls Veo client
   - Updates task status

2. **Veo Client** (`veo3_client.py`):
   - Calls Google AI API
   - Checks operation status ✅ **FIXED HERE**
   - Downloads and uploads video

3. **Frontend Polling** (`officials-dashboard.js`):
   - Polls `/api/check-video-task/{taskId}`
   - Shows progress
   - Displays video when ready

---

## 🚀 **Deployment**

### **Local:**
- ✅ Fixed in current branch
- Restart app to apply

### **Cloud Run:**
- Will be included in next deployment
- Use updated `gcloud run deploy` command

---

## ✅ **Verification Checklist**

After restart, verify:
- [ ] Video generation starts successfully
- [ ] Progress updates shown in console
- [ ] Video completes and shows URL OR
- [ ] Clear error message (not AttributeError)
- [ ] Twitter posting works (if video succeeds)
- [ ] No crashes in backend logs

---

**Fix Complete!** 🎉

Restart your app and try generating a video again!

