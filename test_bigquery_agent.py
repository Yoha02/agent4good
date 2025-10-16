#!/usr/bin/env python3
"""
Test script for the BigQuery EPA Air Quality Agent
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_tool_agent_bquery_tools.agent import call_agent

def test_basic_queries():
    """Test basic agent functionality with sample queries."""
    
    print("🧪 Testing BigQuery EPA Air Quality Agent")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "What datasets are available in the qwiklabs-gcp-00-86088b6278cb project?",
        "Tell me about the BQ_EPA_Air_Data dataset.",
        "What tables are available in the BQ_EPA_Air_Data dataset?",
        "Get information about the pm25_frm_daily_summary table.",
        "What are the PM2.5 levels in Los Angeles County, California in 2020?",
        "Show me the air quality data for Cook County, Illinois for the last 30 days from the data cutoff.",
        "What is the average PM2.5 concentration in Texas in 2019?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        try:
            response = call_agent(query)
            print(f"✅ Response: {response[:200]}...")
            if len(response) > 200:
                print("   (Response truncated for display)")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print()

def test_authentication():
    """Test authentication setup."""
    print("🔐 Testing Authentication")
    print("=" * 30)
    
    try:
        import google.auth
        credentials, project = google.auth.default()
        print(f"✅ Authentication successful!")
        print(f"   Project: {project}")
        print(f"   Credentials type: {type(credentials).__name__}")
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        print("   Please run: gcloud auth application-default login")

def test_bigquery_connection():
    """Test BigQuery connection."""
    print("\n🔗 Testing BigQuery Connection")
    print("=" * 35)
    
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        
        # Test query
        query = """
        SELECT COUNT(*) as total_rows
        FROM `qwiklabs-gcp-00-86088b6278cb.BQ_EPA_Air_Data.pm25_frm_daily_summary`
        LIMIT 1
        """
        
        result = client.query(query).result()
        for row in result:
            print(f"✅ BigQuery connection successful!")
            print(f"   Total rows in EPA dataset: {row.total_rows}")
            
    except Exception as e:
        print(f"❌ BigQuery connection failed: {str(e)}")
        print("   Please check your authentication and permissions")

if __name__ == "__main__":
    print("🚀 BigQuery EPA Air Quality Agent Test Suite")
    print("=" * 50)
    
    # Test authentication
    test_authentication()
    
    # Test BigQuery connection
    test_bigquery_connection()
    
    # Test agent queries
    print("\n" + "=" * 50)
    test_basic_queries()
    
    print("\n🎉 Test suite completed!")
    print("\nTo run the agent interactively, use:")
    print("python multi_tool_agent_bquery_tools/agent.py")
