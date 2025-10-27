#!/usr/bin/env python3
"""
GitHub Secrets Fetcher for Local Development

This script helps fetch GitHub secrets for local development.
It requires GitHub CLI (gh) to be installed and authenticated.

Installation:
1. Install GitHub CLI: https://cli.github.com/
2. Authenticate: gh auth login
3. Run this script: python fetch_github_secrets.py

Security Note: This is for development convenience only.
Never commit the generated .env file to git.
"""

import subprocess
import json
import os
import sys
from pathlib import Path

def check_github_cli():
    """Check if GitHub CLI is installed and authenticated"""
    try:
        result = subprocess.run(['gh', 'auth', 'status'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ GitHub CLI not authenticated. Please run: gh auth login")
            return False
        print("✅ GitHub CLI is authenticated")
        return True
    except FileNotFoundError:
        print("❌ GitHub CLI not found. Please install it from: https://cli.github.com/")
        print("   Windows: winget install --id GitHub.cli")
        print("   Or download from: https://github.com/cli/cli/releases")
        return False

def get_repo_info():
    """Get current repository information"""
    try:
        result = subprocess.run(['gh', 'repo', 'view', '--json', 'owner,name'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Not in a GitHub repository or no access")
            return None
        
        repo_info = json.loads(result.stdout)
        repo_name = f"{repo_info['owner']['login']}/{repo_info['name']}"
        print(f"📁 Repository: {repo_name}")
        return repo_name
    except Exception as e:
        print(f"❌ Error getting repository info: {e}")
        return None

def list_secrets(repo_name):
    """List available secrets in the repository"""
    try:
        result = subprocess.run(['gh', 'secret', 'list', '--repo', repo_name], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Cannot access secrets. Error: {result.stderr}")
            print("💡 Make sure you have admin/maintain permissions on the repository")
            return []
        
        # Parse the output to get secret names
        secrets = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Format: SECRET_NAME    Updated YYYY-MM-DD
                secret_name = line.split()[0]
                secrets.append(secret_name)
        
        print(f"🔐 Found {len(secrets)} secrets in repository")
        return secrets
    except Exception as e:
        print(f"❌ Error listing secrets: {e}")
        return []

def create_env_file(secrets):
    """Create .env file with available secrets"""
    if not secrets:
        print("❌ No secrets available to fetch")
        return False
    
    # Required secrets for this application
    required_secrets = [
        'SECRET_KEY',
        'GOOGLE_CLOUD_PROJECT', 
        'BIGQUERY_DATASET',
        'BIGQUERY_TABLE_REPORTS',
        'GOOGLE_API_KEY',
        'GEMINI_API_KEY', 
        'EPA_API_KEY',
        'AQS_API_KEY',
        'AQS_EMAIL'
    ]
    
    env_content = [
        "# Auto-generated from GitHub Secrets",
        "# DO NOT COMMIT THIS FILE TO GIT",
        "# Generated on: " + str(os.popen('date').read().strip()),
        "",
        "# Flask Configuration",
        "FLASK_ENV=development",
        "FLASK_DEBUG=true",
        ""
    ]
    
    available_secrets = []
    missing_secrets = []
    
    for secret_name in required_secrets:
        if secret_name in secrets:
            available_secrets.append(secret_name)
            env_content.append(f"{secret_name}=<PLEASE_SET_MANUALLY>")
        else:
            missing_secrets.append(secret_name)
            env_content.append(f"# {secret_name}=<NOT_AVAILABLE_IN_GITHUB_SECRETS>")
    
    # Add any extra secrets found
    extra_secrets = [s for s in secrets if s not in required_secrets]
    if extra_secrets:
        env_content.extend(["", "# Additional secrets found:"])
        for secret in extra_secrets:
            env_content.append(f"{secret}=<PLEASE_SET_MANUALLY>")
    
    # Write .env file
    env_file = Path('.env')
    with open(env_file, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"\n✅ Created .env file with {len(available_secrets)} secrets")
    print(f"📁 Location: {env_file.absolute()}")
    
    if available_secrets:
        print(f"\n🔑 Available secrets (you need to set values manually):")
        for secret in available_secrets:
            print(f"   - {secret}")
    
    if missing_secrets:
        print(f"\n⚠️  Missing secrets (not found in GitHub):")
        for secret in missing_secrets:
            print(f"   - {secret}")
    
    print(f"\n📝 Next steps:")
    print(f"   1. Edit .env file and replace <PLEASE_SET_MANUALLY> with actual values")
    print(f"   2. You can find secret values in GitHub Settings → Secrets and variables → Actions")
    print(f"   3. Or ask repository admin for the values")
    print(f"   4. Never commit .env to git (it's in .gitignore)")
    
    return True

def main():
    print("🚀 GitHub Secrets Fetcher for Local Development")
    print("=" * 50)
    
    # Check prerequisites
    if not check_github_cli():
        sys.exit(1)
    
    # Get repository info
    repo_name = get_repo_info()
    if not repo_name:
        sys.exit(1)
    
    # List available secrets
    secrets = list_secrets(repo_name)
    if not secrets:
        print("\n💡 To add secrets to your repository:")
        print("   1. Go to GitHub → Settings → Secrets and variables → Actions")
        print("   2. Click 'New repository secret'")
        print("   3. Add the required secrets from .env.example")
        sys.exit(1)
    
    # Create .env file
    success = create_env_file(secrets)
    if success:
        print(f"\n🎉 Setup complete! You can now run your Flask app with:")
        print(f"   python app_local.py")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()