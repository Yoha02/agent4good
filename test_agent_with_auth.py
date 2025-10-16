#!/usr/bin/env python3
"""
Test the agent with real Google Cloud authentication.
This runs a series of queries to verify everything works.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')  # Fix Windows encoding

from multi_tool_agent.agent import call_agent

def test_agent():
    """Run test queries with real EPA data."""
    print("=" * 80)
    print("EPA AIR QUALITY AGENT - TESTING WITH REAL EPA DATA")
    print("=" * 80)
    print()
    
    test_queries = [
        "What datasets are available in the bigquery-public-data project?",
        "Tell me about the epa_historical_air_quality dataset",
        "What are the PM2.5 levels in Los Angeles County, California in 2020?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}/{len(test_queries)}]")
        print(f"USER: {query}")
        print("-" * 80)
        
        try:
            response = call_agent(query)
            print(f"AGENT:\n{response}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")
        
        print("=" * 80)
    
    print("\n[SUCCESS] Tests completed!")
    print("\nTo run interactive mode: python interactive_demo.py")

if __name__ == "__main__":
    try:
        test_agent()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

