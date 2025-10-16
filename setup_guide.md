# BigQuery EPA Air Quality Agent Setup Guide

This guide will help you set up the BigQuery EPA Air Quality Agent using Google's Agent Development Kit (ADK).

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with BigQuery API enabled
2. **Authentication**: Set up authentication using one of the methods below
3. **Python Environment**: Python 3.8+ with pip

## Important: Project Configuration

**⚠️ CRITICAL**: You must set your own Google Cloud project ID as an environment variable:

```bash
export GOOGLE_CLOUD_PROJECT="your-actual-project-id"
```

**Why this is needed**: The `bigquery-public-data` project is read-only. BigQuery jobs are created in YOUR project, but they can query public datasets.

## Authentication Setup

### Option 1: Application Default Credentials (Recommended for local development)

```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate with your Google account
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### Option 2: Service Account (Recommended for production)

1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

### Option 3: OAuth 2.0 (For user-facing applications)

Set these environment variables:
```bash
export OAUTH_CLIENT_ID="your-client-id"
export OAUTH_CLIENT_SECRET="your-client-secret"
```

## Installation

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Verify BigQuery access**:
```bash
# Test BigQuery connection
python -c "
from google.cloud import bigquery
client = bigquery.Client()
print('BigQuery connection successful!')
"
```

## Running the Agent

### Basic Usage

```python
from multi_tool_agent_bquery_tools.agent import call_agent

# Example queries
response = call_agent("What datasets are available in bigquery-public-data?")
print(response)

response = call_agent("What are the PM2.5 levels in Los Angeles County, California in 2020?")
print(response)
```

### Interactive Demo

```bash
python multi_tool_agent_bquery_tools/agent.py
```

## Available Functions

The agent includes these custom functions:

1. **`get_air_quality()`** - Retrieve air quality data by location and date
2. **`get_metadata()`** - Get information about available states, counties, and cities
3. **`get_table_schema()`** - Get the schema of the EPA air quality table
4. **`test_table_columns()`** - Test what columns are available in the table
5. **`get_current_time()`** - Get current time for specific cities

## BigQuery Tools Available

The agent has access to these BigQuery ADK tools:

- `list_dataset_ids` - List available datasets
- `get_dataset_info` - Get dataset metadata
- `list_table_ids` - List tables in a dataset
- `get_table_info` - Get table metadata
- `execute_sql` - Execute SQL queries
- `forecast` - Generate forecasts
- `ask_data_insights` - Get data insights

## Example Queries

```python
# Dataset exploration
"What datasets are available in qwiklabs-gcp-00-86088b6278cb?"
"Tell me about the BQ_EPA_Air_Data dataset"
"What tables are in the BQ_EPA_Air_Data dataset?"

# Air quality queries
"What are the PM2.5 levels in Los Angeles County, California in 2020?"
"Show me air quality data for Cook County, Illinois"
"What is the average PM2.5 concentration in Texas in 2019?"
"Get air quality data for the last 30 days in New York"

# Schema and metadata
"What columns are available in the pm25_frm_daily_summary table?"
"What states have air quality monitoring data?"
```

## Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure you're authenticated with `gcloud auth application-default login`
2. **Permission Denied**: Ensure your account has BigQuery Data Viewer role
3. **Import Error**: Install all dependencies with `pip install -r requirements.txt`

### BigQuery Job Creation Error (403 Access Denied)

**Error**: `Access Denied: Project bigquery-public-data: User does not have bigquery.jobs.create permission`

**Solution**: 
1. Set your own project ID: `export GOOGLE_CLOUD_PROJECT="your-project-id"`
2. Ensure your project has BigQuery API enabled
3. Make sure you have BigQuery Job User role in your project

**Why this happens**: You cannot create jobs in `bigquery-public-data` (it's read-only). Jobs must be created in your own project.

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Data Source

The agent queries the EPA Historical Air Quality dataset:
- **Project**: `qwiklabs-gcp-00-86088b6278cb`
- **Dataset**: `BQ_EPA_Air_Data`
- **Table**: `pm25_frm_daily_summary`

This dataset contains PM2.5 air quality measurements from monitoring stations across the United States from 2010-2021.

## Support

For issues with:
- **Google ADK**: Check the [ADK documentation](https://cloud.google.com/blog/products/ai-machine-learning/bigquery-meets-google-adk-and-mcp)
- **BigQuery**: Check the [BigQuery documentation](https://cloud.google.com/bigquery/docs)
- **Authentication**: Check the [Google Auth documentation](https://google-auth.readthedocs.io/)
