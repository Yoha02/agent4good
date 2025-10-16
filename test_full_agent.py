#!/usr/bin/env python3
"""
Test the full agent with Gemini API and BigQuery.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from multi_tool_agent.agent import call_agent

def test_full_agent():
    """Test the agent with various queries."""
    print("=" * 80)
    print("TESTING FULL AGENT WITH GEMINI API + BIGQUERY")
    print("=" * 80)
    print()
    
    queries = [
        "Hello! What can you help me with?",
        "What datasets are available in bigquery-public-data?",
        "Tell me about the epa_historical_air_quality dataset",
        "What tables are in the epa_historical_air_quality dataset?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n[Query {i}/{len(queries)}]")
        print(f"USER: {query}")
        print("-" * 80)
        
        try:
            response = call_agent(query)
            print(f"AGENT: {response}")
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            break
        except Exception as e:
            print(f"[ERROR] {str(e)}")
        
        print("=" * 80)
    
    print("\n[COMPLETE] All queries processed!")
    print("\nTo try interactive mode in your terminal, run:")
    print("  python interactive_demo.py")

if __name__ == "__main__":
    try:
        test_full_agent()
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

