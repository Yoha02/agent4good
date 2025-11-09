# Conflict Resolution Guide

## Overview
This guide shows exactly how to resolve conflicts when merging main into `feature/pubsub-integration`.

## Expected Conflicts

### 1. `app_local.py` - Conflict in `get_air_quality_detailed()`

#### Conflict Location
Lines 2587-2664 (approximately)

#### What Happened
- **Main's changes**: Modified the function to support multi-day historical data fetching with date ranges
- **Our changes**: Also modified the function for multi-day support but with different implementation

#### Resolution Strategy
**Keep MAIN's version** - Main's implementation is more complete for multi-day charts.

Our changes to this function are similar to main's, so we should accept main's version which includes:
- Proper date range parsing
- Day-by-day iteration
- Variance simulation for historical data
- Statistical calculations

The Pub/Sub changes are in a different function (`submit_report`) so no conflict there.

#### How to Resolve
When Git shows conflict markers in this section:
```python
<<<<<<< HEAD (our branch)
# Our version
=======
# Main's version
>>>>>>> origin/main
```

**Action**: Keep main's version (delete our version and the conflict markers)

---

### 2. `requirements.txt` - Dependency Versions

#### What Happened
- **Main's changes**: May have different dependency versions
- **Our changes**: Added Pub/Sub and pinned several versions to prevent build timeouts

#### Resolution Strategy
**Keep OUR pinned versions** + add any new dependencies from main.

Our pinned versions are critical - they prevent the 30-minute Cloud Build timeout that we experienced.

#### How to Resolve

**Step 1**: Accept our version as the base

**Step 2**: Manually check if main added any new dependencies we don't have:
```bash
git show origin/main:requirements.txt > main_requirements.txt
git show HEAD:requirements.txt > our_requirements.txt
# Compare the two files
```

**Step 3**: Merge any new dependencies from main into our version

**Step 4**: Ensure these key pinned versions remain:
```
google-adk==1.17.0
google-cloud-aiplatform==1.121.0
google-cloud-storage==2.19.0
google-cloud-pubsub==2.28.0
firebase-admin==6.9.0
tenacity==8.5.0
```

---

## Files with NO Conflicts

### Frontend Files (Auto-merge)
These were modified in main but not in our branch. Git will automatically use main's version:
- `static/js/air-quality-map.js`
- `static/js/app.js`
- `static/js/pollutant-charts.js`
- `templates/report.html`

**Action**: Accept main's version (Git does this automatically)

### Our New Files (Auto-merge)
These exist only in our branch. Git will automatically keep them:
- `pubsub_services/__init__.py`
- `pubsub_services/config.py`
- `pubsub_services/publisher.py`
- `pubsub_services/schemas.py`
- `workers/Dockerfile`
- `workers/bigquery_worker.py`
- `workers/requirements.txt`
- `PUBSUB_*.md` files

**Action**: Keep all (Git does this automatically)

---

## Step-by-Step Conflict Resolution

### When Git Reports Conflicts

After running `git merge origin/main`, Git will report conflicts:
```
Auto-merging app_local.py
CONFLICT (content): Merge conflict in app_local.py
Auto-merging requirements.txt
CONFLICT (content): Merge conflict in requirements.txt
Automatic merge failed; fix conflicts and then commit the result.
```

### Resolve `app_local.py`

**Option A: Using VS Code** (Recommended)
1. Open `app_local.py` in VS Code
2. Look for conflict markers (highlighted by VS Code)
3. For each conflict in `get_air_quality_detailed()`:
   - Click "Accept Incoming Change" (main's version)
4. For conflicts in `submit_report()`:
   - Click "Accept Current Change" (our Pub/Sub integration)
5. Save the file

**Option B: Manual Editing**
1. Open `app_local.py` in a text editor
2. Search for `<<<<<<<` to find conflicts
3. For each conflict:
   - Identify which section is ours vs main's
   - Keep the appropriate version
   - Delete conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
4. Save the file

**Key Points**:
- In `get_air_quality_detailed()`: Keep main's version
- In `submit_report()`: Keep our Pub/Sub version
- If both functions have conflicts, resolve each independently

### Resolve `requirements.txt`

**Option A: Using VS Code**
1. Open `requirements.txt` in VS Code
2. For each conflict:
   - If it's a version we pinned: "Accept Current Change" (our version)
   - If it's a new dependency from main: "Accept Both Changes"
3. Remove any duplicate lines
4. Save the file

**Option B: Manual Editing**
1. Open both versions side by side:
   ```bash
   git show origin/main:requirements.txt > main_req.txt
   git show HEAD:requirements.txt > our_req.txt
   ```
2. Create a merged version:
   - Start with our `requirements.txt`
   - Add any new lines from `main_req.txt` that aren't in ours
   - Ensure no duplicates
   - Keep our pinned versions
3. Replace `requirements.txt` with the merged version
4. Delete `main_req.txt` and `our_req.txt`

---

## Verification After Resolving Conflicts

### 1. Check for Remaining Conflicts
```bash
git status
# Should show:
# both modified: app_local.py
# both modified: requirements.txt
# but NO "unmerged paths" after resolution
```

### 2. Verify No Conflict Markers Remain
```bash
# Check for conflict markers
grep -r "<<<<<<< HEAD" .
grep -r "=======" .
grep -r ">>>>>>>" .
# Should return NO results in code files
```

### 3. Check Python Syntax
```bash
python -m py_compile app_local.py
# Should complete without errors
```

### 4. Check Requirements Format
```bash
cat requirements.txt | sort | uniq -d
# Should show NO duplicate lines
```

---

## Mark Conflicts as Resolved

After resolving all conflicts:

```bash
# Stage the resolved files
git add app_local.py
git add requirements.txt

# Verify all conflicts are resolved
git status
# Should show:
# All conflicts fixed but you are still merging.

# Complete the merge
git commit
# Git will open an editor with a default merge commit message
# You can keep it or customize it
# Save and close the editor
```

---

## If Something Goes Wrong

### Abort the Merge
If you want to start over:
```bash
git merge --abort
# This will reset to the state before the merge
```

### Restore from Backup
If you already committed but want to undo:
```bash
# Restore from backup branch
git reset --hard feature/pubsub-integration-backup
```

---

## Post-Merge Testing

After successfully merging and committing:

### 1. Test Imports
```bash
python -c "from app_local import app; print('✅ Imports OK')"
```

### 2. Test Pub/Sub Import
```bash
python -c "from pubsub_services import USE_PUBSUB, publish_community_report; print('✅ Pub/Sub imports OK')"
```

### 3. Run Local Server
```bash
# With Pub/Sub disabled
$env:USE_PUBSUB="false"
python app_local.py
# Check: http://localhost:5000 loads
# Try submitting a report
# Ctrl+C to stop

# With Pub/Sub enabled
$env:USE_PUBSUB="true"
python app_local.py
# Check: http://localhost:5000 loads
# Try submitting a report
# Ctrl+C to stop
```

### 4. Check Frontend Features from Main
- Multi-day pollutant charts (7, 14, 30 days)
- Location autocomplete on report page
- Map auto-location

---

## Summary Checklist

- [ ] Backup branch created (`feature/pubsub-integration-backup`)
- [ ] Fetch latest from origin (`git fetch origin`)
- [ ] Merge main into feature branch (`git merge origin/main`)
- [ ] Resolve `app_local.py` conflicts (keep main's detailed function, keep our Pub/Sub in submit_report)
- [ ] Resolve `requirements.txt` conflicts (keep our pinned versions)
- [ ] Verify no conflict markers remain
- [ ] Check Python syntax
- [ ] Stage resolved files (`git add`)
- [ ] Commit merge (`git commit`)
- [ ] Test imports
- [ ] Test local server (both Pub/Sub on/off)
- [ ] Push to origin (`git push origin feature/pubsub-integration`)
- [ ] Create Pull Request on GitHub
- [ ] Review and merge PR

---

## Need Help?

If you encounter unexpected conflicts or errors:
1. Run `git status` and share the output
2. Share the conflict section (between `<<<<<<<` and `>>>>>>>`)
3. I'll provide specific resolution steps

