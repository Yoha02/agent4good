# AI-mmunity: Community Health & Wellness Agent

A community-health prototype combining web dashboards with Google's Agent Development Kit (ADK), Gemini, and specialized data-access agents.

**Start here:** [Architecture and integration case study](docs/CASE_STUDY.md) · [Google Cloud Next ’26 presentation and team](https://yoha02.github.io/A4G_LandingPage/)

## Team and my contribution

I'm **Yoha (Eyoha Girma)**. I led the team, coordinated and integrated code from teammates, and worked on agent setup and orchestration. Our AI-mmunity team won Google Cloud's Agentic AI Arena, and I presented **Silos to Synergy: Architecting Scalable Multi-Agent Systems** at the Google Cloud Next ’26 Developer Theater.

This was a team project with **Abhi Ram Salammagari, Eyoha Girma, Semaa Amin, Aashna Kunkolienker, Tianchen Cai, and Sreekanth Kannan**. The case study links the integrated architecture to the source and explains what another developer can learn from it.

The original Cloud Run demo URL was unavailable during the September 22, 2026 review. Use the presentation page and source walkthrough while the demonstration route is being reconciled. The prototype is not presented as a validated clinical system.

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

### **Public Health Officials Portal**
- **Secure Firebase Authentication**: Login system for authorized officials
- **Protected Dashboard**: Access to community reports and health data
- **Session Management**: Secure logout and session handling
- **No Signup Required**: Officials created by admins in Firebase Console

### **Real Data Sources**
- **EPA Air Quality**: Public BigQuery dataset `bigquery-public-data.epa_historical_air_quality` (2010-2021)
- **Infectious Diseases**: CDC BEAM Dashboard via your project's BigQuery dataset
- **AI Processing**: Google Gemini AI via Agent Development Kit

---

## 🚀 Quick Start

### **Prerequisites**
- Google Cloud Project with billing enabled
- Gemini API Key from https://aistudio.google.com/apikey (free tier available)
- BigQuery service account credentials (see [BigQuery Setup](#bigquery-setup))
- Python 3.11+
- Google Cloud SDK (optional, for deployment)

### **Local Development**

1. **Clone and setup**:
```bash
git clone https://github.com/Yoha02/agent4good
cd agent4good
git checkout UI-and-DB
```

2. **Install dependencies**:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

3. **Configure environment variables**:
```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` with your credentials (see [Environment Setup](#environment-setup) below)

4. **Set up BigQuery authentication** (IMPORTANT!):
   
   See detailed instructions in [SETUP_BIGQUERY.md](SETUP_BIGQUERY.md)
   
   Quick steps:
   - Create service account in Google Cloud Console
   - Download JSON key as `bigquery-credentials.json`
   - Place in project root folder
   - Update `GOOGLE_APPLICATION_CREDENTIALS` in `.env`

5. **Test BigQuery connection**:
```bash
python test_bigquery_auth.py
```

6. **Run the application**:
```bash
python app_local.py
```

7. **Open browser**: http://localhost:8080

---

## 🔐 Environment Setup

### **Required Environment Variables**:

Create a `.env` file in the project root with these values:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
BIGQUERY_DATASET=CrowdsourceData
BIGQUERY_TABLE_REPORTS=CrowdSourceData
GOOGLE_APPLICATION_CREDENTIALS=bigquery-credentials.json

# Gemini AI Configuration
GOOGLE_API_KEY=your-google-api-key
GEMINI_API_KEY=your-gemini-api-key
MAPPING_API_KEY=your-google-maps-api-key

# EPA/AirNow API Configuration
EPA_API_KEY=your-epa-api-key
AQS_API_KEY=your-aqs-api-key
AQS_EMAIL=your-email@example.com

# Firebase Authentication (for Officials Login)
FIREBASE_SERVICE_ACCOUNT_FILE=/path/to/firebase-service-account.json

# Optional
PORT=8080
```

**Where to get API keys:**
- **Gemini API**: https://aistudio.google.com/apikey (free)
- **Google Maps API**: https://console.cloud.google.com/google/maps-apis
- **EPA AirNow API**: https://docs.airnowapi.org/account/request
- **EPA AQS API**: https://aqs.epa.gov/data/api/signup?email=youremail
- **Firebase Config**: See [Firebase Setup](#-firebase-authentication-setup) below

---

## 📊 BigQuery Setup

This application uses **BigQuery** to store community-submitted reports. Your teammates will need to set up authentication to use this feature.

### **For New Team Members:**

See **[SETUP_BIGQUERY.md](SETUP_BIGQUERY.md)** for complete step-by-step instructions.

**Quick Overview:**
1. Get the `bigquery-credentials.json` file from project admin (shared securely, NOT in git)
2. Place it in the project root folder
3. Update `.env` to point to it: `GOOGLE_APPLICATION_CREDENTIALS=bigquery-credentials.json`
4. Test with: `python test_bigquery_auth.py`

**For Project Admin:**
1. Go to [Google Cloud Console - Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Create service account with **BigQuery Data Editor** role
3. Generate and download JSON key
4. Share securely with team (encrypted email, secure file sharing)
5. **Never commit the JSON file to git!** (already in `.gitignore`)

---

## 🔥 Firebase Authentication Setup

The platform includes a secure login system for Public Health Officials using Firebase Authentication.

### **Quick Setup for Developers**

1. **Get the service account file** from your admin
2. **Store it securely**:
   ```bash
   mkdir -p ~/secrets/firebase
   mv firebase-adminsdk-xxxxx.json ~/secrets/firebase/service_account.json
   ```
3. **Update `.env`**:
   ```env
   FIREBASE_SERVICE_ACCOUNT_FILE=/Users/YOUR_USERNAME/secrets/firebase/service_account.json
   ```
4. **Install dependencies**: `pip install firebase-admin`
5. **Test**: `python app_local.py` (look for "[OK] Firebase Admin SDK initialized")
6. **Login**: http://localhost:8080/officials-login

### **For Complete Setup Instructions**

See **[FIREBASE_README.md](FIREBASE_README.md)** for:
- 📋 Complete developer setup guide
- 🔧 Admin guide (creating Firebase project, managing users)
- 🔄 Switching Firebase projects
- 🐛 Troubleshooting common issues
- 📚 Additional resources

---

## 🚀 Quick Start

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
