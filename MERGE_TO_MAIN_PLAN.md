# Merge to Main - Pre-Merge Analysis & Plan

## Current Branch Status
- **Current Branch**: `feature/pubsub-integration`
- **Target Branch**: `main`
- **Main is ahead by**: 3 commits (UI improvements from another branch)

## Summary of Changes

### Main Branch (3 commits ahead)
Main has received UI improvements that we don't have:
1. **Commit 2006acc2**: Merge PR #22 (UI selective commits)
2. **Commit 043564ce**: Multi-day pollutant charts, Google Maps autocomplete, Celsius/Fahrenheit toggle, map auto-location
3. **Commit 7a9a5b2c**: Google Maps autocomplete and auto-location fixes

**Files changed in main:**
- `static/js/air-quality-map.js` - Map improvements
- `static/js/app.js` - Location auto-detection and data loading refactoring
- `static/js/pollutant-charts.js` - Multi-day chart support
- `templates/report.html` - Location autocomplete improvements

### Our Branch (5 commits ahead)
Our branch has Pub/Sub integration that main doesn't have:
1. **Commit 2061156c**: Implementation completion summary
2. **Commit 84ddd3f3**: Pub/Sub MVP implementation
3. **Commit c4f5d771**: PowerShell deployment commands
4. **Commit c99a1907**: Pub/Sub MVP plan
5. **Commit 94c2985d**: Pub/Sub integration plan

**Files changed in our branch:**
- `app_local.py` - Pub/Sub integration in submit_report endpoint + detailed pollutant data changes
- `requirements.txt` - Added Pub/Sub and pinned versions
- `deploy_to_cloudrun.sh` - Updated deployment script
- `pubsub_services/` - New directory with Pub/Sub publisher
- `workers/` - New directory with BigQuery worker
- `*.md` files - Documentation

## Conflict Analysis

### ❌ CONFLICTS EXPECTED

#### 1. `app_local.py` - MAJOR CONFLICT
**Our changes:**
- Lines 2255-2354: Pub/Sub integration in `submit_report()`
- Lines 2587-2664: Historical data processing in `get_air_quality_detailed()`

**Main's changes:**
- Same `get_air_quality_detailed()` function modified for multi-day chart support

**Resolution needed**: 
- Keep BOTH changes
- Pub/Sub integration is independent and won't conflict with multi-day chart logic
- Need to carefully merge the detailed data fetching logic

#### 2. `requirements.txt` - MINOR CONFLICT
**Our changes:**
- Added `google-cloud-pubsub==2.28.0`
- Pinned versions: `google-adk==1.17.0`, `google-cloud-aiplatform==1.121.0`, etc.

**Main's changes:**
- May have different versions or additions

**Resolution needed**:
- Keep our pinned versions (they resolve Cloud Build timeouts)
- Ensure no duplicate entries

### ✅ NO CONFLICTS EXPECTED

#### Frontend Files (Safe - We didn't touch these)
- `static/js/air-quality-map.js`
- `static/js/app.js`  
- `static/js/pollutant-charts.js`
- `templates/report.html`

These files were modified in main but not in our branch, so Git will automatically accept main's version.

#### Our New Files (Safe - Don't exist in main)
- `pubsub_services/` directory
- `workers/` directory
- Documentation `.md` files

## Merge Strategy

### Option 1: Merge Main into Our Branch First (RECOMMENDED)
This is the safest approach - we test the merged code before pushing to main.

**Steps:**
1. **Backup our branch** (create a backup branch)
2. **Merge main into our branch** (resolve conflicts in feature branch)
3. **Test the merged code** locally
4. **Test in Cloud Run** (optional but recommended)
5. **Create PR** to merge our branch into main
6. **Review and merge PR**

**Advantages:**
- We resolve conflicts in our branch (safer)
- We can test everything before merging to main
- If something breaks, main is unaffected
- Can iterate on fixes in feature branch

**Disadvantages:**
- Requires local testing after merge

### Option 2: Direct Merge (NOT RECOMMENDED)
Merge feature branch directly into main and resolve conflicts.

**Disadvantages:**
- Conflicts resolved directly in main
- If we break something, main is broken
- Less safe for production

## Recommended Plan

### Step 1: Create Backup Branch
```bash
git checkout feature/pubsub-integration
git branch feature/pubsub-integration-backup
git push origin feature/pubsub-integration-backup
```

### Step 2: Merge Main into Feature Branch
```bash
git checkout feature/pubsub-integration
git merge origin/main
# Resolve conflicts (see below)
```

### Step 3: Resolve Conflicts

#### For `app_local.py`:
1. Accept BOTH changes in `submit_report()` (keep our Pub/Sub integration)
2. In `get_air_quality_detailed()`, carefully merge:
   - Keep main's loop structure for multi-day support
   - Ensure our BigQuery target is preserved

#### For `requirements.txt`:
1. Keep our pinned versions
2. Add any new dependencies from main
3. Remove duplicates

### Step 4: Test Locally
```bash
# Test with Pub/Sub disabled
$env:USE_PUBSUB="false"
python app_local.py

# Test with Pub/Sub enabled
$env:USE_PUBSUB="true"
python app_local.py
```

### Step 5: Verify Tests Pass
- Submit a test report (with Pub/Sub disabled)
- Submit a test report (with Pub/Sub enabled)
- Verify multi-day pollutant charts work
- Verify location autocomplete works

### Step 6: Commit Merge
```bash
git add .
git commit -m "Merge main into feature/pubsub-integration - UI improvements + Pub/Sub integration"
git push origin feature/pubsub-integration
```

### Step 7: Create Pull Request
```bash
# On GitHub:
# Create PR from feature/pubsub-integration -> main
# Title: "Pub/Sub Integration for Community Reports (MVP)"
# Description: See PR template below
```

### Step 8: Review and Merge PR
- Review changes on GitHub
- Ensure CI/CD passes (if configured)
- Merge PR to main
- Delete feature branch (or keep for reference)

## Pull Request Template

```markdown
# Pub/Sub Integration for Community Reports (MVP)

## Overview
Implements Google Cloud Pub/Sub for asynchronous community report processing to meet Google Cloud competition requirements.

## Changes

### Backend
- ✅ Pub/Sub publisher in `pubsub_services/` package
- ✅ BigQuery worker in `workers/` directory  
- ✅ Feature flag (`USE_PUBSUB`) for safe rollout
- ✅ Fallback to direct BigQuery insert if Pub/Sub fails
- ✅ Modified `submit_report()` endpoint for async processing

### Infrastructure
- ✅ Cloud Run worker deployed and tested
- ✅ Pub/Sub topic: `community-reports-submitted`
- ✅ Pub/Sub subscription: `bigquery-writer-sub`
- ✅ IAM permissions configured

### Dependencies
- ✅ Added `google-cloud-pubsub==2.28.0`
- ✅ Pinned dependency versions to prevent build timeouts

### Testing
- ✅ Local testing (with and without feature flag)
- ✅ End-to-end testing in Cloud Run
- ✅ Worker processing verified
- ✅ BigQuery inserts verified

## Merged Changes from Main
- ✅ Multi-day pollutant charts
- ✅ Google Maps autocomplete improvements
- ✅ Location auto-detection improvements
- ✅ Map visualization enhancements

## Deployment Notes
- Feature flag is **DISABLED** by default (`USE_PUBSUB=false`)
- To enable Pub/Sub: Set `USE_PUBSUB=true` in Cloud Run environment variables
- Worker is running and ready to process messages
- Rollback procedure documented in `PUBSUB_ROLLBACK_GUIDE.md`

## Testing Checklist
- [ ] Community report submission (Pub/Sub disabled)
- [ ] Community report submission (Pub/Sub enabled)
- [ ] BigQuery insert verification
- [ ] Worker logs show successful processing
- [ ] Frontend UI works correctly
- [ ] Multi-day pollutant charts load
- [ ] Location autocomplete works

## Competition Requirements Met
- ✅ Cloud Run service/job/worker pool
- ✅ Integration with Google Cloud services (Pub/Sub, BigQuery)
- ✅ Asynchronous message processing
- ✅ Modular, scalable architecture

## Rollback Plan
See `PUBSUB_ROLLBACK_GUIDE.md` for detailed rollback instructions.

Quick rollback:
```bash
# Disable Pub/Sub (no code changes needed)
gcloud run services update agent4good --region us-central1 --set-env-vars USE_PUBSUB=false
```
```

## Next Steps

After reviewing this plan:
1. **Confirm the strategy**: Do you want to proceed with Option 1 (merge main into feature branch first)?
2. **Create backup branch**: I'll create the backup
3. **Perform the merge**: I'll merge main into our branch
4. **Resolve conflicts**: I'll resolve conflicts with your review
5. **Test**: You'll test locally
6. **Create PR**: Create the PR on GitHub

## Risk Assessment

### Low Risk ✅
- Frontend files: No conflicts (we didn't modify them)
- New files: No conflicts (don't exist in main)
- Documentation: No conflicts

### Medium Risk ⚠️
- `requirements.txt`: Easy to resolve
- `get_air_quality_detailed()`: Need to carefully merge logic

### Managed Risk 🛡️
- Pub/Sub feature flag: Disabled by default (safe)
- Backup branch: Can revert if needed
- Rollback guide: Documented procedure

## Estimated Time
- Backup + Merge: 5 minutes
- Conflict resolution: 15-20 minutes
- Local testing: 15-20 minutes
- PR creation: 5 minutes
- **Total: ~45-50 minutes**

