# BigQuery Setup Instructions

## For Team Members: Setting Up BigQuery Authentication

Follow these steps to configure BigQuery access for the Agent4Good application:

### 1. Create a Service Account (Only once, by project admin)

**Note:** If a service account already exists, skip to step 2.

1. Go to [Google Cloud Console - Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Select project: `qwiklabs-gcp-00-4a7d408c735c`
3. Click **"+ CREATE SERVICE ACCOUNT"**
4. Fill in:
   - **Name:** `agent4good-bigquery-service`
   - **Description:** `Service account for Agent4Good BigQuery integration`
5. Click **"CREATE AND CONTINUE"**
6. Grant the following role:
   - **BigQuery Data Editor** (allows read/write to tables)
7. Click **"DONE"**

### 2. Create and Download JSON Key

1. Find the service account you just created (or existing one)
2. Click on the service account name
3. Go to the **"KEYS"** tab
4. Click **"ADD KEY"** → **"Create new key"**
5. Select **JSON** format
6. Click **"CREATE"**
7. The JSON file will download automatically (e.g., `qwiklabs-gcp-00-4a7d408c735c-abc123def456.json`)

### 3. Add the JSON Key to Your Local Project

1. **Rename** the downloaded file to: `bigquery-credentials.json`
2. **Move** it to the project root folder:
   ```
   C:\Users\YourName\agent4good\bigquery-credentials.json
   ```
3. **IMPORTANT:** Do NOT commit this file to git! It's already in `.gitignore`

### 4. Update Your .env File

Copy `.env.example` to `.env` and update it:

```bash
# Copy the example file
cp .env.example .env
```

Then edit `.env` and add:

```env
# BigQuery Configuration
GOOGLE_CLOUD_PROJECT=qwiklabs-gcp-00-4a7d408c735c
BIGQUERY_DATASET=CrowdsourceData
BIGQUERY_TABLE_REPORTS=CrowdSourceData
GOOGLE_APPLICATION_CREDENTIALS=bigquery-credentials.json
```

**Note:** The path is relative to the project root. If you place the file elsewhere, use the full absolute path.

### 5. Test the Connection

Run the test script to verify authentication:

```bash
# Activate virtual environment (if not already active)
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Mac/Linux

# Run the test
python test_bigquery_auth.py
```

You should see:
```
✓ BigQuery client created successfully
✓ Table exists!
```

### 6. Run the Application

```bash
python app_local.py
```

Visit `http://localhost:8080/report` and submit a test report. Check the console for:
```
[BIGQUERY SUCCESS] Report {id} inserted into qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData
```

---

## Troubleshooting

### Error: "Could not automatically determine credentials"
- Make sure `GOOGLE_APPLICATION_CREDENTIALS` in `.env` points to the correct JSON file
- Verify the JSON file exists in the specified location

### Error: "Permission denied" or "403 Forbidden"
- The service account needs **BigQuery Data Editor** role
- Contact the project admin to grant proper permissions

### Error: "Table not found"
- Verify the table exists: `qwiklabs-gcp-00-4a7d408c735c.CrowdsourceData.CrowdSourceData`
- Check that dataset and table names in `.env` are correct

### Error: "Quota exceeded"
- The project may have reached its BigQuery quota limit
- Contact the project admin or check [quota settings](https://console.cloud.google.com/iam-admin/quotas)

---

## Security Best Practices

⚠️ **NEVER commit the JSON credentials file to GitHub!**

- The file `bigquery-credentials.json` is already in `.gitignore`
- Share the credentials securely (e.g., via encrypted email, secure file sharing)
- Rotate keys regularly (every 90 days recommended)
- Use separate service accounts for development and production

---

## For Project Admins: Creating Keys for Team Members

Instead of sharing the same JSON key:

1. Create individual service accounts for each team member
2. Grant minimal required permissions (principle of least privilege)
3. Use Google Cloud IAM to manage access
4. Regularly audit service account usage

Alternatively, use **Workload Identity Federation** for more secure, keyless authentication (advanced setup).
