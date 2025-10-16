#!/usr/bin/env python3
"""
Quick setup script to fix the BigQuery project configuration issue
"""

import os
import subprocess
import sys

def get_current_project():
    """Get the current Google Cloud project."""
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def set_environment_variable(project_id):
    """Set the GOOGLE_CLOUD_PROJECT environment variable."""
    os.environ['GOOGLE_CLOUD_PROJECT'] = project_id
    print(f"✅ Set GOOGLE_CLOUD_PROJECT={project_id}")

def main():
    print("🔧 BigQuery Project Configuration Fix")
    print("=" * 40)
    
    # Get current project
    current_project = get_current_project()
    
    if current_project:
        print(f"📋 Current Google Cloud project: {current_project}")
        set_environment_variable(current_project)
        
        print(f"\n✅ Configuration complete!")
        print(f"   Your BigQuery jobs will be created in: {current_project}")
        print(f"   Public datasets will be queried from: bigquery-public-data")
        
        # Test the configuration
        print(f"\n🧪 Testing configuration...")
        try:
            from multi_tool_agent_bquery_tools.agent import call_agent
            response = call_agent("What datasets are available in bigquery-public-data?")
            print(f"✅ Test successful! Agent is working.")
        except Exception as e:
            print(f"❌ Test failed: {str(e)}")
            print(f"   Make sure you're authenticated: gcloud auth application-default login")
    else:
        print("❌ No Google Cloud project found!")
        print("\n🔧 Setup steps:")
        print("1. Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install")
        print("2. Authenticate: gcloud auth login")
        print("3. Set project: gcloud config set project YOUR_PROJECT_ID")
        print("4. Enable BigQuery API: gcloud services enable bigquery.googleapis.com")
        print("5. Run this script again")

if __name__ == "__main__":
    main()
