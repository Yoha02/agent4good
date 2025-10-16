#!/usr/bin/env python3
"""
Interactive demo for the EPA Air Quality Agent using Google ADK BigQuery tools.
Run this script to interact with the agent in real-time.
"""

import sys
from multi_tool_agent.agent import call_agent

def print_banner():
    """Print a welcome banner."""
    print("=" * 80)
    print("🌬️  EPA AIR QUALITY AGENT - ADK BigQuery Implementation  🌬️")
    print("=" * 80)
    print("Query EPA historical air quality data using natural language!")
    print("Dataset: bigquery-public-data.epa_historical_air_quality.pm25_frm_daily_summary")
    print("Data coverage: 2010-2021 (cutoff: 2021-11-08)")
    print("\nExample queries:")
    print("• What datasets are available in the bigquery-public-data project?")
    print("• Tell me about the epa_historical_air_quality dataset")
    print("• What are the PM2.5 levels in Los Angeles County, California in 2020?")
    print("• Show me air quality data for Texas in 2019")
    print("• What's the air quality in Cook County, Illinois?")
    print("\nType 'quit', 'exit', or 'q' to exit.")
    print("=" * 80)

def main():
    """Main interactive loop."""
    print_banner()
    
    while True:
        try:
            # Get user input
            user_input = input("\n🤔 Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'q', '']:
                print("\n👋 Goodbye! Thanks for using the EPA Air Quality Agent!")
                break
            
            # Process the query
            print("\n🔍 Processing your query...")
            print("-" * 60)
            
            response = call_agent(user_input)
            
            print(f"\n🤖 Agent Response:")
            print(response)
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using the EPA Air Quality Agent!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    main()
