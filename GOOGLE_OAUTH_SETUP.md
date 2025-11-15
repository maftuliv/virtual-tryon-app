# 🔐 Google OAuth 2.0 Setup Guide

Complete guide for setting up Google OAuth 2.0 authentication in Virtual Try-On App.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Google Cloud Console Setup](#google-cloud-console-setup)
3. [Local Development Setup](#local-development-setup)
4. [Railway Production Setup](#railway-production-setup)
5. [Testing the OAuth Flow](#testing-the-oauth-flow)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## 🎯 Overview

### What is Google OAuth?

Google OAuth 2.0 allows users to sign in with their Google account without creating a separate password. Benefits:

- ✅ **Better UX**: One-click sign-in
- ✅ **Enhanced Security**: No password storage
- ✅ **Trust**: Users trust Google authentication
- ✅ **Auto-fill**: Name, email, avatar from Google profile

### Architecture Flow

```
User clicks "Sign in with Google"
         ↓
Frontend requests /api/auth/google/login
         ↓
Backend generates Google authorization URL + state token
         ↓
User redirected to Google consent screen
         ↓
User approves permissions
         ↓
Google redirects to /api/auth/google/callback?code=...
         ↓
Backend exchanges code for tokens
         ↓
Backend fetches user profile from Google
         ↓
Backend creates/finds user in database
         ↓
Backend generates JWT token
         ↓
Frontend receives JWT token in URL hash
         ↓
User is logged in!
```

---

## 🛠️ Google Cloud Console Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: `Virtual Try-On` (or any name)
4. Click **"Create"**
5. Wait for project creation (~30 seconds)

### Step 2: Enable Google+ API (Legacy requirement)

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google+ API"**
3. Click **"Enable"**
4. Wait for API enablement

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Select **"External"** (for public app)
3. Click **"Create"**

**App Information:**
- **App name**: `Virtual Try-On`
- **User support email**: Your email
- **App logo**: (Optional, upload app logo)
- **App domain**: `https://taptolook.net` (your domain)
- **Authorized domains**: `taptolook.net`
- **Developer contact**: Your email

4. Click **"Save and Continue"**

**Scopes:**
5. Click **"Add or Remove Scopes"**
6. Select these scopes (minimal required):
   - `openid`
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
7. Click **"Update"** → **"Save and Continue"**

**Test Users:** (only for development)
8. Add test emails if in "Testing" mode
9. Click **"Save and Continue"**

### Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth Client ID"**
3. Select **"Web application"**

**Configuration:**
- **Name**: `Virtual Try-On Web Client`
- **Authorized JavaScript origins**:
  - `http://localhost:5000` (for local dev)
  - `https://taptolook.net` (for production)
- **Authorized redirect URIs**:
  - `http://localhost:5000/api/auth/google/callback` (local)
  - `https://taptolook.net/api/auth/google/callback` (production)

4. Click **"Create"**
5. **Copy your credentials:**
   - **Client ID**: `123456789-abc...apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-...`

⚠️ **IMPORTANT**: Keep your Client Secret secure! Never commit to Git.

---

## 💻 Local Development Setup

### Option A: Using ngrok (Recommended)

Google OAuth requires HTTPS. Use ngrok to create a secure tunnel:

#### 1. Install ngrok

```bash
# Download from https://ngrok.com/download
# Or install via package manager:
brew install ngrok  # macOS
choco install ngrok  # Windows
```

#### 2. Start your Flask app

```bash
python backend/app.py
# Server running on http://localhost:5000
```

#### 3. Start ngrok tunnel

```bash
ngrok http 5000
```

You'll get a URL like: `https://abc123.ngrok.io`

#### 4. Update Google Cloud Console

Go back to **OAuth Credentials** and add:
- **Authorized redirect URI**: `https://abc123.ngrok.io/api/auth/google/callback`

#### 5. Update `.env` file

```bash
# Google OAuth Configuration
GOOGLE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here
GOOGLE_REDIRECT_URI=https://abc123.ngrok.io/api/auth/google/callback
```

#### 6. Restart Flask app

```bash
python backend/app.py
```

#### 7. Test OAuth

Open `https://abc123.ngrok.io` in your browser and click "Sign in with Google"

### Option B: Using localhost (Limited)

⚠️ **Note**: Some browsers block OAuth on `http://localhost` due to security policies.

#### 1. Update `.env`

```bash
GOOGLE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_secret_here
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/google/callback
```

#### 2. Ensure Google Console has localhost redirect

In **OAuth Credentials**, verify:
- Authorized redirect URI: `http://localhost:5000/api/auth/google/callback`

---

## 🚀 Railway Production Setup

### Step 1: Get your Railway domain

Your app is deployed at: `https://your-app.railway.app` or `https://taptolook.net`

### Step 2: Update Google Cloud Console

Add production redirect URI to **OAuth Credentials**:
- `https://taptolook.net/api/auth/google/callback`

### Step 3: Add Environment Variables to Railway

Go to Railway Dashboard → Your Service → **Variables** tab:

```
GOOGLE_OAUTH_ENABLED=true
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret_here
GOOGLE_REDIRECT_URI=https://taptolook.net/api/auth/google/callback
```

### Step 4: Deploy

Railway will auto-deploy when you update variables. Or manually trigger:

```bash
git push origin main
```

### Step 5: Verify

1. Open `https://taptolook.net`
2. Click "Sign in with Google"
3. Approve permissions
4. You should be logged in!

---

## 🧪 Testing the OAuth Flow

### Test Checklist

- [ ] **Status Endpoint**: `GET /api/auth/google/status`
  - Should return `{"enabled": true, "configured": true}`

- [ ] **Login Initiation**: Click "Sign in with Google"
  - Should redirect to Google consent screen
  - Check browser console for `[GOOGLE-AUTH]` logs

- [ ] **Google Consent**: Approve permissions
  - Should redirect back to your app

- [ ] **Callback Handling**: After redirect
  - Should see success message
  - User should be logged in
  - Check `localStorage.auth_token` in DevTools

- [ ] **User Profile**: After login
  - Avatar should load from Google
  - Email and name should match Google account

### Debug Logs

Enable detailed logging:

**Backend:**
```python
# backend/logger.py - set level to DEBUG
```

**Frontend:**
```javascript
// Check browser console for:
// [GOOGLE-AUTH] logs
```

### Common Test Scenarios

**1. First-time Google user**
- Creates new account in database
- Sets `provider='google'`
- No password stored

**2. Existing email user**
- Updates existing account to Google OAuth
- Migrates from `provider='email'` to `provider='google'`

**3. Canceled consent**
- User clicks "Cancel" on Google
- Should return error message gracefully

---

## 🔧 Troubleshooting

### Error: "redirect_uri_mismatch"

**Cause**: Redirect URI in code doesn't match Google Console

**Solution**:
1. Check `.env` → `GOOGLE_REDIRECT_URI`
2. Check Google Console → **Authorized redirect URIs**
3. Ensure they match EXACTLY (including http/https and trailing slashes)

### Error: "invalid_client"

**Cause**: Client ID or Secret is wrong

**Solution**:
1. Double-check `.env` credentials
2. Regenerate credentials in Google Console if needed
3. Ensure no extra spaces in `.env`

### Error: "access_denied"

**Cause**: User clicked "Cancel" or permissions denied

**Solution**:
- This is normal user behavior
- App shows error message
- User can retry

### Error: "State mismatch (CSRF protection)"

**Cause**: Session state doesn't match callback state

**Solution**:
1. Ensure Flask `SECRET_KEY` is set
2. Check browser allows cookies
3. Try clearing cookies and retry

### OAuth not enabled

**Symptom**: "Google OAuth not configured" error

**Solution**:
1. Check `.env`: `GOOGLE_OAUTH_ENABLED=true`
2. Check all 3 env vars are set:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
3. Restart Flask app

---

## 🔒 Security Best Practices

### ✅ DO

- **Use HTTPS** in production (Railway provides this)
- **Validate state token** (we do this)
- **Verify ID token** (we do this with `google.auth`)
- **Use minimal scopes** (we only request email, profile)
- **Store secrets in env vars** (never in code)
- **Rotate secrets** periodically in Google Console

### ❌ DON'T

- **Never commit** Client Secret to Git
- **Don't log** access tokens or refresh tokens
- **Don't share** credentials publicly
- **Don't use HTTP** in production
- **Don't skip** email verification check

### Secret Management

**.env** (local):
```bash
# Keep this file in .gitignore!
GOOGLE_CLIENT_SECRET=GOCSPX-xyz...
```

**.env.example** (commit this):
```bash
# Example configuration (no real secrets!)
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
```

**Railway** (production):
- Store secrets in Railway Variables tab
- Railway encrypts all environment variables

---

## 📝 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `GOOGLE_OAUTH_ENABLED` | Yes | Enable/disable Google OAuth | `true` or `false` |
| `GOOGLE_CLIENT_ID` | Yes* | OAuth Client ID from Google Console | `123...apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | Yes* | OAuth Client Secret | `GOCSPX-abc...` |
| `GOOGLE_REDIRECT_URI` | Yes* | Callback URL (must match Console) | `https://domain/api/auth/google/callback` |

\* Required only if `GOOGLE_OAUTH_ENABLED=true`

---

## 🎓 Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Security Best Practices](https://tools.ietf.org/html/rfc6819)
- [ngrok Documentation](https://ngrok.com/docs)

---

## ✅ Quick Start Checklist

- [ ] Create Google Cloud Project
- [ ] Enable Google+ API
- [ ] Configure OAuth Consent Screen
- [ ] Create OAuth 2.0 Credentials
- [ ] Copy Client ID and Secret
- [ ] Add redirect URIs to Google Console
- [ ] Update `.env` with credentials
- [ ] Set `GOOGLE_OAUTH_ENABLED=true`
- [ ] Restart Flask app
- [ ] Test login flow
- [ ] Deploy to Railway (if production)
- [ ] Update Railway environment variables
- [ ] Test production OAuth

---

**Need Help?**

If you encounter issues:
1. Check logs: `backend/logs/` and browser console
2. Verify all environment variables
3. Check Google Console settings
4. Review [Troubleshooting](#troubleshooting) section

---

*Generated with Claude Code*
*Co-Authored-By: Claude <noreply@anthropic.com>*
