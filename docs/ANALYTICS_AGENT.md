# Analytics Agent Documentation

## Overview

The **Analytics Agent** is a specialized sub-agent that performs cross-dataset analysis on air quality and infectious disease data using Python code execution. It can handle complex analytical queries that span multiple data sources.

## Capabilities

### Data Sources
1. **Historical Air Quality** - EPA Historical Air Quality dataset (PM2.5, AQI)
2. **Live Air Quality** - Real-time AirNow API data
3. **Infectious Disease** - CDC BEAM disease surveillance data

### Analysis Types
- Cross-dataset correlations
- Temporal pattern analysis
- Geographic comparisons
- Trend analysis and forecasting
- Statistical modeling
- Data visualization

## Architecture

### Tools
The agent has access to three data retrieval tools:
- `get_air_quality()` - Historical EPA data
- `get_live_air_quality()` - Current air quality readings
- `get_infectious_disease_data()` - CDC disease data

### Code Execution
Uses `VertexAiCodeExecutor` to:
- Execute Python code in a stateful environment
- Run data analysis and visualizations
- Maintain state across multiple code executions

## Example Queries

### Cross-Dataset Analysis
```
"Analyze the correlation between air quality and respiratory diseases in California"
```

### Temporal Analysis
```
"Show me trends in air quality vs disease rates over the past year"
```

### Geographic Comparison
```
"Compare air quality and disease patterns across different states"
```

## Files Created

1. `multi_tool_agent_bquery_tools/agents/analytics_agent.py` - Main agent definition
2. `multi_tool_agent_bquery_tools/agents/analytics_prompts.py` - Instruction prompts
3. `multi_tool_agent_bquery_tools/agent.py` - Updated to include analytics agent

## Integration

The analytics agent is automatically integrated into the root agent's sub-agents list and will be routed to when users ask analytical questions spanning multiple datasets.
