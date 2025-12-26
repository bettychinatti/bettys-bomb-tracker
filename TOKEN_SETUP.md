# 🔐 Bearer Token Setup Guide

## Why Authentication is Required

The betting exchange API requires Bearer token authentication to:
- Prevent abuse from unauthorized users
- Block cloud hosting IPs from scraping data
- Ensure only logged-in users can access market data

**Without authentication, you'll get 403 Forbidden errors on Render.com (or any cloud platform).**

---

## How to Get Your Bearer Token

### Method 1: From Browser Network Inspector (Quick)

1. **Open 99exch.com in Chrome/Firefox**
2. **Login to your account**
3. **Open Developer Tools:**
   - Chrome: `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
   - Firefox: `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
4. **Go to Network tab**
5. **Refresh the page or navigate to in-play section**
6. **Find request to:** `api.d99exch.com/api/client/event_list`
7. **Click on the request**
8. **View Request Headers section**
9. **Copy the `authorization` header value** (looks like: `bearer eyJ0eXAiOiJKV1Qi...`)

### Method 2: From Console (Alternative)

1. **Open 99exch.com in browser**
2. **Login to your account**
3. **Open Developer Console** (`F12` → Console tab)
4. **Run this JavaScript:**
   ```javascript
   // Extract token from localStorage or API call
   console.log(localStorage.getItem('auth_token'));
   // Or intercept next API call
   let originalFetch = window.fetch;
   window.fetch = function(...args) {
       console.log('Request:', args);
       return originalFetch.apply(this, args);
   };
   ```
5. **Refresh page and look for authorization header in logged requests**

---

## Token Format

Your token should look like this:

```
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5kOTlleGNoLmNvbS9hcGkvYXV0aCIsImlhdCI6MTc2Njc0NTQ2NywiZXhwIjoxNzY2NzYzNDY3LCJuYmYiOjE3NjY3NDU0NjcsImp0aSI6IlRNd1IwTjNwQVRQcFVIWkkiLCJzdWIiOiI5ODcyOTQiLCJwcnYiOiI4N2UwYWYxZWY5ZmQxNTgxMmZkZWM5NzE1M2ExNGUwYjA0NzU0NmFhIn0.XE3AIrm60v-No5wuNmSwDBGHZgNSYUk5S4C4kGJYd7U
```

**Do NOT include "bearer " prefix - just the token itself.**

---

## Updating the Token in Your Code

### Option A: Direct Edit (Quick & Simple)

**Edit these 2 files:**

1. **`dashboard.py`** (line ~26):
   ```python
   BEARER_TOKEN = "YOUR_TOKEN_HERE"
   ```

2. **`background_tracker.py`** (line ~10):
   ```python
   BEARER_TOKEN = "YOUR_TOKEN_HERE"
   ```

Then commit and push:
```bash
git add dashboard.py background_tracker.py
git commit -m "Update bearer token"
git push origin main
```

Render will auto-deploy the changes.

### Option B: Environment Variable (More Secure)

**For production, use environment variables to avoid committing tokens to git.**

1. **Update `dashboard.py` and `background_tracker.py`:**
   ```python
   import os
   BEARER_TOKEN = os.getenv("BEARER_TOKEN", "fallback_token_here")
   ```

2. **Set environment variable on Render:**
   - Go to Render dashboard
   - Select your service
   - Click "Environment" tab
   - Add key: `BEARER_TOKEN`
   - Add value: `your_token_here`
   - Click "Save Changes"

Render will automatically redeploy with the new environment variable.

---

## Token Expiration

**Tokens expire every ~5 hours** (based on JWT `exp` field).

### Signs Your Token Has Expired:
- Render logs show: `403 Client Error: Forbidden`
- Dashboard shows: "No events found"
- Network requests fail with 401/403 errors

### Solution:
1. Get a fresh token from browser (see Method 1 above)
2. Update the token in your code or environment variable
3. Redeploy (Render auto-deploys on git push)

---

## Automation Options (Advanced)

### Option 1: Manual Refresh Every 4 Hours
Set a reminder to update the token every 4 hours before it expires.

### Option 2: Token Refresh Endpoint (If Available)
If 99exch.com has a token refresh API endpoint:
```python
def refresh_token(old_token):
    resp = requests.post("https://api.d99exch.com/api/auth/refresh", 
                        headers={"Authorization": f"bearer {old_token}"})
    return resp.json()['token']
```

### Option 3: Login Automation (Not Recommended)
Automate browser login with Selenium/Puppeteer to extract tokens. **Risky and against ToS.**

### Option 4: Multiple Tokens with Rotation
- Get tokens from multiple browser sessions
- Store in environment variables: `TOKEN_1`, `TOKEN_2`, `TOKEN_3`
- Rotate when one expires

---

## Testing Your Token

**Quick test script:**

```python
import requests

TOKEN = "your_token_here"
HEADERS = {
    "Authorization": f"bearer {TOKEN}",
    "Accept": "application/json",
}

resp = requests.get("https://api.d99exch.com/api/client/event_list", 
                   headers=HEADERS, timeout=10)

if resp.status_code == 200:
    print("✅ Token is valid!")
    print(f"Found {len(resp.json().get('data', {}).get('events', []))} events")
elif resp.status_code == 401:
    print("❌ Token expired or invalid")
elif resp.status_code == 403:
    print("❌ Token forbidden (may be IP restricted)")
else:
    print(f"❌ Error: {resp.status_code}")
```

Run locally:
```bash
cd "/Users/shuza/Downloads/gargi bot"
python3 -c "import requests; ..."
```

---

## Security Best Practices

### ✅ DO:
- Use environment variables for production
- Rotate tokens regularly
- Keep tokens private (don't commit to public repos)
- Use `.gitignore` to exclude token files

### ❌ DON'T:
- Commit tokens to git (especially public repos)
- Share tokens with others
- Use expired tokens
- Hardcode tokens in production code

---

## Token Decoded (Example)

Your JWT token contains:

**Header:**
```json
{
  "typ": "JWT",
  "alg": "HS256"
}
```

**Payload:**
```json
{
  "iss": "https://api.d99exch.com/api/auth",
  "iat": 1766745467,  // Issued at: Dec 26, 2025 12:11:07 GMT
  "exp": 1766763467,  // Expires at: Dec 26, 2025 17:11:07 GMT (~5 hours)
  "nbf": 1766745467,  // Not before: Dec 26, 2025 12:11:07 GMT
  "jti": "TMwR0N3pATPpUHZI",  // Unique token ID
  "sub": "987294",  // User ID
  "prv": "87e0af1ef9fd15812fdec97153a14e0b047546aa"  // Provider hash
}
```

**Use https://jwt.io to decode your token and check expiration time.**

---

## Troubleshooting

### "403 Forbidden" on Render
- **Cause:** Token expired or missing
- **Fix:** Update token in code or environment variable

### "401 Unauthorized"
- **Cause:** Invalid token format
- **Fix:** Verify token copied correctly (no extra spaces, complete string)

### Token Works Locally But Not on Render
- **Cause:** Possible IP restrictions on cloud platforms
- **Fix:** Ensure using correct API endpoints (d99exch.com, not d99hub.com)

### Token Expires Too Quickly
- **Cause:** Normal behavior (5-hour expiration)
- **Fix:** Set up token rotation or manual refresh every 4 hours

---

## Current Token Status

**Your current token (from browser):**
- Issued: Dec 26, 2025 12:11:07 GMT (IST 17:41:07)
- Expires: Dec 26, 2025 17:11:07 GMT (IST 22:41:07)
- Lifetime: 5 hours
- User ID: 987294

**Next update needed:** Before 22:41 IST today.

---

## Quick Reference

| Task | Command |
|------|---------|
| Get token from browser | F12 → Network → api.d99exch.com → Authorization header |
| Update token in code | Edit `BEARER_TOKEN` in `dashboard.py` and `background_tracker.py` |
| Deploy to Render | `git push origin main` (auto-deploys) |
| Set env variable | Render dashboard → Environment → Add `BEARER_TOKEN` |
| Test token validity | See "Testing Your Token" script above |
| Decode token | https://jwt.io |

---

**Your tracker is now configured for authenticated API access! 🔐**

Once you update the token and redeploy, Render will work perfectly at **$0/month**. 🎉
