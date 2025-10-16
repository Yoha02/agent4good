#!/usr/bin/env python3
"""
Non-interactive test of the local agent demo.
"""

from demo_agent_local import process_query

def test_agent():
    """Run test queries to demonstrate the agent."""
    print("=" * 80)
    print("EPA AIR QUALITY AGENT - LOCAL DEMO TEST")
    print("=" * 80)
    print()
    
    test_queries = [
        "Hello!",
        "What are the PM2.5 levels in Los Angeles, California?",
        "Tell me about infectious diseases in Cook County, Illinois.",
        "Show me water safety tips.",
        "Are there any E. coli cases in Harris County, Texas?",
        "Check the air quality in Phoenix, Arizona.",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[Test {i}/{len(test_queries)}]")
        print(f"USER: {query}")
        print("-" * 80)
        response = process_query(query)
        print(f"AGENT:\n{response}")
        print("=" * 80)
    
    print("\n[SUCCESS] All tests completed successfully!")
    print("\n[TIP] To try interactive mode, run: python demo_agent_local.py")

if __name__ == "__main__":
    test_agent()

