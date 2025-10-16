# Agent SDK Integration Guide

## Overview

This project now includes **two complementary systems**:

1. **Web Application** - Flask-based air quality monitoring dashboard
2. **Agent SDK System** - Google ADK-powered intelligent agents for data querying

## 🎯 Quick Start

### Web Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run the web app
python app_epa.py

# Visit http://localhost:8080
```

### Agent SDK (ADK)
```bash
# Install dependencies (includes ADK packages)
pip install -r requirements.txt

# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Run interactive agent demo
python interactive_demo.py
```

## 📁 Project Structure

```
agent4good/
├── Web Application Files
│   ├── app.py                      # Basic Flask app
│   ├── app_epa.py                  # EPA BigQuery-connected app
│   ├── app_hybrid.py               # Hybrid implementation
│   ├── app_integrated.py           # Integrated platform
│   ├── templates/                  # HTML templates
│   └── static/                     # CSS, JS, assets
│
├── Agent SDK Files (NEW!)
│   ├── multi_tool_agent/           # Basic ADK agent
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── multi_tool_agent_bquery_tools/  # Advanced ADK agent with BigQuery tools
│   │   ├── __init__.py
│   │   └── agent.py
│   ├── agent_working.py            # Standalone working agent
│   ├── interactive_demo.py         # Interactive CLI demo
│   ├── test_epa_agent.py           # Agent tests
│   ├── test_bigquery_agent.py      # BigQuery agent tests
│   └── test_multi_agent_system.py  # Multi-agent tests
│
└── Documentation
    ├── README.md                   # Main project readme
    ├── README_ADK.md               # ADK-specific documentation
    ├── setup_guide.md              # Setup instructions
    └── AGENT_SDK_GUIDE.md          # This file
```

## 🤖 Agent SDK Features

### 1. Multi-Tool Agent (`multi_tool_agent/`)
- Basic ADK implementation
- Custom functions for EPA data
- County-to-state mapping intelligence
- Natural language query processing

### 2. BigQuery Tools Agent (`multi_tool_agent_bquery_tools/`)
- Advanced ADK with BigQuery toolset
- Access to BigQuery native tools:
  - `list_dataset_ids`
  - `get_dataset_info`
  - `list_table_ids`
  - `get_table_info`
  - `execute_sql`
  - `forecast`
  - `ask_data_insights`
- Enhanced querying capabilities
- Metadata exploration

### 3. Standalone Working Agent (`agent_working.py`)
- Self-contained agent implementation
- Can be run independently
- Good for testing and debugging

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Required for Agent SDK
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"  # Optional

# Optional for Web App
export BIGQUERY_DATASET="BQ_EPA_Air_Data"
export BIGQUERY_TABLE="pm25_frm_daily_summary"
export GEMINI_API_KEY="your-gemini-api-key"
export SECRET_KEY="your-secret-key"
```

### Authentication Methods

#### Method 1: Application Default Credentials (Recommended for Development)
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

#### Method 2: Service Account (Recommended for Production)
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

## 📊 Data Sources

### EPA Historical Air Quality Data
- **Project**: `bigquery-public-data`
- **Dataset**: `epa_historical_air_quality`
- **Table**: `pm25_frm_daily_summary`
- **Coverage**: 2010-2021 (cutoff: 2021-11-08)

### Alternative: Your Project Dataset
- **Project**: `qwiklabs-gcp-00-86088b6278cb` (or your project)
- **Dataset**: `BQ_EPA_Air_Data`
- **Table**: `pm25_frm_daily_summary`

## 🚀 Usage Examples

### Using the Agent SDK

#### Example 1: Basic Query
```python
from multi_tool_agent.agent import call_agent

response = call_agent("What are the PM2.5 levels in Los Angeles County, California in 2020?")
print(response)
```

#### Example 2: Dataset Exploration
```python
from multi_tool_agent_bquery_tools.agent import call_agent

# List available datasets
response = call_agent("What datasets are available in bigquery-public-data?")

# Get dataset info
response = call_agent("Tell me about the epa_historical_air_quality dataset")

# List tables
response = call_agent("What tables are in the epa_historical_air_quality dataset?")
```

#### Example 3: Interactive Mode
```bash
python interactive_demo.py
```

Example queries in interactive mode:
- "What are the PM2.5 levels in Los Angeles County, California in 2020?"
- "Show me air quality data for Texas in 2019"
- "What's the air quality in Cook County, Illinois?"
- "Tell me about the epa_historical_air_quality dataset"

### Running Tests

```bash
# Test EPA agent
python test_epa_agent.py

# Test BigQuery agent
python test_bigquery_agent.py

# Test multi-agent system
python test_multi_agent_system.py
```

## 🎨 Agent Capabilities

### Natural Language Understanding
The agents can understand queries like:
- "What's the air quality in Los Angeles?"
- "Show me PM2.5 levels for California in 2020"
- "Tell me about air quality in Cook County"
- "What datasets are available?"

### Intelligent State Inference
- Automatically infers state from county names
- Handles ambiguous counties (e.g., Orange County exists in CA and FL)
- Provides clear error messages for clarification

### Health Impact Assessment
Automatically categorizes air quality:
- **Good** (≤12.0 μg/m³): Satisfactory air quality
- **Moderate** (12.1-35.4 μg/m³): Acceptable for most people
- **Unhealthy for Sensitive Groups** (35.5-55.4 μg/m³): Sensitive groups affected
- **Unhealthy** (55.5-150.4 μg/m³): Everyone may be affected
- **Very Unhealthy** (>150.4 μg/m³): Health alert

### Flexible Date Queries
- Specific dates: "2020-01-15"
- Year and month: "2020-01"
- Year only: "2020"
- Relative dates: "last 30 days"

## 🔄 Integration Options

### Option 1: Use Agents in Web App
Integrate the agent SDK into the Flask web application:

```python
from multi_tool_agent_bquery_tools.agent import call_agent

@app.route('/api/agent-query', methods=['POST'])
def agent_query():
    """API endpoint for agent queries"""
    data = request.get_json()
    question = data.get('question', '')
    
    response = call_agent(question)
    
    return jsonify({
        'success': True,
        'response': response
    })
```

### Option 2: Standalone Agent Service
Run the agent as a standalone service and call it from the web app via API.

### Option 3: Dual System
Use both systems independently:
- Web app for visualization and dashboards
- Agent SDK for advanced queries and analysis

## 🐛 Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'google.adk'"
```bash
pip install google-adk
```

#### 2. "Access Denied: Project bigquery-public-data"
Set your own project ID:
```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

#### 3. "name 'asyncio' is not defined"
Use Python 3.8+:
```bash
python3 --version  # Should be 3.8 or higher
python3 interactive_demo.py  # Use python3 instead of python
```

#### 4. Authentication Error
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

#### 5. BigQuery Permission Error
Ensure your account/service account has:
- `BigQuery Data Viewer` role
- `BigQuery Job User` role

## 📚 Additional Resources

- [README_ADK.md](README_ADK.md) - Detailed ADK implementation guide
- [setup_guide.md](setup_guide.md) - Complete setup instructions
- [README.md](README.md) - Main project documentation
- [Google ADK Documentation](https://cloud.google.com/blog/products/ai-machine-learning/bigquery-meets-google-adk-and-mcp)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)

## 🎓 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Authenticate**: `gcloud auth application-default login`
3. **Set project**: `export GOOGLE_CLOUD_PROJECT="your-project-id"`
4. **Try the interactive demo**: `python interactive_demo.py`
5. **Run tests**: `python test_epa_agent.py`
6. **Integrate into web app**: Add agent endpoints to Flask app
7. **Deploy**: Use Cloud Run or your preferred platform

## 🤝 Contributing

Both the web application and agent SDK are modular and extensible:
- Add new agent capabilities in `multi_tool_agent/agent.py`
- Extend BigQuery tools in `multi_tool_agent_bquery_tools/agent.py`
- Add new web endpoints in `app_epa.py` or `app_integrated.py`
- Create new visualizations in `templates/` and `static/`

## 📄 License

Copyright 2025 Google LLC. Licensed under the Apache License, Version 2.0.

---

**Built with ❤️ for Community Health & Wellness**

*Combining traditional web interfaces with cutting-edge AI agents for maximum impact*

