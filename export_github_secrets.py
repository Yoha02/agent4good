#!/usr/bin/env python3
"""
GitHub Secrets Importer - Uses GitHub Workflow Run to Fetch Secrets
This triggers a workflow that exports secrets to a file you can download
"""

import subprocess
import sys
import time
import json

GH_PATH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "Yoha02/agent4good"

def create_workflow_file():
    """Create a GitHub Actions workflow to export secrets"""
    
    workflow_content = """name: Export Secrets to File
on:
  workflow_dispatch:

jobs:
  export-secrets:
    runs-on: ubuntu-latest
    steps:
      - name: Create secrets env file
        run: |
          cat > secrets.env << EOF
          GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}
          GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}
          EPA_API_KEY=${{ secrets.EPA_API_KEY }}
          AQS_API_KEY=${{ secrets.AQS_API_KEY }}
          AQS_EMAIL=${{ secrets.AQS_EMAIL }}
          GOOGLE_CLOUD_PROJECT=${{ secrets.GOOGLE_CLOUD_PROJECT }}
          BIGQUERY_DATASET=${{ secrets.BIGQUERY_DATASET }}
          BIGQUERY_TABLE_REPORTS=${{ secrets.BIGQUERY_TABLE_REPORTS }}
          SECRET_KEY=${{ secrets.SECRET_KEY }}
          PORT=${{ secrets.PORT }}
          GCS_VIDEO_BUCKET=${{ secrets.GCS_VIDEO_BUCKET }}
          TWITTER_API_KEY=${{ secrets.TWITTER_API_KEY }}
          TWITTER_API_SECRET=${{ secrets.TWITTER_API_SECRET }}
          TWITTER_ACCESS_TOKEN=${{ secrets.TWITTER_ACCESS_TOKEN }}
          TWITTER_ACCESS_TOKEN_SECRET=${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }}
          TWITTER_BEARER_TOKEN=${{ secrets.TWITTER_BEARER_TOKEN }}
          TWITTER_USERNAME=${{ secrets.TWITTER_USERNAME }}
          EOF
          
      - name: Upload secrets file
        uses: actions/upload-artifact@v3
        with:
          name: secrets-env-file
          path: secrets.env
          retention-days: 1
"""
    
    with open('.github/workflows/export-secrets.yml', 'w') as f:
        f.write(workflow_content)
    
    print("✅ Created workflow file: .github/workflows/export-secrets.yml")
    return True

def trigger_workflow():
    """Trigger the workflow to export secrets"""
    print("🚀 Triggering workflow to export secrets...")
    
    result = subprocess.run(
        [GH_PATH, 'workflow', 'run', 'export-secrets.yml', '--repo', REPO],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Workflow triggered successfully")
        return True
    else:
        print(f"❌ Failed to trigger workflow: {result.stderr}")
        return False

def wait_for_workflow():
    """Wait for workflow to complete"""
    print("⏳ Waiting for workflow to complete...")
    
    for i in range(30):  # Wait up to 5 minutes
        result = subprocess.run(
            [GH_PATH, 'run', 'list', '--workflow=export-secrets.yml', '--repo', REPO, '--limit', '1', '--json', 'status'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            runs = json.loads(result.stdout)
            if runs and runs[0]['status'] == 'completed':
                print("✅ Workflow completed")
                return True
        
        time.sleep(10)
        print(f"⏳ Still waiting... ({i * 10}s)")
    
    print("❌ Workflow timed out")
    return False

def download_artifact():
    """Download the secrets file"""
    print("📥 Downloading secrets file...")
    
    result = subprocess.run(
        [GH_PATH, 'run', 'download', '--repo', REPO, '--name', 'secrets-env-file'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Downloaded secrets file")
        return True
    else:
        print(f"❌ Failed to download: {result.stderr}")
        return False

def main():
    print("="*60)
    print("🔐 GitHub Secrets Exporter via Workflow")
    print("="*60)
    print()
    print("⚠️  WARNING: This creates a file with your secrets!")
    print("    Make sure to delete it after copying to .env")
    print()
    
    choice = input("Do you want to continue? (yes/no): ")
    if choice.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Step 1: Create workflow file
    if not create_workflow_file():
        return
    
    print()
    print("📝 Next steps:")
    print("1. Commit and push the workflow file:")
    print("   git add .github/workflows/export-secrets.yml")
    print("   git commit -m 'Add secrets export workflow'")
    print("   git push")
    print()
    print("2. Then run this script again to trigger the workflow")
    
if __name__ == "__main__":
    main()
