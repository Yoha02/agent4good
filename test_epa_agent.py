#!/usr/bin/env python3
"""
Test script for the EPA Air Quality Agent using Google ADK BigQuery tools.
This script demonstrates the agent's capabilities with the EPA historical air quality dataset.
"""

import asyncio
from multi_tool_agent.agent import call_agent, run_epa_air_quality_queries

def main():
    """Main function to test the EPA air quality agent."""
    print("=" * 80)
    print("EPA AIR QUALITY AGENT - ADK BigQuery Implementation Test")
    print("=" * 80)
    
    # Test individual queries
    test_queries = [
        "What datasets are available in the bigquery-public-data project?",
        "Tell me about the epa_historical_air_quality dataset.",
        "What tables are available in the epa_historical_air_quality dataset?",
        "Get information about the pm25_frm_daily_summary table.",
        "What are the PM2.5 levels in Los Angeles County, California in 2020?",
        "Show me the air quality data for Cook County, Illinois for the last 30 days from the data cutoff.",
        "What is the average PM2.5 concentration in Texas in 2019?"
    ]
    
    print("\nTesting individual queries:")
    print("-" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Query {i}]")
        print(f"USER: {query}")
        try:
            response = call_agent(query)
            print(f"AGENT: {response}")
        except Exception as e:
            print(f"ERROR: {str(e)}")
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80)

if __name__ == "__main__":
    main()
