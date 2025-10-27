# 🔍 Disease Cards Debug Checklist

**Issue**: COVID-19, Influenza, and RSV cards stuck on "Loading..." with `-` values

---

## 📋 What to Check in Browser Console

### 1. **Check if respiratory-chart.js is loading**
Look for this log on page load:
```
[RESPIRATORY CHART] Initializing disease cards...
```

### 2. **Check if updateDiseaseCards is being called**
Look for this log:
```
[DISEASE CARDS] ========== UPDATING CARDS (BigQuery) ==========
[DISEASE CARDS] Days: 7
[DISEASE CARDS] State: California Location text: California
```

### 3. **Check if API call is being made**
Look for:
```
[DISEASE CARDS] Fetching BigQuery data: /api/infectious-disease-dashboard?state=California&days=7
[DISEASE CARDS] Response status: 200
[DISEASE CARDS] BigQuery Result status: success
```

### 4. **Check for errors**
Look for any red error messages containing:
- `[DISEASE CARDS]`
- `updateDiseaseCards`
- `infectious-disease-dashboard`

---

## 🎯 Possible Issues

### Issue 1: JavaScript Not Running
**Symptom**: No console logs at all  
**Cause**: Script not loaded or JavaScript error earlier in page  
**Solution**: Check for any red errors in console before the page finishes loading

### Issue 2: API Returns No Data
**Symptom**: Logs show API called but status is not 'success'  
**Cause**: BigQuery tables empty or not accessible  
**Solution**: This is expected for development - tables need to be populated

### Issue 3: currentState is Undefined
**Symptom**: Logs show `State:  Location text: National`  
**Cause**: `currentState` variable not set when cards initialize  
**Solution**: Need to ensure `currentState = 'California'` before cards load

### Issue 4: Timing Issue
**Symptom**: Cards load before state is set  
**Cause**: `updateDiseaseCards(7)` runs before `currentState` is initialized  
**Solution**: Call `updateDiseaseCards` after state is set

---

## 🔧 Quick Test

Open browser console and manually run:
```javascript
// Check if function exists
console.log('updateDiseaseCards:', typeof updateDiseaseCards);

// Check if currentState is set
console.log('currentState:', window.currentState);

// Manually trigger update
if (typeof updateDiseaseCards === 'function') {
    updateDiseaseCards(7);
}
```

This will tell us:
1. ✅ If the function is available
2. ✅ If the state variable is accessible  
3. ✅ What happens when we manually call it

---

## 📊 Expected Console Output

If everything is working, you should see:

```
[RESPIRATORY CHART] Initializing disease cards...
[DISEASE CARDS] ========== UPDATING CARDS (BigQuery) ==========
[DISEASE CARDS] Days: 7
[DISEASE CARDS] State: California Location text: California
[DISEASE CARDS] Updated location indicator
[DISEASE CARDS] Fetching BigQuery data: /api/infectious-disease-dashboard?state=California&days=7
[DISEASE CARDS] Response status: 200
[DISEASE CARDS] BigQuery Result status: success
[DISEASE CARDS] ✅ BigQuery data received
[DISEASE CARDS] RSV avg positivity from BigQuery: 12.5
[DISEASE CARDS] COVID avg positivity from BigQuery: 8.3
[DISEASE CARDS] Flu avg positivity from BigQuery: 5.7
```

---

## 🚨 Most Likely Issue

Based on the symptoms, the **most likely issue** is:

### **`currentState` is undefined when `updateDiseaseCards()` is called**

**Why**: 
- `updateDiseaseCards(7)` is called in a `setTimeout(..., 500)` 
- But `currentState` might not be set yet in `initializeApp()`
- The function looks for `currentState` variable to determine the state

**How to verify**:
In the console logs, look for:
```
[DISEASE CARDS] State:  Location text: National
```

If "State:" is empty, that's the problem!

---

## 💡 Solution

If `currentState` is undefined, we need to ensure the disease cards load **AFTER** the state is set in `app.js`.

Currently:
```javascript
// app.js - initializeApp()
currentState = 'California';  // Line 523
// ... lots of other code ...

// respiratory-chart.js - runs 500ms after DOM loads
updateDiseaseCards(7);  // This might run before currentState is set!
```

**Fix**: Call `updateDiseaseCards` after we're sure `currentState` is set.

