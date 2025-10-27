"""
Direct GitHub Secrets Fetcher
Uses GitHub API to fetch secrets directly at runtime
"""

import subprocess
import os
import json
import base64

def fetch_secrets_from_github():
    """
    Fetch secrets from GitHub repository using gh CLI
    Since GitHub doesn't expose secret values via API (security feature),
    we use environment variables that are automatically set in GitHub Actions
    or need to be manually set locally.
    """
    
    gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
    repo = "Yoha02/agent4good"
    
    print("[SECRETS] 🔍 Fetching secrets from GitHub...")
    
    # List all secret names
    try:
        result = subprocess.run(
            [gh_path, 'secret', 'list', '--repo', repo],
            capture_output=True,
            text=True,
            check=True
        )
        
        secret_names = []
        for line in result.stdout.split('\n'):
            if line.strip() and not line.startswith('NAME'):
                parts = line.split()
                if parts:
                    secret_names.append(parts[0])
        
        print(f"[SECRETS] ✅ Found {len(secret_names)} secrets in repository")
        
        # Since we can't read secret values via CLI/API (security feature),
        # we need to use environment variables
        secrets_dict = {}
        missing_secrets = []
        
        for name in secret_names:
            value = os.getenv(name)
            if value:
                secrets_dict[name] = value
            else:
                missing_secrets.append(name)
        
        if secrets_dict:
            print(f"[SECRETS] ✅ Loaded {len(secrets_dict)} secrets from environment")
            for key in secrets_dict.keys():
                print(f"[SECRETS]    ✓ {key}")
        
        if missing_secrets:
            print(f"[SECRETS] ⚠️  {len(missing_secrets)} secrets not in environment:")
            for key in missing_secrets:
                print(f"[SECRETS]    ✗ {key}")
            print(f"[SECRETS] 💡 Solution: Set them in your current shell:")
            print(f"[SECRETS]    $env:{missing_secrets[0]}='your-value-here'")
        
        # Set all loaded secrets as environment variables
        for key, value in secrets_dict.items():
            os.environ[key] = value
        
        return secrets_dict
        
    except subprocess.CalledProcessError as e:
        print(f"[SECRETS] ❌ Error fetching secrets: {e.stderr}")
        return {}
    except FileNotFoundError:
        print(f"[SECRETS] ❌ GitHub CLI not found")
        return {}


def load_secrets_from_env_if_exists():
    """Fallback: Load from .env file if it exists"""
    from pathlib import Path
    
    env_file = Path('.env')
    if env_file.exists():
        print(f"[SECRETS] 📄 Loading from .env file...")
        from dotenv import load_dotenv
        load_dotenv()
        return True
    return False


def setup_environment():
    """
    Main setup function - call this at the start of your app
    This will:
    1. Try to fetch secrets from GitHub environment
    2. Fall back to .env file if available
    3. Use defaults for development
    """
    
    print("\n" + "="*60)
    print("🔐 GitHub Secrets Manager - Initializing...")
    print("="*60)
    
    # Try to fetch from GitHub (will use environment variables)
    secrets = fetch_secrets_from_github()
    
    if not secrets:
        print("[SECRETS] 💡 No secrets in environment, checking for .env file...")
        if load_secrets_from_env_if_exists():
            print("[SECRETS] ✅ Loaded secrets from .env file")
        else:
            print("[SECRETS] ⚠️  No .env file found")
            print("[SECRETS] 💡 App will use mock data and defaults")
    
    print("="*60 + "\n")
    
    return secrets


if __name__ == "__main__":
    # Test the setup
    secrets = setup_environment()
    
    print("\n📊 Environment Status:")
    print(f"   Google API Key: {'✓ Set' if os.getenv('GOOGLE_API_KEY') else '✗ Missing'}")
    print(f"   Gemini API Key: {'✓ Set' if os.getenv('GEMINI_API_KEY') else '✗ Missing'}")
    print(f"   EPA API Key: {'✓ Set' if os.getenv('EPA_API_KEY') else '✗ Missing'}")
    print(f"   BigQuery Project: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
