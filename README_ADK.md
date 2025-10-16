# EPA Air Quality Agent - ADK BigQuery Implementation

This project implements an intelligent agent for querying EPA historical air quality data using Google's Agent Development Kit (ADK) BigQuery tools. The agent provides flexible querying capabilities for PM2.5 air quality data from the EPA's BigQuery dataset.

## Features

- **ADK BigQuery Integration**: Uses Google ADK BigQuery tools for efficient data querying
- **Flexible Location Queries**: Query by state, county, or city with intelligent state inference
- **Date Filtering**: Support for specific dates, months, years, or relative date queries
- **Health Impact Assessment**: Automatic categorization of air quality based on EPA standards
- **Rich Metadata**: Access to monitoring site information, coordinates, and AQI values

## Dataset Information

- **Project**: `bigquery-public-data`
- **Dataset**: `epa_historical_air_quality`
- **Table**: `pm25_frm_daily_summary`
- **Data Coverage**: 2010-2021 (data cutoff: 2021-11-08)
- **Measurements**: PM2.5 concentrations, AQI values, monitoring site details

## ADK BigQuery Tools Used

The agent utilizes the following BigQuery tools from the ADK:

1. **list_dataset_ids**: Lists available datasets in a project
2. **get_dataset_info**: Retrieves metadata about a dataset
3. **list_table_ids**: Lists tables in a dataset
4. **get_table_info**: Retrieves table schema and metadata
5. **execute_sql**: Executes SQL queries and returns results
6. **forecast**: AI-powered time series forecasting (available)
7. **ask_data_insights**: Natural language data insights (available)

## Setup

### Prerequisites

- **Python 3.8+** (Required - uses type hints, f-strings, and other Python 3 features)
- Google Cloud credentials configured (Application Default Credentials)
- Access to BigQuery public datasets
- Google ADK packages installed

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud credentials:
```bash
gcloud auth application-default login
```

### Configuration

The agent is configured with:
- **Write Mode**: `BLOCKED` (read-only access)
- **Credentials**: Application Default Credentials
- **Model**: `gemini-2.0-flash`

## Usage

### Basic Usage

```python
from multi_tool_agent.agent import call_agent

# Query air quality data
response = call_agent("What are the PM2.5 levels in Los Angeles County, California in 2020?")
print(response)
```

### Example Queries

1. **Dataset Information**:
   - "What datasets are available in the bigquery-public-data project?"
   - "Tell me about the epa_historical_air_quality dataset."

2. **Table Information**:
   - "What tables are available in the epa_historical_air_quality dataset?"
   - "Get information about the pm25_frm_daily_summary table."

3. **Location-based Queries**:
   - "What are the PM2.5 levels in Los Angeles County, California in 2020?"
   - "Show me air quality data for Texas in 2019."
   - "What's the air quality in Cook County, Illinois?"

4. **Date-based Queries**:
   - "Show me the air quality data for the last 30 days from the data cutoff."
   - "What was the air quality in 2019?"
   - "Show me data for January 2020."

### Running the Test Script

```bash
python3 test_epa_agent.py
```

### Running the Interactive Demo

```bash
python3 interactive_demo.py
```

## Agent Capabilities

### Intelligent State Inference
- Automatically infers state from county names
- Handles ambiguous county names (e.g., Orange County exists in multiple states)
- Provides clear error messages for clarification

### Flexible Date Queries
- Specific dates: "2020-01-15"
- Year and month: "2020-01"
- Year only: "2020"
- Relative dates: "last 30 days" (calculated from 2021-11-08 cutoff)

### Health Impact Assessment
The agent automatically categorizes air quality based on EPA standards:
- **Good** (≤12.0 μg/m³): Satisfactory air quality
- **Moderate** (12.1-35.4 μg/m³): Acceptable for most people
- **Unhealthy for Sensitive Groups** (35.5-55.4 μg/m³): Sensitive groups may experience health effects
- **Unhealthy** (55.5-150.4 μg/m³): Everyone may experience health effects
- **Very Unhealthy** (>150.4 μg/m³): Health alert for everyone

### Rich Data Output
Each query returns:
- Average PM2.5 concentration
- Air quality category and health impact
- Recent readings from monitoring sites
- Site locations, coordinates, and addresses
- AQI values where available

## Architecture

The agent combines:
1. **ADK BigQuery Tools**: For efficient data querying and metadata access
2. **Custom Functions**: For specialized air quality analysis and health impact assessment
3. **Semantic Layer**: Metadata about available locations and data coverage
4. **State Inference Logic**: Intelligent county-to-state mapping

## Error Handling

The agent provides comprehensive error handling for:
- Invalid locations or ambiguous county names
- Date ranges outside available data
- BigQuery connection issues
- Missing or invalid data

## Troubleshooting

### Common Issues

1. **"name 'asyncio' is not defined"**: 
   - Ensure you're using Python 3.8+ (`python3 --version`)
   - Run with `python3` instead of `python`

2. **"ModuleNotFoundError: No module named 'google.adk'"**:
   - Install the Google ADK packages: `pip3 install -r requirements.txt`
   - Ensure you have the latest versions of Google ADK packages

3. **Authentication errors**:
   - Run `gcloud auth application-default login`
   - Ensure your Google Cloud project has BigQuery access

4. **Import errors**:
   - Make sure you're in the correct directory
   - Use `python3` instead of `python` for all commands

### Testing the Installation

```bash
# Test basic import
python3 -c "from multi_tool_agent.agent import call_agent; print('✅ Module imported successfully!')"

# Test with a simple query (requires ADK packages installed)
python3 -c "from multi_tool_agent.agent import call_agent; print(call_agent('Hello, agent!'))"
```

## Future Enhancements

- Integration with BigQuery AI forecasting capabilities
- Natural language data insights using `ask_data_insights`
- Support for additional EPA datasets
- Real-time data integration
- Advanced analytics and trend analysis

## License

Copyright 2025 Google LLC. Licensed under the Apache License, Version 2.0.
