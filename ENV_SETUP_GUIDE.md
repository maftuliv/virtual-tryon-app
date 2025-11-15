# Environment Variables Setup Guide

This guide explains all environment variables required for the Virtual Try-On application.

## 📋 Quick Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in the required values
3. **Never commit `.env` to git** (it's already in `.gitignore`)

---

## 🔐 Required Variables

### DATABASE_URL (REQUIRED)
**PostgreSQL connection string**

```env
DATABASE_URL=postgresql://user:password@host:port/database
```

**How to get it:**
- **Railway**: Dashboard → Your Project → Variables → DATABASE_URL (copy the value)
- **Local PostgreSQL**:
  ```
  postgresql://postgres:your_password@localhost:5432/virtual_tryon
  ```

**Used by:**
- User authentication system
- Daily generation limits tracking
- Device fingerprinting for free users
- Admin panel and statistics

**⚠️ CRITICAL**: Without this variable:
- Authentication won't work
- Free user limits won't be enforced
- Database utility scripts will fail

---

### JWT_SECRET_KEY (REQUIRED)
**Secret key for JWT token signing**

```env
JWT_SECRET_KEY=your_64_character_random_string_here
```

**How to generate:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

**Security Notes:**
- **MUST be random and unpredictable**
- **NEVER share this key**
- **NEVER commit to version control**
- Changing this will invalidate all existing user sessions

**⚠️ WARNING**: If not set:
- A temporary key is auto-generated on server start
- All user sessions will be lost on server restart
- Not suitable for production

---

## 🔌 API Configuration

### NANOBANANA_API_KEY (REQUIRED for try-on)
**Nano Banana API for virtual try-on**

```env
NANOBANANA_API_KEY=your_api_key_here
```

**How to get it:**
1. Visit https://nanobananaapi.ai/
2. Sign up for an account
3. Navigate to API Keys section
4. Generate a new API key

**Pricing**: ~$0.02 per image
**Documentation**: https://docs.nanobananaapi.ai/

---

### FASHN_API_KEY (OPTIONAL)
**Alternative try-on API (currently not used)**

```env
FASHN_API_KEY=your_fashn_api_key_here
```

**How to get it:**
1. Visit https://app.fashn.ai/api
2. Sign up and purchase credits
3. Copy your API key

**Note**: Currently the app uses Nano Banana API by default

---

## 📬 Notification Configuration (OPTIONAL)

### TELEGRAM_BOT_TOKEN
**Telegram bot for feedback notifications**

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

**How to get it:**
1. Open Telegram and message @BotFather
2. Send `/newbot` and follow instructions
3. Copy the token provided by BotFather

See [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) for detailed guide.

---

### TELEGRAM_CHAT_ID (OPTIONAL)
**Telegram chat ID to receive notifications**

```env
TELEGRAM_CHAT_ID=123456789
```

**How to get it:**
1. Message your bot (send `/start`)
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for `"chat":{"id":123456789}`

**Note**: If not set, the bot will auto-detect from first message.

---

## ⚙️ Server Configuration

### FLASK_ENV
```env
FLASK_ENV=production
```

**Values:**
- `production` - Production mode (recommended for Railway)
- `development` - Development mode with debug features

---

### FLASK_DEBUG
```env
FLASK_DEBUG=0
```

**Values:**
- `0` - Debug mode OFF (recommended for production)
- `1` - Debug mode ON (only for local development)

**⚠️ WARNING**: NEVER enable debug mode in production!

---

### HOST / PORT
```env
HOST=0.0.0.0
PORT=5000
```

**Railway note**: Railway automatically sets `PORT` variable, so this is only for local development.

---

## 🔍 Diagnostics (OPTIONAL)

### ENABLE_STARTUP_DIAGNOSTICS
```env
ENABLE_STARTUP_DIAGNOSTICS=0
```

**Values:**
- `0` - Diagnostics OFF (default)
- `1` - Diagnostics ON (shows all env vars on startup)

**Use when:**
- Debugging Railway deployment issues
- Verifying environment variables are loaded
- Troubleshooting API key problems

**⚠️ WARNING**: This will print masked secrets to logs. Only enable temporarily for debugging.

---

## 📝 Complete Example

```env
# Required
DATABASE_URL=postgresql://postgres:mypassword@localhost:5432/virtual_tryon
JWT_SECRET_KEY=ZJK3n2xK9mP4vL7wQ5yR8tU6iO0pA1sD3fG4hJ5kL6zX8cV9bN1mQ2wE3rT4yU5iO

# API Keys
NANOBANANA_API_KEY=fc2af66aeb85b001d8a346958ff202c6

# Notifications (optional)
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Server
FLASK_ENV=production
FLASK_DEBUG=0
HOST=0.0.0.0
PORT=5000
```

---

## 🚀 Railway Deployment

When deploying to Railway:

1. **Do NOT upload `.env` file** to Railway
2. Instead, set variables in Railway Dashboard:
   - Project → Variables
   - Click "New Variable"
   - Add each variable manually

3. **Required for Railway:**
   - `DATABASE_URL` - Auto-provided by Railway PostgreSQL plugin
   - `JWT_SECRET_KEY` - Generate and add manually
   - `NANOBANANA_API_KEY` - Add manually

4. After adding variables, redeploy:
   ```bash
   git push
   ```

---

## ✅ Verification Checklist

After setting up environment variables, verify:

- [ ] `DATABASE_URL` is set and connects to PostgreSQL
- [ ] `JWT_SECRET_KEY` is a long random string (64+ characters)
- [ ] `NANOBANANA_API_KEY` is valid and has credits
- [ ] `.env` file is in `.gitignore` (never commit secrets!)
- [ ] Railway variables match your local `.env` (for production)

Test connection:
```bash
cd virtual-tryon-app
python backend/db_config.py  # Should not show errors
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` to git**
   - Already in `.gitignore`
   - Use `.env.example` for templates only

2. **Use strong random secrets**
   - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(64))"`
   - Minimum 32 characters for JWT_SECRET_KEY

3. **Different secrets per environment**
   - Use different `JWT_SECRET_KEY` for local, staging, and production
   - This prevents token replay attacks

4. **Rotate secrets periodically**
   - Change `JWT_SECRET_KEY` every 6-12 months
   - Note: This will log out all users

5. **Backup your secrets securely**
   - Store in password manager (1Password, LastPass, etc.)
   - Document in team's secure vault

---

## ❓ Troubleshooting

### "DATABASE_URL environment variable is not set"
- **Cause**: `.env` file missing or variable not set
- **Fix**: Copy `.env.example` to `.env` and fill in DATABASE_URL

### "JWT_SECRET_KEY not set. Generated a temporary secret"
- **Cause**: JWT_SECRET_KEY missing from environment
- **Fix**: Add `JWT_SECRET_KEY` to your `.env` file
- **Warning**: Temporary keys reset on server restart

### "Cannot connect to database"
- **Cause**: Wrong DATABASE_URL or database not running
- **Fix**:
  1. Check DATABASE_URL format: `postgresql://user:password@host:port/database`
  2. Verify PostgreSQL is running
  3. Test connection: `psql $DATABASE_URL`

### Railway: "Module 'backend.db_config' not found"
- **Cause**: Missing files in deployment
- **Fix**: Ensure all files are committed and pushed to git

---

## 📚 Related Documentation

- [POSTGRESQL_SETUP.md](POSTGRESQL_SETUP.md) - PostgreSQL installation guide
- [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) - Telegram bot setup
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Railway deployment
- [BACKUP_GUIDE.md](BACKUP_GUIDE.md) - Database backup instructions

---

## 🆘 Need Help?

If you encounter issues:

1. Check this guide first
2. Review error messages carefully
3. Verify all required variables are set
4. Test each component individually
5. Check Railway logs for deployment issues

**Common issues are usually:**
- Missing or incorrect DATABASE_URL
- Missing JWT_SECRET_KEY
- Wrong API keys
- Database not accessible
