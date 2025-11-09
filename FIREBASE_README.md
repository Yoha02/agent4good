# 🔥 Firebase Authentication Setup Guide

Complete guide for setting up Firebase Authentication for the Public Health Officials login system.

---

## Table of Contents

- [Overview](#overview)
- [For Developers - Local Setup](#for-developers---local-setup)
- [For Admins - Setting Up Firebase](#for-admins---setting-up-firebase)
- [For Admins - Creating Official Users](#for-admins---creating-official-users)
- [Switching to a New Firebase Project](#switching-to-a-new-firebase-project)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

---

## Overview

The platform includes a secure login system for Public Health Officials using Firebase Authentication.

**Key Features**:
- 🔒 Secure Firebase Authentication
- 🚪 Login-only system (no signup)
- 🛡️ Protected dashboard with session management
- 👥 Admin-controlled user creation

**Access Points**:
- **Login page**: http://localhost:8080/officials-login
- **Dashboard** (requires login): http://localhost:8080/officials-dashboard

---

## For Developers - Local Setup

### Step 1: Get Firebase Credentials from Admin

Request these files from your project administrator:
- Firebase service account JSON file (e.g., `firebase-adminsdk-xxxxx.json`)
- Firebase configuration values (if using `.env` instead of fallbacks)

**⚠️ IMPORTANT**: These files contain sensitive credentials. Receive them via secure channels (encrypted email, password manager, secure file sharing).

### Step 2: Store Service Account File Securely

```bash
# Create secrets directory (outside git repo)
mkdir -p ~/secrets/firebase

# Move the service account file (adjust filename as needed)
mv ~/Downloads/your-project-firebase-adminsdk-xxxxx.json ~/secrets/firebase/service_account.json

# Verify it exists
ls -la ~/secrets/firebase/service_account.json
```

### Step 3: Update Your `.env` File

**Minimum Required** (service account file only):

```env
# Firebase Admin SDK - REQUIRED for backend token verification
FIREBASE_SERVICE_ACCOUNT_FILE=/Users/YOUR_USERNAME/secrets/firebase/service_account.json
```

**Optional** (client-side config - template has fallback values):

```env
# Firebase Web SDK - OPTIONAL (template has fallbacks)
FIREBASE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=123456789012
FIREBASE_APP_ID=1:123456789012:web:xxxxxxxxxxxxx
```

**Note**: The client-side config values are optional because the template has fallback values. Only add them if you need to override the defaults or switch Firebase projects.

### Step 4: Install Firebase Dependencies

```bash
pip install firebase-admin
# or
pip install -r requirements.txt
```

### Step 5: Test Firebase Initialization

```bash
python app_local.py
```

Look for this in the console output:
```
[OK] Firebase Admin SDK initialized
```

If you see `[WARNING] Firebase service account file not found`, check your file path in `.env`.

### Step 6: Access Officials Login

- **Login page**: http://localhost:8080/officials-login
- **Dashboard** (requires login): http://localhost:8080/officials-dashboard

**Test Credentials**: Ask your admin for a test account.

---

## For Admins - Setting Up Firebase

### Option 1: Use Existing Firebase Project

If you already have a Firebase project set up, skip to [Getting Credentials](#getting-credentials-from-existing-project).

### Option 2: Create New Firebase Project

#### 1. **Go to Firebase Console**

https://console.firebase.google.com/

#### 2. **Create New Project** (or select existing)

- Click "Add project"
- Enter project name
- Enable Google Analytics (optional)
- Click "Create project"

#### 3. **Enable Authentication**

- In Firebase Console, go to **Authentication** → **Sign-in method**
- Click **Email/Password**
- Toggle **Enable** to ON
- Click **Save**

#### 4. **Add Authorized Domains**

- In **Authentication** → **Settings** → **Authorized domains**
- Add these domains:
  - `localhost` (for local development)
  - `your-production-domain.com` (e.g., `aimmunity.io`)
- Click **Add domain** for each

#### 5. **Get Web App Configuration**

- Go to **Project Settings** (gear icon) → **General**
- Scroll to **Your apps** section
- If no web app exists:
  - Click **Add app** → **Web** (</>)
  - Register app with a nickname (e.g., "Agent4Good Web")
- Copy the Firebase configuration:
  ```javascript
  const firebaseConfig = {
    apiKey: "AIzaSy...",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.firebasestorage.app",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:..."
  };
  ```

#### 6. **Download Service Account Key**

- Go to **Project Settings** → **Service accounts**
- Click **Firebase Admin SDK** tab
- Click **Generate new private key**
- Download the JSON file
- **⚠️ Keep this file secure!** Never commit to git.

#### 7. **Share Credentials with Team**

**What to Share**:
1. Service account JSON file (securely)
2. Path to store the file: `~/secrets/firebase/service_account.json`
3. This README

**How to Share Securely**:
- ✅ Encrypted email
- ✅ Password manager (1Password, LastPass)
- ✅ Secure file sharing (Google Drive with access control)
- ✅ In-person transfer
- ❌ **Never**: Plain email, Slack, public repos

---

### Getting Credentials from Existing Project

#### For Web App Config (Client-Side)

1. Go to **Project Settings** → **General**
2. Scroll to **Your apps**
3. Find your web app
4. Copy the `firebaseConfig` values

#### For Service Account (Server-Side)

1. Go to **Project Settings** → **Service accounts**
2. Click **Generate new private key**
3. Download JSON file
4. Share securely with team

---

## For Admins - Creating Official Users

Since signup is disabled (login-only), officials must be created manually.

### Method 1: Firebase Console (Recommended)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Authentication** → **Users**
4. Click **Add user**
5. Enter:
   - **Email**: `official@healthdept.gov`
   - **Password**: (create a secure password)
6. Click **Add user**
7. Share credentials securely with the official

### Method 2: Bulk Creation with Firebase CLI

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Create users from JSON file
firebase auth:import users.json --project your-project-id
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

## Switching to a New Firebase Project

### When You Need This

- Migrating to production Firebase project
- Changing GCP projects
- Setting up separate dev/staging/prod environments

### Step 1: Set Up New Project

Follow [Option 2: Create New Firebase Project](#option-2-create-new-firebase-project) above.

### Step 2: Get New Credentials

- Web app config (for client-side) - **Optional** if using fallback values
- Service account JSON (for server-side) - **Required**

### Step 3: Update Configuration

**Update `.env` file** (minimum required):

```env
FIREBASE_SERVICE_ACCOUNT_FILE=/path/to/new-service-account.json
```

**Optional** (only if you need to override template fallbacks):

```env
FIREBASE_API_KEY=new-api-key
FIREBASE_AUTH_DOMAIN=new-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=new-project-id
FIREBASE_STORAGE_BUCKET=new-project-id.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=new-sender-id
FIREBASE_APP_ID=new-app-id
```

**Replace service account file**:

```bash
# Backup old file (optional)
mv ~/secrets/firebase/service_account.json ~/secrets/firebase/service_account.old.json

# Place new file
mv ~/Downloads/new-firebase-adminsdk-xxxxx.json ~/secrets/firebase/service_account.json
```

### Step 4: Update Code (if using different GCP project)

If your new Firebase project has a different project ID, update `app_local.py`:

```python
# Line ~70
GCP_PROJECT_ID = 'your-new-project-id'
```

**OR** update template fallback values in `templates/officials_login.html`:

```javascript
// Around line 269-274
const firebaseConfig = {
    apiKey: "{{ firebase_config.apiKey or 'NEW-API-KEY' }}",
    authDomain: "{{ firebase_config.authDomain or 'new-project.firebaseapp.com' }}",
    projectId: "{{ firebase_config.projectId or 'new-project-id' }}",
    // ... etc
};
```

### Step 5: Test New Configuration

```bash
# Restart app
python app_local.py

# Check console for:
# [OK] Firebase Admin SDK initialized

# Test login at:
# http://localhost:8080/officials-login
```

### Step 6: Update Production Deployment

For Cloud Run:

```bash
# If using env vars (optional)
gcloud run services update agent4good \
  --set-env-vars="FIREBASE_API_KEY=new-api-key,FIREBASE_AUTH_DOMAIN=new-project.firebaseapp.com,..." \
  --region=us-central1

# Upload new service account as secret (recommended)
gcloud secrets create firebase-service-account --data-file=new-service-account.json

# Update Cloud Run to use new secret
gcloud run services update agent4good \
  --update-secrets=FIREBASE_SERVICE_ACCOUNT_FILE=/secrets/firebase-service-account:latest \
  --region=us-central1
```

---

## Troubleshooting

### "Firebase service account file not found"

**Symptom**: Warning in console, authentication disabled

**Fix**: 
1. Check `.env` has: `FIREBASE_SERVICE_ACCOUNT_FILE=/full/path/to/file.json`
2. Verify file exists: `ls -la /full/path/to/file.json`
3. Use absolute path, not relative
4. Restart app after updating `.env`

### "auth/invalid-api-key"

**Symptom**: Error in browser console when trying to login

**Fix**: 
1. If using `.env` for Firebase config, verify `FIREBASE_API_KEY` matches Firebase Console
2. If using template fallbacks, ensure they match your Firebase project
3. Check for typos or extra spaces
4. Restart app to reload environment

### "Email/password accounts are not enabled"

**Symptom**: Login fails with this error message

**Fix**: 
1. Go to Firebase Console → Authentication → Sign-in method
2. Enable **Email/Password**
3. Click **Save**

### "There is no user record"

**Symptom**: Login fails with valid credentials

**Fix**: 
1. Create user in Firebase Console → Authentication → Users
2. Click **Add user**
3. Enter email and password
4. Try logging in again

### "Unauthorized domain"

**Symptom**: Firebase auth blocked by CORS or domain error

**Fix**: 
1. Go to Firebase Console → Authentication → Settings → Authorized domains
2. Add your domain:
   - `localhost` (for local)
   - Your production domain
3. Click **Add domain**

### Login works but dashboard redirects to login

**Symptom**: Successful login but dashboard not accessible

**Fix**: 
1. Check Flask `SECRET_KEY` is set in `.env`
2. Clear browser cookies/cache
3. Try incognito mode
4. Check browser console for errors
5. Verify session is created (check server logs)

### "Cannot access dashboard without login" (Expected Behavior)

**Symptom**: Accessing `/officials-dashboard` redirects to login

**Fix**: This is correct behavior! Dashboard is protected. You must:
1. Go to `/officials-login`
2. Login with valid credentials
3. Then access dashboard

---

## Additional Resources

### Detailed Documentation

- **Quick Start**: [FIREBASE_QUICK_START.md](FIREBASE_QUICK_START.md) - 5-minute setup
- **Complete Setup**: [FIREBASE_SETUP.md](FIREBASE_SETUP.md) - Comprehensive guide
- **Integration Details**: [FIREBASE_INTEGRATION_COMPLETE.md](FIREBASE_INTEGRATION_COMPLETE.md)
- **Security Implementation**: [FIREBASE_AUTH_FIX_COMPLETE.md](FIREBASE_AUTH_FIX_COMPLETE.md)
- **Logout Implementation**: [LOGOUT_FIX_COMPLETE.md](LOGOUT_FIX_COMPLETE.md)

### Firebase Official Documentation

- **Firebase Console**: https://console.firebase.google.com/
- **Firebase Auth Docs**: https://firebase.google.com/docs/auth
- **Admin SDK Docs**: https://firebase.google.com/docs/admin/setup
- **Security Best Practices**: https://firebase.google.com/docs/rules

### Environment Variables Reference

See [env.template](env.template) for a complete list of environment variables.

---

## Security Best Practices

### ✅ Do

- Store service account JSON outside git repo (`~/secrets/`)
- Never commit `.env` or service account JSON files
- Share credentials via encrypted channels only
- Use strong passwords for official accounts
- Rotate service account keys periodically
- Monitor Firebase Console for suspicious activity
- Use HTTPS in production (automatic with Cloud Run)
- Enable only Email/Password provider (disable others if not needed)

### ❌ Don't

- Commit service account JSON to git
- Share credentials via plain email or public channels
- Reuse passwords across multiple officials
- Enable anonymous authentication (unless needed)
- Ignore suspicious login activity
- Use weak passwords for official accounts
- Share service account with unauthorized people

---

## FAQ

### Q: Do I need to add Firebase config to `.env`?

**A**: No, only `FIREBASE_SERVICE_ACCOUNT_FILE` is required. The client-side Firebase config has fallback values in the template. Add the other values to `.env` only if you need to override defaults or switch Firebase projects easily.

### Q: Are the Firebase API keys in the template safe?

**A**: Yes! Firebase API keys are designed to be public (they're visible in browser DevTools anyway). Security comes from authorized domains and authentication rules, not hiding the API key. The sensitive credential is the service account JSON file, which stays on the server.

### Q: Can users sign up on their own?

**A**: No, signup is disabled by design. Only admins can create official accounts via Firebase Console or CLI. This ensures only authorized personnel have access.

### Q: How do I add a new official?

**A**: Go to Firebase Console → Authentication → Users → Add user. Enter their email and a secure password, then share the credentials securely.

### Q: What happens if I lose the service account file?

**A**: Generate a new one in Firebase Console → Project Settings → Service accounts → Generate new private key. Update the file path in `.env` and restart the app.

### Q: Can I use multiple Firebase projects (dev/staging/prod)?

**A**: Yes! Update `.env` with the appropriate service account file path for each environment. Optionally update the template fallback values or use `.env` for all Firebase config.

### Q: How long do sessions last?

**A**: Flask sessions last until the browser is closed (by default). You can configure session lifetime in `app_local.py` if needed.

---

## Support

For issues or questions:

- **GitHub Issues**: Create an issue in the repository
- **Documentation**: This README and related docs
- **Firebase Support**: https://firebase.google.com/support

---

**Built with ❤️ for Community Health & Wellness**

*Last Updated: November 8, 2025*

