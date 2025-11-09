# Firebase Authentication Setup Guide

Complete guide for setting up Firebase Authentication for the Officials Login system.

## Overview

The application uses Firebase Authentication for secure login of public health officials. The system integrates:
- **Firebase Web SDK** (client-side) for user login
- **Firebase Admin SDK** (server-side) for token verification
- **Flask sessions** for maintaining authenticated state

## Prerequisites

- Google Cloud Project (already created: `qwiklabs-gcp-00-4a7d408c735c`)
- Firebase project enabled
- Service account JSON file downloaded

---

## 1. Firebase Console Setup

### Step 1: Enable Authentication

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `qwiklabs-gcp-00-4a7d408c735c`
3. Navigate to **Authentication** → **Sign-in method**
4. Enable **Email/Password** provider
5. Click **Save**

### Step 2: Add Authorized Domains

1. In **Authentication** → **Settings** → **Authorized domains**
2. Add the following domains:
   - `localhost` (for local development)
   - `aimmunity.io` (production domain)
3. Click **Add domain** for each

### Step 3: Get Web App Configuration

1. Go to **Project Settings** (gear icon)
2. Scroll to **Your apps** section
3. If no web app exists, click **Add app** → **Web** (</>) 
4. Register the app with nickname "Agent4Good Web"
5. Copy the Firebase configuration object (you'll need these values):
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSy...",
     authDomain: "your-project.firebaseapp.com",
     projectId: "qwiklabs-gcp-00-4a7d408c735c",
     storageBucket: "qwiklabs-gcp-00-4a7d408c735c.firebasestorage.app",
     messagingSenderId: "776464277441",
     appId: "1:776464277441:web:..."
   };
   ```

### Step 4: Download Service Account Key

1. Go to **Project Settings** → **Service accounts**
2. Click **Firebase Admin SDK** tab
3. Click **Generate new private key**
4. Download the JSON file (e.g., `qwiklabs-gcp-00-4a7d408c735c-firebase-adminsdk-xxxxx.json`)
5. **IMPORTANT**: Keep this file secure and never commit it to git

---

## 2. Local Development Setup

### Step 1: Store Service Account File

Place the downloaded JSON file in a secure location:

```bash
# Create secrets directory (not in repo)
mkdir -p ~/secrets/firebase

# Move the service account file
mv ~/Downloads/qwiklabs-gcp-00-4a7d408c735c-firebase-adminsdk-*.json ~/secrets/firebase/service_account.json
```

### Step 2: Configure Environment Variables

Create or update your `.env` file in the project root:

```bash
# Firebase Web SDK Configuration (public - used by client)
FIREBASE_API_KEY=AIzaSyDTK4NBTDymbXtuRpNhbU9gDH1yX60JGw0
FIREBASE_AUTH_DOMAIN=qwiklabs-gcp-00-4a7d408c735c.firebaseapp.com
FIREBASE_PROJECT_ID=qwiklabs-gcp-00-4a7d408c735c
FIREBASE_STORAGE_BUCKET=qwiklabs-gcp-00-4a7d408c735c.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=776464277441
FIREBASE_APP_ID=1:776464277441:web:f4faf70781e429a4671940

# Firebase Admin SDK Configuration (private - server only)
FIREBASE_SERVICE_ACCOUNT_FILE=/Users/YOUR_USERNAME/secrets/firebase/service_account.json

# Flask Secret Key (generate a random string)
SECRET_KEY=your-secret-key-here-change-in-production
```

**Note**: Update `FIREBASE_SERVICE_ACCOUNT_FILE` path to match your actual location.

### Step 3: Update `.gitignore`

Ensure these are ignored (should already be in place):

```
.env
*.json
!package*.json
~/secrets/
```

### Step 4: Install Dependencies

```bash
pip install firebase-admin
# or
pip install -r requirements.txt
```

### Step 5: Load Environment and Run

```powershell
# Load environment variables
. .\load_env.ps1

# Run the application
python app_local.py
```

---

## 3. Creating Official Users

Since signup is disabled (login-only mode), you must create users manually in Firebase Console.

### Method 1: Firebase Console (Recommended)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Navigate to **Authentication** → **Users**
3. Click **Add user**
4. Enter:
   - Email: `official@healthdept.gov`
   - Password: (create a secure password)
5. Click **Add user**
6. Share credentials securely with the official

### Method 2: Firebase CLI (Bulk Creation)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Create user script
firebase auth:import users.json --project qwiklabs-gcp-00-4a7d408c735c
```

Example `users.json`:
```json
{
  "users": [
    {
      "email": "official1@healthdept.gov",
      "password": "SecurePassword123!"
    },
    {
      "email": "official2@healthdept.gov",
      "password": "SecurePassword456!"
    }
  ]
}
```

---

## 4. Production Deployment Setup

### Option A: Using Service Account File (Cloud Run / VM)

1. **Upload service account to server**:
   ```bash
   # On server, create secrets directory
   mkdir -p /secrets/firebase
   
   # Upload file (use scp, gcloud, or Cloud Run secrets)
   scp service_account.json user@server:/secrets/firebase/
   ```

2. **Set environment variables** in deployment config:
   ```bash
   FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase/service_account.json
   FIREBASE_API_KEY=AIzaSy...
   FIREBASE_AUTH_DOMAIN=...
   # ... (all other env vars)
   ```

### Option B: Using Environment Variable (Cloud Run Secrets)

1. **Convert JSON to base64** (alternative if file storage not available):
   ```bash
   cat service_account.json | base64 > service_account_b64.txt
   ```

2. **Add to Cloud Run secrets** or env vars

3. **Update `app_local.py`** to decode from env var if needed:
   ```python
   import json
   import base64
   
   # In initialization section
   firebase_json_b64 = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON_B64')
   if firebase_json_b64:
       firebase_json = base64.b64decode(firebase_json_b64)
       cred = credentials.Certificate(json.loads(firebase_json))
   ```

### Cloud Run Deployment Commands

```bash
# Set environment variables
gcloud run services update agent4good \
  --set-env-vars="FIREBASE_API_KEY=AIzaSy...,FIREBASE_AUTH_DOMAIN=...,FIREBASE_PROJECT_ID=..." \
  --region=us-central1

# Or use secrets manager (recommended)
gcloud secrets create firebase-config --data-file=service_account.json
gcloud run services update agent4good \
  --update-secrets=FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase/service_account.json:latest
```

---

## 5. Team Collaboration

### For Team Members

1. **Request service account file** from admin (via secure channel)
2. **Place file** in `~/secrets/firebase/service_account.json`
3. **Get `.env` template** from team (values without actual secrets)
4. **Update `.env`** with actual Firebase config values
5. **Run** `.\load_env.ps1` then `python app_local.py`

### For Admin (Sharing Secrets)

**Do NOT commit** `.env` or service account JSON to git. Share via:
- Password manager (1Password, LastPass)
- Encrypted email
- Secure messaging (Signal, encrypted Slack)
- In-person transfer

**Share with team**:
1. `.env.template` (file with keys but dummy values)
2. Actual `.env` values (securely)
3. Service account JSON file (securely)
4. This setup guide

---

## 6. Testing the Integration

### Test 1: Check Firebase Initialization

```bash
python app_local.py
```

Look for console output:
```
[OK] Firebase Admin SDK initialized
```

If you see warnings, check:
- `FIREBASE_SERVICE_ACCOUNT_FILE` path is correct
- File exists and is readable
- JSON format is valid

### Test 2: Login Flow

1. Navigate to `http://localhost:8080/officials-login`
2. Enter a valid official email/password (created in Firebase Console)
3. Click **Secure Login**
4. Should see "Authenticating..." then redirect to `/officials-dashboard`
5. Check console for:
   ```
   [OK] Official logged in: official@healthdept.gov (UID: abc123...)
   ```

### Test 3: Session Persistence

1. After successful login, try accessing `/officials-dashboard` directly
2. Should load without redirect (session active)
3. Restart browser and try again - should redirect to login (session expired)

### Test 4: Protected Route

1. **Without login**: Navigate to `http://localhost:8080/officials-dashboard`
   - Should redirect to `/officials-login`
2. **After login**: Access should be granted

---

## 7. Troubleshooting

### Error: "Firebase service account file not found"

**Cause**: `FIREBASE_SERVICE_ACCOUNT_FILE` path is incorrect

**Fix**:
- Check path in `.env`
- Ensure file exists: `ls ~/secrets/firebase/service_account.json`
- Use absolute path, not relative

### Error: "Invalid authentication token"

**Cause**: Token verification failed

**Fix**:
- Check service account file has correct permissions
- Ensure Firebase project ID matches
- Verify clock sync (tokens are time-sensitive)

### Error: "auth/invalid-credential"

**Cause**: Wrong email or password on client side

**Fix**:
- Verify user exists in Firebase Console → Authentication → Users
- Check password is correct
- Try resetting password in Firebase Console

### Error: "Firebase not available - skipping auth check"

**Cause**: Firebase Admin SDK not initialized (dev mode fallback)

**Impact**: Authentication is bypassed, any user can access protected routes

**Fix**: This is expected in dev mode if Firebase is not configured. For production, ensure Firebase is properly initialized.

### Error: "CORS / Network request failed"

**Cause**: Domain not authorized in Firebase

**Fix**:
- Add domain to Firebase Console → Authentication → Authorized domains
- Check browser console for specific CORS errors

---

## 8. Security Best Practices

1. **Never commit secrets** to git:
   - `.env` file
   - Service account JSON
   - API keys

2. **Use strong passwords** for official accounts:
   - Minimum 12 characters
   - Mix of upper, lower, numbers, symbols
   - Unique per user

3. **Rotate service account keys** periodically:
   - Generate new key in Firebase Console
   - Update all deployments
   - Delete old key

4. **Monitor authentication logs**:
   - Firebase Console → Authentication → Users
   - Check for suspicious activity
   - Review login patterns

5. **Use HTTPS in production**:
   - Required for Firebase Authentication
   - Already handled by Cloud Run

6. **Set session timeouts**:
   - Flask sessions expire on browser close
   - Consider adding explicit timeout for longer sessions

---

## 9. Architecture Overview

```
┌─────────────────┐
│  Browser        │
│  (Client)       │
└────────┬────────┘
         │
         │ 1. User enters email/password
         │ 2. Firebase Auth (signInWithEmailAndPassword)
         │
    ┌────▼──────────────────────────┐
    │  Firebase Authentication      │
    │  (Google Cloud)               │
    └────┬──────────────────────────┘
         │
         │ 3. Returns ID token (JWT)
         │
    ┌────▼──────────────────────────┐
    │  Flask Backend (app_local.py) │
    │  /officials-verify-token      │
    └────┬──────────────────────────┘
         │
         │ 4. Verify token with Firebase Admin SDK
         │ 5. Create Flask session
         │
    ┌────▼──────────────────────────┐
    │  Protected Routes             │
    │  /officials-dashboard         │
    │  @require_official_auth       │
    └───────────────────────────────┘
```

### Key Components

1. **Firebase Web SDK** (`officials_login.html`):
   - Handles client-side authentication
   - Calls `signInWithEmailAndPassword()`
   - Obtains ID token from Firebase

2. **Flask Backend** (`app_local.py`):
   - Receives ID token via `/officials-verify-token`
   - Verifies token with Firebase Admin SDK
   - Creates Flask session with `officials_uid`

3. **Session Guard** (`@require_official_auth`):
   - Decorator for protected routes
   - Checks for `officials_uid` in session
   - Redirects to login if not authenticated

---

## 10. Next Steps

- [ ] Add password reset functionality
- [ ] Implement role-based access control (RBAC)
- [ ] Add multi-factor authentication (MFA)
- [ ] Set up email verification for new users
- [ ] Add audit logging for official actions
- [ ] Implement session timeout warnings
- [ ] Add "Remember Me" functionality with refresh tokens

---

## Support

For issues or questions:
- Check Firebase Console logs: Authentication → Users
- Review Flask console output for errors
- Test with Firebase CLI: `firebase auth:test`
- Contact: it-support@healthdept.gov

---

**Last Updated**: November 8, 2025  
**Version**: 1.0  
**Project**: Agent4Good Health Platform

