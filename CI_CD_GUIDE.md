# CI/CD Pipeline Documentation

## 🚀 Overview

This project uses GitHub Actions for continuous integration and deployment. All workflows automatically fetch secrets from GitHub Secrets, so **no `.env` file is needed in CI/CD**.

## 📋 Workflows

### 1. **Main Deployment** (`.github/workflows/deploy.yml`)
**Triggers:** Push to `main`, `combined-branch-s`, or `Improving-UI-From-Main-S`

**Jobs:**
- ✅ **Test & Code Quality** - Runs linting, formatting checks, and tests
- 🚀 **Build & Deploy** - Builds Docker image and deploys to Google Cloud Run

**What it does:**
1. Checks code quality with flake8 and black
2. Runs all tests
3. Verifies all secrets are configured
4. Builds Docker image and pushes to Google Container Registry
5. Deploys to Cloud Run with all environment variables
6. Tests the deployment
7. Creates deployment summary

**Secrets used:** ALL (18 secrets including Google, EPA, Twitter APIs)

---

### 2. **Test Suite** (`.github/workflows/test.yml`)
**Triggers:** Push or PR to main branches

**Jobs:**
- Runs tests on Python 3.11 and 3.12
- Generates code coverage reports
- Uploads coverage to Codecov

---

### 3. **Code Quality** (`.github/workflows/code-quality.yml`)
**Triggers:** Push or PR to main branches

**Jobs:**
- Runs flake8 for PEP8 compliance
- Checks code formatting with black
- Checks import sorting with isort
- Runs pylint for code analysis
- Security scan with bandit
- Checks dependencies for vulnerabilities

---

### 4. **Branch Build** (`.github/workflows/branch-build.yml`)
**Triggers:** Push to any branch except main/combined-branch-s

**Jobs:**
- Builds and tests without deploying
- Verifies all secrets are available
- Runs smoke tests
- Tests Docker container locally

---

## 🔐 Required GitHub Secrets

All secrets are automatically loaded in CI/CD. To view/edit:
```
https://github.com/Yoha02/agent4good/settings/secrets/actions
```

### Core Secrets (18 total):

| Secret Name | Purpose | Required |
|------------|---------|----------|
| `GCP_SERVICE_ACCOUNT_KEY` | Google Cloud authentication JSON | ✅ Yes |
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | ✅ Yes |
| `GOOGLE_API_KEY` | Google Maps/Places API | ✅ Yes |
| `GEMINI_API_KEY` | Google Gemini AI | ✅ Yes |
| `EPA_API_KEY` | EPA AirNow API | ✅ Yes |
| `AQS_API_KEY` | EPA Air Quality System | ⚠️ Optional |
| `AQS_EMAIL` | Email for AQS API | ⚠️ Optional |
| `BIGQUERY_DATASET` | BigQuery dataset name | ✅ Yes |
| `BIGQUERY_TABLE_REPORTS` | BigQuery table name | ✅ Yes |
| `SECRET_KEY` | Flask secret key | ✅ Yes |
| `GCS_VIDEO_BUCKET` | Google Cloud Storage bucket | ⚠️ Optional |
| `TWITTER_API_KEY` | Twitter API key | ⚠️ Optional |
| `TWITTER_API_SECRET` | Twitter API secret | ⚠️ Optional |
| `TWITTER_ACCESS_TOKEN` | Twitter access token | ⚠️ Optional |
| `TWITTER_ACCESS_TOKEN_SECRET` | Twitter token secret | ⚠️ Optional |
| `TWITTER_BEARER_TOKEN` | Twitter bearer token | ⚠️ Optional |
| `TWITTER_USERNAME` | Twitter username | ⚠️ Optional |

---

## 🎯 How Secrets Are Used

### In GitHub Actions:
```yaml
env:
  GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  # ... all other secrets
```

### Passed to Cloud Run:
```bash
gcloud run deploy agent4good \
  --set-env-vars "GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}" \
  --set-env-vars "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" \
  # ... all other secrets
```

### In Your Flask App:
```python
# Secrets are automatically available as environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
# ... etc
```

---

## 🔄 Deployment Process

### Automatic Deployment:
1. Push code to `main`, `combined-branch-s`, or `Improving-UI-From-Main-S`
2. GitHub Actions automatically:
   - Runs tests
   - Builds Docker image
   - Pushes to Google Container Registry
   - Deploys to Cloud Run
   - Runs health checks
   - Creates deployment summary

### Manual Deployment:
1. Go to GitHub Actions tab
2. Select "CI/CD - Build, Test & Deploy" workflow
3. Click "Run workflow"
4. Select branch and run

---

## 🧪 Testing Locally with Secrets

### Option 1: Use `.env` file
1. Create `.env` from `.env.example`
2. Copy values from GitHub Secrets page
3. Run: `python app_local.py`

### Option 2: Load from environment
```powershell
# PowerShell
. .\load_env.ps1
python app_local.py
```

### Option 3: Set manually
```powershell
$env:GOOGLE_API_KEY="your-key"
$env:GEMINI_API_KEY="your-key"
python app_local.py
```

---

## 📊 Monitoring Deployments

### View Workflow Runs:
```
https://github.com/Yoha02/agent4good/actions
```

### View Deployed App:
After deployment, check the workflow summary for the Cloud Run URL.

### View Logs:
```bash
gcloud run logs read --service=agent4good --region=us-central1
```

---

## 🛠️ Adding New Secrets

1. **In GitHub:**
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add name and value

2. **In Workflow:**
   - Add to `env:` section in `.github/workflows/deploy.yml`
   - Add to Cloud Run deployment command with `--set-env-vars`

3. **In Application:**
   - Use `os.getenv('YOUR_SECRET_NAME')` in Python code

---

## 🔒 Security Best Practices

✅ **DO:**
- Store all credentials in GitHub Secrets
- Rotate API keys regularly
- Use least-privilege service accounts
- Review workflow logs for exposed secrets

❌ **DON'T:**
- Commit `.env` files to git
- Echo secret values in workflow logs
- Use secrets in public workflow outputs
- Share secrets via insecure channels

---

## 📝 Workflow Status Badges

Add these to your README.md:

```markdown
![Deploy](https://github.com/Yoha02/agent4good/actions/workflows/deploy.yml/badge.svg)
![Tests](https://github.com/Yoha02/agent4good/actions/workflows/test.yml/badge.svg)
![Code Quality](https://github.com/Yoha02/agent4good/actions/workflows/code-quality.yml/badge.svg)
```

---

## 🆘 Troubleshooting

### Build Fails with "Secret not found"
- Verify secret exists in GitHub Settings → Secrets
- Check secret name matches exactly (case-sensitive)
- Ensure you have repository access

### Deployment Fails
- Check Cloud Run logs: `gcloud run logs read --service=agent4good`
- Verify GCP_SERVICE_ACCOUNT_KEY is valid JSON
- Ensure service account has required permissions

### Tests Fail
- Check test logs in Actions tab
- Run tests locally: `pytest tests/ -v`
- Verify all dependencies are installed

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Managing GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**Last Updated:** October 26, 2025
