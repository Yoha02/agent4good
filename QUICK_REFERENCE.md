# Quick Reference: Crowdsourcing Integration

## 📌 Current Status
- ✅ Branch created: `integrate-crowdsourcing-features`
- ✅ All planning documents created
- ⏳ Ready to implement

---

## 🎯 What We're Doing
**Adding crowdsourcing features from `recovered_agent_code` branch to `main` WITHOUT breaking anything**

---

## 📂 Files to Add (5 New Files)

### From `recovered_agent_code` branch:
1. `multi_tool_agent_bquery_tools/agents/crowdsourcing_agent.py`
2. `multi_tool_agent_bquery_tools/agents/health_official_agent.py`
3. `multi_tool_agent_bquery_tools/tools/crowdsourcing_tool.py`
4. `multi_tool_agent_bquery_tools/tools/embedding_tool.py`
5. `multi_tool_agent_bquery_tools/tools/semantic_query_tool.py`

---

## ✏️ Files to Update (3 Files)

### 1. `multi_tool_agent_bquery_tools/agent.py`
**Add after line 33:**
```python
from .agents.crowdsourcing_agent import crowdsourcing_agent
from .agents.health_official_agent import health_official_agent
from .tools.embedding_tool import generate_report_embeddings
```

**Add to sub_agents list (line ~146):**
```python
crowdsourcing_agent,
health_official_agent,
```

**Add to tools (line ~110):**
```python
tools=[generate_report_embeddings],
```

**Add to menu and routing rules:**
- Menu: Add items 8 & 9 for community reports and insights
- Routing: Add rules for report submission and semantic search

### 2. `multi_tool_agent_bquery_tools/agents/clinic_finder_agent.py`
- Update `instruction` parameter with enhanced prompt from recovered branch
- Keep everything else the same

### 3. `multi_tool_agent_bquery_tools/agents/infectious_diseases_agent.py`
- Update `instruction` parameter with enhanced prompt from recovered branch
- Change model to `gemini-2.5-pro`
- Keep everything else the same

---

## 🚫 Files to NEVER Touch
- ❌ `app_local.py`
- ❌ `air_quality_tool.py`
- ❌ `disease_tools.py`
- ❌ `.github/workflows/deploy.yml`
- ❌ `Dockerfile`
- ❌ Context injection logic in `agent.py`

---

## 📋 Implementation Order

1. Copy 5 new files from `recovered_agent_code`
2. Update `agent.py` (add imports, sub-agents, tools, routing)
3. Update `clinic_finder_agent.py` prompt
4. Update `infectious_diseases_agent.py` prompt
5. Test locally
6. Push to remote
7. Deploy to Cloud Run
8. Merge to main

---

## ✅ Testing Checklist

### Existing Features (Must Work):
- [ ] Air quality (live & historical)
- [ ] Disease tracking
- [ ] Clinic finder
- [ ] Health FAQ
- [ ] Analytics agent
- [ ] PSA videos
- [ ] Twitter posting

### New Features (Must Work):
- [ ] Submit health report
- [ ] Search reports semantically
- [ ] Generate embeddings

---

## 🆘 Quick Commands

### Fetch recovered branch:
```bash
git fetch origin recovered_agent_code
```

### Copy a file from recovered:
```bash
git show origin/recovered_agent_code:path/to/file > path/to/file
```

### Test locally:
```bash
python -c "from multi_tool_agent_bquery_tools.agent import root_agent; print('✅ Import successful')"
```

### Rollback if needed:
```bash
git checkout main
git branch -D integrate-crowdsourcing-features
```

---

## 📚 Full Documentation

- `INTEGRATION_PLAN.md` - Complete detailed plan
- `AGENT_PY_CHANGES.md` - Exact line-by-line changes
- `INTEGRATION_SUMMARY.md` - Overview and summary
- `RECOVERED_AGENT_CODE_COMPARISON.md` - Branch comparison analysis

---

## 🎯 Success Criteria

✅ All existing features work  
✅ New crowdsourcing features work  
✅ No errors in logs  
✅ Cloud Run deployment succeeds  
✅ Zero regressions  

---

## ⏱️ Time Estimate
**Total: ~1.5 hours**
- Implementation: 45 min
- Testing: 30 min
- Deployment: 15 min

