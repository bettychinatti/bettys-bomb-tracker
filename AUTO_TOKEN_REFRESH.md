# 🤖 Automated Token Refresh Guide

## Problem: Manual Token Updates Every 5 Hours

Your Bearer tokens expire every ~5 hours, requiring manual updates. This is tedious for 24/7 operation.

---

## ✅ Solution: Automated Token Management

I've added `token_manager.py` which automatically handles token refresh. **No more manual updates!**

---

## 🚀 Setup Options

### Option 1: Auto-Login with Credentials (RECOMMENDED) ⭐

**This completely automates token management - zero manual intervention needed.**

#### On Render.com:

1. **Go to your Render dashboard**
2. **Select `bettys-bomb-tracker` service**
3. **Click "Environment" tab**
4. **Add these environment variables:**
   
   | Key | Value | Example |
   |-----|-------|---------|
   | `EXCH_USERNAME` | Your 99exch.com username | `betty123` |
   | `EXCH_PASSWORD` | Your 99exch.com password | `YourP@ssw0rd` |

5. **Click "Save Changes"**
6. **Render will auto-redeploy** (takes ~2 minutes)

#### Locally:

```bash
# Add to your ~/.zshrc or ~/.bash_profile
export EXCH_USERNAME="your_username"
export EXCH_PASSWORD="your_password"

# Or set for current session only
export EXCH_USERNAME="your_username"
export EXCH_PASSWORD="your_password"

# Run the tracker
cd "/Users/shuza/Downloads/gargi bot"
source .venv/bin/activate
python3 background_tracker.py
```

**How it works:**
- Token manager detects credentials in environment variables
- Automatically logs in to 99exch.com API when token expires
- Refreshes token every 4.5 hours (30 min before expiration)
- Zero downtime, zero manual intervention

---

### Option 2: Manual Token Update (FALLBACK)

**If you prefer not to store credentials**, update the token manually when it expires:

#### Quick Update (2 minutes):

1. **Get fresh token from browser:**
   - Open 99exch.com in Chrome
   - Press F12 → Network tab
   - Refresh page
   - Find request to `api.d99exch.com/api/client/event_list`
   - Copy `authorization` header value (just the token part, not "bearer ")

2. **Update code:**
   ```bash
   cd "/Users/shuza/Downloads/gargi bot"
   
   # Edit dashboard.py line 29
   # Edit background_tracker.py line 13
   # Change BEARER_TOKEN_FALLBACK = "new_token_here"
   
   git add dashboard.py background_tracker.py
   git commit -m "Update bearer token"
   git push origin main
   ```

3. **Render auto-deploys** (2-3 minutes)

---

## 📊 How Automated Refresh Works

### Flow Diagram:

```
┌─────────────────────────────────────────────────────────┐
│ Background Tracker / Dashboard Starts                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ token_manager.py      │
         │ get_valid_token()     │
         └───────────┬───────────┘
                     │
            ┌────────┴────────┐
            │                 │
            ▼                 ▼
   ┌─────────────────┐   ┌──────────────────┐
   │ Credentials Set?│   │ No Credentials?  │
   │ (EXCH_USERNAME) │   │ Use Fallback     │
   └────────┬────────┘   └──────────────────┘
            │
            ▼
   ┌─────────────────┐
   │ Check Token     │
   │ Expiration      │
   └────────┬────────┘
            │
       ┌────┴─────┐
       │          │
       ▼          ▼
  ┌──────┐    ┌──────────┐
  │Valid?│    │ Expired? │
  │ Use  │    │ Refresh  │
  │ It   │    └────┬─────┘
  └──────┘         │
                   ▼
          ┌────────────────┐
          │ POST /api/auth │
          │ with username  │
          │ and password   │
          └────────┬───────┘
                   │
                   ▼
          ┌────────────────┐
          │ Get New Token  │
          │ (5hr validity) │
          └────────┬───────┘
                   │
                   ▼
          ┌────────────────┐
          │ Use New Token  │
          │ for API calls  │
          └────────────────┘
```

### Key Features:

1. **Automatic Expiration Detection:**
   - Decodes JWT token payload
   - Checks `exp` (expiration timestamp)
   - Refreshes 5 minutes before expiration

2. **Seamless Refresh:**
   - Logs in to API automatically
   - Extracts new token
   - Updates headers dynamically
   - No service interruption

3. **Fallback Protection:**
   - If auto-login fails, uses manual token
   - Logs warnings if fallback token expired
   - Prevents complete service failure

---

## 🔍 Testing Auto-Refresh

### Test Locally:

```bash
cd "/Users/shuza/Downloads/gargi bot"
source .venv/bin/activate

# Set credentials (replace with your actual credentials)
export EXCH_USERNAME="your_username"
export EXCH_PASSWORD="your_password"

# Run token manager test
python3 token_manager.py
```

**Expected output:**
```
============================================================
TOKEN MANAGER TEST
============================================================

1. Token Payload:
   Issuer: https://api.d99exch.com/api/auth
   Subject (User ID): 987294
   Issued At: 2025-12-26 12:11:07+00:00
   Expires At: 2025-12-26 17:11:07+00:00

2. Token Expiration:
   Is Expired: True

3. Auto-Login Test:
   [token] Attempting login for user: your_username
   [token] ✅ Login successful! Token expires at 2025-12-26 22:41:07 UTC
   Token: eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

============================================================
```

### Test API Call with Auto-Token:

```bash
python3 -c "
import requests
from token_manager import get_valid_token

# Get valid token (auto-refreshes if needed)
token = get_valid_token()

# Test API call
headers = {
    'Authorization': f'bearer {token}',
    'Accept': 'application/json',
}
resp = requests.get('https://api.d99exch.com/api/client/event_list', 
                   headers=headers, timeout=10)

print(f'Status: {resp.status_code}')
if resp.status_code == 200:
    events = resp.json().get('data', {}).get('events', [])
    print(f'✅ Found {len(events)} in-play events')
else:
    print(f'❌ Error: {resp.text[:200]}')
"
```

---

## 🔐 Security Best Practices

### ✅ DO:

1. **Use environment variables** (not hardcoded credentials)
2. **Keep credentials private** (never commit to git)
3. **Use different credentials** for production vs development
4. **Rotate passwords** regularly
5. **Monitor login attempts** for suspicious activity

### ❌ DON'T:

1. **Commit credentials to git** (especially public repos)
2. **Share credentials** with others
3. **Use your main account** (create a dedicated API account if possible)
4. **Store credentials in code files**
5. **Use same password** across multiple services

---

## 📝 Environment Variable Reference

| Variable | Required | Purpose | Example |
|----------|----------|---------|---------|
| `EXCH_USERNAME` | For auto-refresh | 99exch.com username | `betty123` |
| `EXCH_PASSWORD` | For auto-refresh | 99exch.com password | `MyP@ssw0rd` |

**If these are NOT set:**
- Falls back to manual `BEARER_TOKEN_FALLBACK`
- Still works, but requires manual token updates every 5 hours

---

## 🐛 Troubleshooting

### "Login failed with status 401"

**Cause:** Incorrect username or password

**Fix:**
1. Verify credentials are correct
2. Try logging in manually on 99exch.com
3. Check if account is locked/suspended
4. Ensure no special characters in password need escaping

### "Login response missing token"

**Cause:** API response format changed or login endpoint different

**Fix:**
1. Check browser network inspector for actual login endpoint
2. Update `login_url` in `token_manager.py` if needed
3. Verify response structure matches expected format

### "Token expired or invalid"

**Cause:** Fallback token expired and auto-login not configured

**Fix:**
1. Set `EXCH_USERNAME` and `EXCH_PASSWORD` env vars
2. Or update `BEARER_TOKEN_FALLBACK` manually

### Auto-refresh not working on Render

**Cause:** Environment variables not set or incorrect

**Fix:**
1. Go to Render dashboard → Environment tab
2. Verify `EXCH_USERNAME` and `EXCH_PASSWORD` are set
3. Check for typos in variable names (case-sensitive)
4. Click "Save Changes" to redeploy

---

## 📊 Token Lifecycle Example

```
Time: 12:00 PM - User logs in manually
Token issued: exp=17:00 (5 hours validity)

Time: 16:55 PM - Token Manager checks expiration
Token expires in 5 minutes → Triggers refresh
Auto-login → New token: exp=22:00

Time: 21:55 PM - Token Manager checks again
Token expires in 5 minutes → Triggers refresh
Auto-login → New token: exp=02:00

... continues indefinitely with zero manual intervention
```

---

## 🎯 Comparison: Manual vs Automated

| Feature | Manual Token | Automated Refresh |
|---------|--------------|-------------------|
| **Setup Time** | 2 minutes | 5 minutes (one-time) |
| **Maintenance** | Every 5 hours | Zero |
| **Downtime** | Yes (token expires) | No (seamless refresh) |
| **Security** | Token in code | Credentials in env vars |
| **Convenience** | ⭐ Low | ⭐⭐⭐⭐⭐ High |
| **Reliability** | ⭐⭐ Medium | ⭐⭐⭐⭐⭐ High |

---

## ✨ Quick Start (TL;DR)

**To enable fully automated token refresh:**

1. **On Render:**
   ```
   Dashboard → Your Service → Environment
   Add: EXCH_USERNAME = your_username
   Add: EXCH_PASSWORD = your_password
   Save Changes
   ```

2. **Push updated code:**
   ```bash
   cd "/Users/shuza/Downloads/gargi bot"
   git add token_manager.py dashboard.py background_tracker.py
   git commit -m "Add automated token refresh"
   git push origin main
   ```

3. **Done!** 🎉
   - No more manual token updates
   - 24/7 operation without intervention
   - Tokens auto-refresh every 4.5 hours

---

## 📞 Support

If auto-refresh isn't working:
1. Check Render logs for token manager messages
2. Look for `[token]` prefix in log output
3. Verify credentials are correct
4. Test locally first with `python3 token_manager.py`

**Your tracker now runs 24/7 with ZERO manual token management!** 🚀
