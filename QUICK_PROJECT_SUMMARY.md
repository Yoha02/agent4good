# 🎯 Community Health Platform - Quick Summary

## What Is This?

A **comprehensive health monitoring platform** that combines AI agents, real-time data, and interactive dashboards to serve communities and health officials.

---

## 🚀 What It Does

### For the Public
1. **Check Air Quality** - Current and historical data
2. **Track Diseases** - Infectious disease monitoring
3. **Find Clinics** - Locate nearby medical facilities
4. **Get Health Advice** - AI-powered wellness tips
5. **Watch PSA Videos** - AI-generated health announcements
6. **Report Issues** - Submit community health concerns

### For Health Officials
1. **County-Level Monitoring** - Detailed health metrics
2. **Multi-Source Data** - EPA, CDC, USGS, NOAA
3. **Alert Management** - Create and distribute warnings
4. **Trend Analysis** - Historical data visualization
5. **Export Data** - CSV/JSON for reports

---

## 🤖 The AI System

### **8 Specialized Agents**
```
🏥 community_health_assistant (Root)
├── 1. air_quality_agent         [EPA historical data]
├── 2. live_air_quality_agent    [AirNow real-time]
├── 3. infectious_diseases_agent [CDC tracking]
├── 4. clinic_finder_agent       [Google Search]
├── 5. health_faq_agent          [Wellness Q&A]
├── 6. persona_aware_agent       [Context adaptation]
├── 7-9. PSA Video Agents        [Video generation + Twitter]
     ├── actionline_agent
     ├── veo_prompt_agent
     └── twitter_agent
```

**Each agent is a specialist** - knows one domain extremely well!

---

## 💾 Data Sources

### Real-Time
- **AirNow API** - Current air quality
- **USGS** - Earthquake alerts
- **NOAA** - Severe weather
- **InciWeb** - Active wildfires

### Historical
- **EPA BigQuery** - 2025 air quality data
- **CDC** - Disease tracking
- **NY State Health** - Health metrics

### **Total:** 12+ data sources feeding the system!

---

## 🎥 PSA Video Feature (Your Work!)

### How It Works
```
1. User: "Create a PSA about air quality"
2. AI generates short health message
3. AI creates video with Veo 3.1 (30-60 sec)
4. Video displayed in chat
5. User: "yes" → Posted to Twitter @AI_mmunity
```

### **Live Examples**
- https://twitter.com/AI_mmunity/status/1982181391912812817
- https://twitter.com/AI_mmunity/status/1982189217402040358
- https://twitter.com/AI_mmunity/status/1982198114317652060

---

## 🏗️ Technology

### Backend
- **Python 3.13** + Flask 3.0
- **Google ADK** (Agent Development Kit)
- **BigQuery** (Data warehouse)
- **Gemini 2.0** (AI chat)
- **Veo 3.1** (Video generation)

### Frontend
- **Vanilla JavaScript** (no frameworks!)
- **D3.js** (Visualizations)
- **Three.js** (3D effects)
- **Tailwind CSS** (Styling)

### Infrastructure
- **Google Cloud Run** (Serverless)
- **Cloud Storage** (Videos)
- **BigQuery** (Analytics)

---

## 📊 By the Numbers

- **8** AI Agents
- **12+** Data Sources
- **5** Web Pages
- **8** Tool Modules
- **20,000+** Lines of Code
- **140+** Files
- **16,000+** Lines Added in Final Integration

---

## ✅ Status

**Branch:** `main`  
**Deployment:** Ready for Cloud Run  
**Features:** All working  
**Tests:** Passing  
**Documentation:** Complete  

### What Works
✓ All 8 agents responding  
✓ Air quality (live + historical)  
✓ Disease tracking  
✓ Clinic finder  
✓ PSA video generation  
✓ Twitter posting  
✓ Officials dashboard  
✓ Community reporting  

---

## 🎯 Your Contribution

### **PSA Video & Twitter Integration**
- 3 new agents (ActionLine, VeoPrompt, Twitter)
- Veo 3.1 API integration
- Twitter OAuth with video upload
- Async video task management
- Web UI for video preview and posting
- Successfully integrated into team's modular structure

**Impact:** Enables automated public health communication at scale!

---

## 🚀 Quick Start

### **Run Locally**
```bash
python app.py
# Visit: http://localhost:8080
```

### **Deploy to Cloud**
```bash
./deploy_new.ps1
```

### **Test Twitter**
```bash
python test_twitter_post.py --auto
```

---

## 🔑 Key Files

**Main:** `app.py` (Flask server)  
**Agents:** `multi_tool_agent_bquery_tools/agents/`  
**Tools:** `multi_tool_agent_bquery_tools/tools/`  
**UI:** `templates/` + `static/`  
**Data:** `data_ingestion/` + `data/bigquery_schemas/`  

---

**Built for:** Google Agents for Good Hackathon  
**Platform:** Google Cloud + Agent Development Kit  
**Status:** Production Ready 🎉

