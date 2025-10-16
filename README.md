# Community Health & Wellness Advisor - Air Quality Monitoring Platform

An impactful, interactive web application that combines Google Cloud SDK agents, BigQuery database, and Gemini AI to provide real-time air quality monitoring and health recommendations.

![Platform Overview](https://img.shields.io/badge/Platform-Google_Cloud-4285F4?style=for-the-badge&logo=google-cloud)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask)
![BigQuery](https://img.shields.io/badge/BigQuery-Enabled-669DF6?style=for-the-badge&logo=google-cloud)

## 🌟 Features

- **Real-time Air Quality Monitoring**: Track AQI (Air Quality Index) across multiple locations
- **AI-Powered Health Insights**: Get personalized health recommendations using Gemini AI
- **Interactive Data Visualization**: Beautiful charts and graphs powered by Chart.js
- **BigQuery Integration**: Fast, scalable data queries from Google BigQuery
- **Google SDK Agents**: Intelligent agents for data analysis and health advisory
- **Responsive UI/UX**: Modern, mobile-friendly interface with smooth animations
- **Cloud Run Ready**: Optimized for deployment on Google Cloud Run

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │
│  (HTML/CSS/JS)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Flask App     │
│  (Python 3.11)  │
└────────┬────────┘
         │
         ├──────────────┐
         ▼              ▼
┌─────────────┐  ┌──────────────┐
│  BigQuery   │  │  Gemini AI   │
│  Database   │  │   (SDK)      │
└─────────────┘  └──────────────┘
```

## 📋 Prerequisites

- Python 3.11+
- Google Cloud Platform account
- Google Cloud Project with:
  - BigQuery API enabled
  - Cloud Run API enabled
  - Gemini API access
- Service account key with appropriate permissions

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Yoha02/agent4good.git
cd agent4good
```

### 2. Set Up Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
BIGQUERY_DATASET=air_quality_dataset
BIGQUERY_TABLE=air_quality_data
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=your-secret-key-here
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Run Locally

```bash
python app.py
```

Visit `http://localhost:8080` in your browser.

## ☁️ Deploy to Google Cloud Run

### Method 1: Using gcloud CLI

1. **Build and push the container:**

```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Build the container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/air-quality-advisor

# Deploy to Cloud Run
gcloud run deploy air-quality-advisor \
  --image gcr.io/YOUR_PROJECT_ID/air-quality-advisor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,BIGQUERY_DATASET=air_quality_dataset,BIGQUERY_TABLE=air_quality_data,GEMINI_API_KEY=YOUR_GEMINI_API_KEY"
```

2. **Access your deployed app:**

The deployment will provide a URL like: `https://air-quality-advisor-xxxxx.run.app`

### Method 2: Using Cloud Console

1. Go to [Google Cloud Run Console](https://console.cloud.google.com/run)
2. Click "CREATE SERVICE"
3. Select "Deploy one revision from an existing container image"
4. Build the container using Cloud Build:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/air-quality-advisor
   ```
5. Configure:
   - Service name: `air-quality-advisor`
   - Region: `us-central1`
   - Authentication: Allow unauthenticated invocations
   - Container port: `8080`
6. Add environment variables in "Variables & Secrets"
7. Click "CREATE"

## 📊 Setting Up BigQuery

### 1. Create Dataset and Table

```sql
-- Create dataset
CREATE SCHEMA IF NOT EXISTS air_quality_dataset;

-- Create table
CREATE TABLE IF NOT EXISTS air_quality_dataset.air_quality_data (
  date DATE,
  state_name STRING,
  county_name STRING,
  aqi INT64,
  parameter_name STRING,
  site_name STRING
);
```

### 2. Load CSV Data

```bash
# Upload your CSV file to BigQuery
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  air_quality_dataset.air_quality_data \
  daily_88101_2025.csv \
  date:DATE,state_name:STRING,county_name:STRING,aqi:INTEGER,parameter_name:STRING,site_name:STRING
```

Or use the BigQuery Console:
1. Go to BigQuery in Cloud Console
2. Select your dataset
3. Click "CREATE TABLE"
4. Upload the CSV file
5. Define schema matching the table structure above

## 🔑 Setting Up Service Account

1. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create air-quality-sa \
     --display-name "Air Quality Service Account"
   ```

2. **Grant Permissions:**
   ```bash
   # BigQuery permissions
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:air-quality-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.dataViewer"
   
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:air-quality-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/bigquery.jobUser"
   ```

3. **Download Key:**
   ```bash
   gcloud iam service-accounts keys create service-account-key.json \
     --iam-account=air-quality-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

## 🧪 Testing the Application

### Test Health Endpoint

```bash
curl https://your-app-url.run.app/health
```

### Test Air Quality API

```bash
curl "https://your-app-url.run.app/api/air-quality?days=7"
```

### Test AI Analysis

```bash
curl -X POST https://your-app-url.run.app/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the health risks of high AQI?", "days": 7}'
```

## 📁 Project Structure

```
agent4good/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── .dockerignore          # Docker ignore rules
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── static/
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       └── app.js        # Frontend JavaScript
└── templates/
    └── index.html        # Main HTML template
```

## 🎨 UI/UX Features

- **Gradient Backgrounds**: Eye-catching color schemes
- **Glass Morphism**: Modern translucent card designs
- **Smooth Animations**: Engaging transitions and effects
- **Responsive Design**: Works perfectly on all devices
- **Interactive Charts**: Real-time data visualization
- **AI Chat Interface**: Natural conversation with health advisor
- **Accessibility**: WCAG compliant design

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account key | Yes |
| `BIGQUERY_DATASET` | BigQuery dataset name | Yes |
| `BIGQUERY_TABLE` | BigQuery table name | Yes |
| `GEMINI_API_KEY` | Gemini AI API key | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `PORT` | Application port (default: 8080) | No |
| `FLASK_ENV` | Environment (production/development) | No |

## 🐛 Troubleshooting

### BigQuery Connection Issues

- Verify service account has proper permissions
- Check that BigQuery API is enabled
- Ensure dataset and table exist

### Gemini AI Issues

- Verify API key is correct
- Check API quota limits
- Ensure Gemini API is enabled in your project

### Cloud Run Deployment Issues

- Check container logs: `gcloud run services logs read air-quality-advisor`
- Verify environment variables are set correctly
- Ensure port 8080 is exposed in Dockerfile

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

Agents for Impact - Community Health & Wellness Initiative

## 🙏 Acknowledgments

- Google Cloud Platform for infrastructure
- Gemini AI for intelligent insights
- Chart.js for beautiful visualizations
- Flask community for excellent documentation

## 📞 Support

For questions or support, please open an issue in the GitHub repository.

---

**Built with ❤️ for Community Health & Wellness**

*Powered by Google Cloud, BigQuery, and Gemini AI*
