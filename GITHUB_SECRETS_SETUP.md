# GitHub Secrets Configuration Guide

This project uses **GitHub Secrets** instead of `.env` files for secure credential management in production and CI/CD pipelines.

## 🔐 Required GitHub Secrets

To deploy and run this application, you need to configure the following secrets in your GitHub repository:

### How to Add Secrets to GitHub:
1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret below

---

## 📋 Secrets to Configure

### 1. Flask Configuration
| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `SECRET_KEY` | Flask secret key for sessions | `your-random-secret-key-here` |

**Generate a secure key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

### 2. Google Cloud Configuration
| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `GOOGLE_CLOUD_PROJECT` | Your GCP project ID | `qwiklabs-gcp-00-4a7d408c735c` |
| `BIGQUERY_DATASET` | BigQuery dataset name | `CrowdsourceData` |
| `BIGQUERY_TABLE_REPORTS` | BigQuery table name | `CrowdSourceData` |
| `GCP_CREDENTIALS` | Service account JSON (entire file content) | `{"type": "service_account",...}` |

**To get GCP_CREDENTIALS:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. IAM & Admin → Service Accounts
3. Create or select a service account
4. Create JSON key
5. Copy the **entire JSON file content** as the secret value

---

### 3. Google API Keys
| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `GOOGLE_API_KEY` | Google Maps/Geocoding API key | `AIzaSy...` |
| `GEMINI_API_KEY` | Google Gemini AI API key | `AIzaSy...` |

**Get API keys:**
- [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- Enable these APIs:
  - Maps JavaScript API
  - Geocoding API
  - Places API
  - Air Quality API
  - Generative Language API (Gemini)

---

### 4. EPA/AirNow API Configuration
| Secret Name | Description | Example Value |
|------------|-------------|---------------|
| `EPA_API_KEY` | EPA AirNow API key | `87FB7DB4-DDE6-4FDB-B214-3948D35ADE59` |
| `AQS_API_KEY` | EPA Air Quality System API key | `ochregazelle35` |
| `AQS_EMAIL` | Email for AQS API | `your.email@example.com` |

**Get EPA API keys:**
- AirNow API: https://docs.airnowapi.org/account/request/
- AQS API: https://aqs.epa.gov/aqsweb/documents/data_api.html

---

## 🚀 Using Secrets in Development

For local development, you can still use a `.env` file (which is gitignored).

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your local values in `.env`

3. **NEVER commit `.env` to git** - it's in `.gitignore`

---

## 📦 Environment Variables in Code

The application uses `os.getenv()` to read environment variables, which works with both:
- ✅ GitHub Secrets (in CI/CD)
- ✅ `.env` files (in local development via python-dotenv)

Example:
```python
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
```

---

## 🔄 How GitHub Actions Uses Secrets

The `.github/workflows/deploy.yml` file automatically:

1. **Loads secrets** as environment variables:
   ```yaml
   env:
     GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
   ```

2. **Passes them to Cloud Run** during deployment:
   ```yaml
   --set-env-vars GOOGLE_API_KEY=${{ secrets.GOOGLE_API_KEY }}
   ```

---

## ✅ Verification Checklist

After adding secrets to GitHub, verify:

- [ ] All secrets are added in GitHub Settings → Secrets
- [ ] `.env` file is in `.gitignore`
- [ ] `.env` is NOT committed to the repository
- [ ] `.env.example` has placeholders (no real values)
- [ ] GitHub Actions workflow can access secrets
- [ ] Deployed application can read environment variables

---

## 🛡️ Security Best Practices

1. **Never commit secrets to git**
   - Always use `.gitignore` for `.env`
   - Never hardcode API keys in source code

2. **Rotate keys regularly**
   - Change API keys periodically
   - Update GitHub Secrets when keys change

3. **Use least privilege**
   - Service accounts should have minimal required permissions
   - Restrict API keys to specific services

4. **Monitor usage**
   - Check Google Cloud billing
   - Monitor API quota usage
   - Review access logs

---

## 🆘 Troubleshooting

**Issue:** "Secret not found" error in GitHub Actions
- **Solution:** Verify secret name matches exactly (case-sensitive)

**Issue:** Application can't connect to BigQuery
- **Solution:** Check `GCP_CREDENTIALS` is valid JSON

**Issue:** API key not working
- **Solution:** Ensure API is enabled in Google Cloud Console

---

## 📚 Additional Resources

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)

---

**Last Updated:** October 26, 2025
