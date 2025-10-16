#!/usr/bin/env python3
"""
Test script for the multi-agent health data system.
This demonstrates the new architecture with a main coordinator agent
that routes to specialized sub-agents for air quality and infectious diseases.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'multi_tool_agent_bquery_tools'))

from agent import call_agent

def test_multi_agent_system():
    """Test the multi-agent system with various query types."""
    
    print("🏥 Multi-Agent Health Data System Test")
    print("=" * 50)
    
    # Test queries that should route to air quality agent
    air_quality_queries = [
        "What are the PM2.5 levels in Los Angeles County, California?",
        "Tell me about air pollution in New York",
        "Show me air quality data for Texas in 2020"
    ]
    
    # Test queries that should route to infectious diseases agent
    infectious_diseases_queries = [
        "What infectious diseases data is available for California?",
        "Show me diarrhea cases in Florida",
        "Tell me about waterborne diseases in Texas"
    ]
    
    # Test general queries that should be classified
    general_queries = [
        "I'm concerned about health issues in my area",
        "What health data do you have available?",
        "Help me understand environmental health risks"
    ]
    
    print("\n🌬️ Testing Air Quality Routing:")
    print("-" * 30)
    for query in air_quality_queries:
        print(f"\nUSER: {query}")
        try:
            response = call_agent(query)
            print(f"AGENT: {response[:200]}...")  # Truncate for readability
        except Exception as e:
            print(f"ERROR: {e}")
        print("-" * 50)
    
    print("\n🦠 Testing Infectious Diseases Routing:")
    print("-" * 30)
    for query in infectious_diseases_queries:
        print(f"\nUSER: {query}")
        try:
            response = call_agent(query)
            print(f"AGENT: {response[:200]}...")  # Truncate for readability
        except Exception as e:
            print(f"ERROR: {e}")
        print("-" * 50)
    
    print("\n🤖 Testing General Classification:")
    print("-" * 30)
    for query in general_queries:
        print(f"\nUSER: {query}")
        try:
            response = call_agent(query)
            print(f"AGENT: {response[:200]}...")  # Truncate for readability
        except Exception as e:
            print(f"ERROR: {e}")
        print("-" * 50)

if __name__ == "__main__":
    test_multi_agent_system()
