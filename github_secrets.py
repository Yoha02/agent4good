"""
GitHub Secrets Manager - Runtime Secret Fetching
Fetches secrets directly from GitHub at runtime, no .env file needed!
"""

import subprocess
import os
import sys
import json
from functools import lru_cache

class GitHubSecretsManager:
    """Fetch and cache GitHub secrets at runtime"""
    
    def __init__(self, repo="Yoha02/agent4good"):
        self.repo = repo
        self.gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
        self._secrets_cache = {}
        self._load_all_secrets()
    
    def _run_gh_command(self, args):
        """Run a GitHub CLI command"""
        try:
            cmd = [self.gh_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[SECRETS] Error running gh command: {e.stderr}")
            return None
        except FileNotFoundError:
            print(f"[SECRETS] GitHub CLI not found at {self.gh_path}")
            return None
    
    def _load_all_secrets(self):
        """Load all secret names from GitHub"""
        print(f"[SECRETS] Fetching secret names from GitHub repo: {self.repo}")
        
        output = self._run_gh_command(['secret', 'list', '--repo', self.repo])
        
        if not output:
            print("[SECRETS] ⚠️ Could not fetch secrets from GitHub")
            return
        
        # Parse secret names
        secret_names = []
        for line in output.split('\n'):
            if line.strip() and not line.startswith('NAME'):
                parts = line.split()
                if parts:
                    secret_names.append(parts[0])
        
        print(f"[SECRETS] ✅ Found {len(secret_names)} secrets in GitHub")
        
        # Note: GitHub doesn't allow reading secret VALUES via CLI
        # We store the names and they must be set as environment variables
        # when running in GitHub Actions or manually in local .env
        
        # Check which secrets are available as environment variables
        available = []
        for name in secret_names:
            if os.getenv(name):
                self._secrets_cache[name] = os.getenv(name)
                available.append(name)
        
        if available:
            print(f"[SECRETS] ✅ Loaded {len(available)} secrets from environment")
        else:
            print(f"[SECRETS] ⚠️ No secrets found in environment variables")
            print(f"[SECRETS] 💡 This is expected in local development")
    
    def get(self, key, default=None):
        """Get a secret value"""
        # First check cache
        if key in self._secrets_cache:
            return self._secrets_cache[key]
        
        # Then check environment variables
        value = os.getenv(key)
        if value:
            self._secrets_cache[key] = value
            return value
        
        # Return default
        return default
    
    def get_all(self):
        """Get all available secrets"""
        return self._secrets_cache.copy()
    
    def is_available(self, key):
        """Check if a secret is available"""
        return key in self._secrets_cache or os.getenv(key) is not None


# Global instance
_secrets_manager = None

def get_secrets_manager():
    """Get or create the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = GitHubSecretsManager()
    return _secrets_manager

def get_secret(key, default=None):
    """Convenience function to get a secret"""
    manager = get_secrets_manager()
    return manager.get(key, default)

# Export commonly used secrets as functions
def get_google_api_key():
    return get_secret('GOOGLE_API_KEY')

def get_gemini_api_key():
    return get_secret('GEMINI_API_KEY')

def get_epa_api_key():
    return get_secret('EPA_API_KEY')

def get_aqs_api_key():
    return get_secret('AQS_API_KEY')

def get_aqs_email():
    return get_secret('AQS_EMAIL')

def get_google_cloud_project():
    return get_secret('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-00-4a7d408c735c')

def get_bigquery_dataset():
    return get_secret('BIGQUERY_DATASET', 'CrowdsourceData')

def get_bigquery_table():
    return get_secret('BIGQUERY_TABLE_REPORTS', 'CrowdSourceData')

def get_secret_key():
    return get_secret('SECRET_KEY', 'dev-secret-key-change-in-production')


if __name__ == "__main__":
    # Test the secrets manager
    print("Testing GitHub Secrets Manager...")
    print("=" * 50)
    
    manager = get_secrets_manager()
    
    print(f"\n🔍 Available secrets:")
    all_secrets = manager.get_all()
    if all_secrets:
        for key in all_secrets.keys():
            value = all_secrets[key]
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print(f"   ✓ {key}: {masked}")
    else:
        print("   ⚠️ No secrets loaded from environment")
        print("   💡 In local dev, set secrets in .env file")
        print("   💡 In GitHub Actions, secrets are automatically available")
    
    print(f"\n📋 Example usage:")
    print(f"   from github_secrets import get_secret")
    print(f"   api_key = get_secret('GOOGLE_API_KEY')")
