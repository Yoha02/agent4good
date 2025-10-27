#!/usr/bin/env python3
"""
CI/CD Status Checker
Check GitHub Actions workflow status and deployment info
"""

import subprocess
import json
import sys

GH_PATH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "Yoha02/agent4good"

def run_gh(args):
    """Run GitHub CLI command"""
    try:
        result = subprocess.run(
            [GH_PATH] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None

def check_workflows():
    """Check status of workflows"""
    print("=" * 60)
    print("🔍 GitHub Actions Workflows Status")
    print("=" * 60)
    
    output = run_gh(['run', 'list', '--repo', REPO, '--limit', '10', '--json', 
                     'displayTitle,status,conclusion,headBranch,createdAt'])
    
    if not output:
        print("❌ Could not fetch workflow runs")
        return
    
    runs = json.loads(output)
    
    for run in runs:
        status = run['status']
        conclusion = run.get('conclusion', 'in_progress')
        title = run['displayTitle']
        branch = run['headBranch']
        
        if status == 'completed':
            if conclusion == 'success':
                emoji = "✅"
            elif conclusion == 'failure':
                emoji = "❌"
            else:
                emoji = "⚠️"
        else:
            emoji = "🔄"
        
        print(f"{emoji} {title}")
        print(f"   Branch: {branch} | Status: {status} | Result: {conclusion}")
        print()

def check_secrets():
    """Check configured secrets"""
    print("=" * 60)
    print("🔐 GitHub Secrets Status")
    print("=" * 60)
    
    output = run_gh(['secret', 'list', '--repo', REPO])
    
    if not output:
        print("❌ Could not fetch secrets")
        return
    
    secrets = []
    for line in output.split('\n'):
        if line.strip() and not line.startswith('NAME'):
            parts = line.split()
            if parts:
                secrets.append(parts[0])
    
    required = [
        'GOOGLE_API_KEY',
        'GEMINI_API_KEY',
        'EPA_API_KEY',
        'GOOGLE_CLOUD_PROJECT',
        'GCP_SERVICE_ACCOUNT_KEY'
    ]
    
    print(f"Total secrets configured: {len(secrets)}")
    print()
    
    for secret in required:
        if secret in secrets:
            print(f"✅ {secret}")
        else:
            print(f"❌ {secret} (MISSING)")
    
    print()

def check_deployment():
    """Check last deployment"""
    print("=" * 60)
    print("🚀 Last Deployment Status")
    print("=" * 60)
    
    output = run_gh(['run', 'list', '--workflow=deploy.yml', '--repo', REPO, 
                     '--limit', '1', '--json', 'status,conclusion,headBranch,createdAt,url'])
    
    if not output:
        print("❌ No deployments found")
        return
    
    runs = json.loads(output)
    if not runs:
        print("❌ No deployments found")
        return
    
    last_run = runs[0]
    status = last_run['status']
    conclusion = last_run.get('conclusion', 'in_progress')
    branch = last_run['headBranch']
    url = last_run['url']
    
    print(f"Branch: {branch}")
    print(f"Status: {status}")
    print(f"Result: {conclusion}")
    print(f"URL: {url}")
    print()

def main():
    print()
    check_workflows()
    check_secrets()
    check_deployment()
    
    print("=" * 60)
    print("💡 To view detailed logs:")
    print(f"   Visit: https://github.com/{REPO}/actions")
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
