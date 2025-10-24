# Community Health & Wellness Agent

A full-stack web application combining beautiful UI dashboards with Google's Agent Development Kit (ADK) multi-agent system for real-time community health monitoring.

**Live Demo**: https://community-health-agent-776464277441.us-central1.run.app

![Platform Overview](https://img.shields.io/badge/Platform-Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask)

---

## 🌟 Features

### **Multi-Agent AI System**
- **Air Quality Agent**: Queries EPA BigQuery data for PM2.5 and AQI information across US counties
- **Disease Tracking Agent**: Monitors infectious diseases from CDC BEAM dashboard data
- **Health FAQ System**: Provides wellness information on water safety, food safety, and prevention

### **Interactive Web Dashboard**
- Real-time air quality statistics with auto-updating metrics
- Interactive data visualizations (D3.js, Chart.js, Three.js backgrounds)
- AI-powered chat interface with natural language understanding
- State-based filtering for localized insights
- 7-day, 14-day, and 30-day trend analysis

### **Real Data Sources**
- **EPA Air Quality**: Public BigQuery dataset `bigquery-public-data.epa_historical_air_quality` (2010-2021)
- **Infectious Diseases**: CDC BEAM Dashboard via your project's BigQuery dataset
- **AI Processing**: Google Gemini AI via Agent Development Kit

---

## 🚀 Quick Start

### **Prerequisites**
- Google Cloud Project with billing enabled
- Gemini API Key from https://aistudio.google.com/apikey (free tier available)
- Google Cloud SDK installed and configured

### **Local Development**

1. **Clone and setup**:
```bash
git clone https://github.com/Yoha02/agent4good
cd agent4good
git checkout combined_UI_and_agent
```

2. **Create `.env` file** in root directory:
```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_API_KEY=your-gemini-api-key
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_GENAI_USE_VERTEXAI=FALSE
SECRET_KEY=your-random-secret-key
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Authenticate with Google Cloud**:
```bash
gcloud auth application-default login
gcloud config set project your-gcp-project-id
```

5. **Run the application**:
```bash
python app.py
```

6. **Open browser**: http://localhost:8080

---

## ☁️ Deploy to Google Cloud Run

### **One-Command Deployment**:

```bash
gcloud run deploy community-health-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_API_KEY=your-api-key,GEMINI_API_KEY=your-api-key,GOOGLE_GENAI_USE_VERTEXAI=FALSE" \
  --memory 2Gi \
  --timeout 300
```

### **Step-by-Step Deployment**:

1. **Set your project**:
```bash
gcloud config set project your-project-id
```

2. **Enable required APIs**:
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com bigquery.googleapis.com
```

3. **Authenticate**:
```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project your-project-id
```

4. **Deploy** (takes ~6-8 minutes):
```bash
gcloud run deploy community-health-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_API_KEY=your-api-key,GEMINI_API_KEY=your-api-key,GOOGLE_GENAI_USE_VERTEXAI=FALSE" \
  --memory 2Gi \
  --timeout 300
```

5. **Get your live URL**:
```bash
gcloud run services describe community-health-agent --region us-central1 --format='value(status.url)'
```

---

## 📁 Project Structure

```
agent4good/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container configuration
├── .dockerignore                   # Build optimization
├── deploy_new.ps1                  # Windows deployment script
│
├── multi_tool_agent_bquery_tools/  # ADK Multi-Agent System
│   ├── agent.py                    # Multi-agent implementation
│   └── __init__.py
│
├── templates/                      # HTML templates
│   └── index.html                  # Main dashboard
│
└── static/                         # Frontend assets
    ├── css/style.css              # Styles
    └── js/
        ├── app.js                 # Main application logic
        ├── animations.js          # UI animations
        ├── d3-viz.js             # D3 visualizations
        └── three-bg.js           # 3D background
```

---

## 🎯 Architecture

```
┌─────────────────────────────────────┐
│   Web Browser                       │
│   - Dashboard UI                    │
│   - Interactive Charts              │
│   - AI Chat Interface               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Flask Backend (app.py)            │
│   - /api/air-quality                │
│   - /api/health-recommendations     │
│   - /api/agent-chat                 │
└──────────────┬──────────────────────┘
               │
               ├──────────────┬─────────────┐
               ▼              ▼             ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │  BigQuery    │  │  Gemini AI   │  │  ADK Agent   │
    │  EPA Data    │  │  (Fallback)  │  │  System      │
    └──────────────┘  └──────────────┘  └──────┬───────┘
                                               │
                                    ┌──────────┴──────────┐
                                    ▼                     ▼
                            ┌──────────────┐      ┌──────────────┐
                            │ Air Quality  │      │   Disease    │
                            │    Agent     │      │    Agent     │
                            └──────────────┘      └──────────────┘
```

---

## 🔧 Configuration Details

### **Required Environment Variables**:

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID | `my-project-123` |
| `GOOGLE_API_KEY` | Gemini API key | `AIzaSy...` |
| `GEMINI_API_KEY` | Same as GOOGLE_API_KEY | `AIzaSy...` |
| `GOOGLE_GENAI_USE_VERTEXAI` | Use Google AI Studio | `FALSE` |

### **Optional Variables**:
| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `PORT` | Server port | `8080` |

---

## 🤖 Multi-Agent System

### **How It Works**:

1. **User asks a question** in the chat interface
2. **Root Agent** analyzes the question and routes to appropriate sub-agent
3. **Specialized Agent** queries relevant data source (BigQuery or knowledge base)
4. **Response** is formatted and returned to user

### **Example Interactions**:

**Air Quality**:
```
User: "What's the air quality in Los Angeles?"
Agent: Queries EPA BigQuery → Returns PM2.5 levels, AQI, health impacts
```

**Disease Tracking**:
```
User: "Show me E. coli cases in Texas"
Agent: Queries CDC BEAM data → Returns case counts, trends, sources
```

**Health FAQs**:
```
User: "How can I stay safe during high pollution?"
Agent: Retrieves FAQ → Returns practical health advice
```

---

## 📊 Data Sources

### **1. EPA Air Quality Data**
- **BigQuery Dataset**: `bigquery-public-data.epa_historical_air_quality.pm25_frm_daily_summary`
- **Coverage**: 2010-2021, all US states
- **Metrics**: PM2.5 concentrations, AQI values, monitoring site locations
- **Access**: Public dataset (no setup required)

### **2. CDC Infectious Disease Data**
- **BigQuery Dataset**: `your-project.beam_report_data_folder.beam_report_data`
- **Source**: CDC BEAM Dashboard Report
- **Metrics**: Laboratory-confirmed isolates, pathogens, sources
- **Coverage**: State-level disease surveillance

---

## 📝 API Endpoints

### **Web Interface**:
- `GET /` - Main dashboard with visualizations

### **Data APIs**:
- `GET /api/air-quality?days=7&state=California` - Get air quality data
- `GET /api/health-recommendations?state=Texas` - Get health advice based on AQI

### **AI Agent**:
- `POST /api/agent-chat` - Chat with multi-agent system
  ```json
  {
    "question": "What's the air quality in Los Angeles?"
  }
  ```

### **System**:
- `GET /health` - Health check endpoint

---

## 🐛 Troubleshooting

### **Problem: Chat not responding**
**Check**: Environment variables are set
```bash
gcloud run services describe community-health-agent --region us-central1 --format="get(spec.template.spec.containers[0].env)"
```
**Solution**: Redeploy with correct env vars

### **Problem: No dashboard data**
**Check**: BigQuery permissions
```bash
gcloud projects get-iam-policy your-project-id
```
**Solution**: App falls back to demo data if BigQuery unavailable

### **Problem: Deployment fails**
**Check**: Build logs
```bash
gcloud builds list --limit 5
```
**Common issues**: 
- Dependency conflicts in requirements.txt
- Missing API enablement
- Billing not enabled

### **View Logs**:
```bash
gcloud run services logs read community-health-agent --region us-central1 --limit 50
```

---

## 🎨 Technology Stack

**Backend**:
- Python 3.11
- Flask 3.0
- Google Cloud BigQuery
- Google ADK (Agent Development Kit)
- Google Gemini AI

**Frontend**:
- HTML5 / CSS3 / JavaScript
- Tailwind CSS
- Chart.js (trend charts)
- D3.js (geographic visualizations)
- Three.js (3D backgrounds)
- Anime.js (animations)

**Infrastructure**:
- Docker
- Google Cloud Run
- Container Registry
- Cloud Build

---

## 💰 Cost Estimate

**Free Tier Includes**:
- Cloud Run: 2 million requests/month
- BigQuery: 1 TB queries/month
- Container Registry: 500 MB storage

**Expected Cost**: $0-5/month for typical usage

---

## 🤝 Contributing

Contributions are welcome! The codebase is clean and well-organized:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test locally**: `python app.py`
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Google Cloud Platform** for infrastructure and AI services
- **Gemini AI** for natural language understanding
- **EPA** for historical air quality data
- **CDC** for disease surveillance data
- **Agents for Impact** hackathon organizers and community

---

## 📞 Support

For issues or questions:
- **GitHub Issues**: https://github.com/Yoha02/agent4good/issues
- **Documentation**: This README
- **Deployment Help**: See deploy_new.ps1 script

---

**Built with ❤️ for Community Health & Wellness**

*Agents for Impact Hackathon - October 2025*
