# 🔧 Fixing Render Persistent Disk Storage

## ❌ Problem Found

Your `render.yaml` had **incorrect syntax**: 
- Used `disk:` (singular) 
- Should be `disks:` (plural array)

This has been **FIXED** in the updated `render.yaml`.

---

## ✅ Correct Configuration

```yaml
disks:
  - name: tracker-data
    mountPath: /data
    sizeGB: 1
```

**Note:** The disk MUST be created manually in Render dashboard first, THEN it will mount automatically!

---

## 📋 Step-by-Step Fix for Render.com

### Option 1: Add Disk via Render Dashboard (RECOMMENDED)

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com/
   - Select your service: `bettys-bomb-tracker`

2. **Navigate to Disks Tab**
   - Click on the "Disks" tab in the left sidebar
   - Click "Add Disk" button

3. **Configure Disk**
   - **Name:** `tracker-data` (must match render.yaml)
   - **Mount Path:** `/data` (must match render.yaml)
   - **Size:** `1 GB` (free tier includes 1GB)
   - Click "Save"

4. **Service Will Auto-Restart**
   - Render will automatically restart your service
   - The disk will now be mounted at `/data`
   - Your app will use `/data/tracker.db` for storage

5. **Verify in Logs**
   - Go to "Logs" tab
   - Look for: "Using: /data/tracker.db" (not local fallback)

---

### Option 2: Check if Disk Already Exists

If you already created a disk, verify:

1. **Check Disk Name**
   - Dashboard → Disks → Name should be `tracker-data`
   - NOT `tracker-disk` or anything else
   
2. **Check Mount Path**
   - Must be `/data` exactly
   - NOT `/app/data` or other paths

3. **Check Status**
   - Status should be "Active" or "Mounted"
   - If "Creating", wait a few minutes

---

## 🧪 Testing the Fix

### Test 1: After Pushing Updated Code

```bash
cd "/Users/shuza/Downloads/gargi bot"

# Commit the fixed render.yaml
git add render.yaml
git commit -m "Fix disk configuration: use disks array instead of disk object"
git push origin main
```

### Test 2: Wait for Deployment

1. Go to: https://dashboard.render.com/
2. Select: `bettys-bomb-tracker`
3. Watch "Logs" tab for:
   - "Deploy started"
   - "Build successful"
   - "Deploy live"

### Test 3: Check Disk Mounting

Visit: `https://bettys-bomb-tracker.onrender.com/?diagnostic=true`

This will show:
- ✅ /data mount EXISTS (should be green)
- ✅ Write/Read/Delete permissions OK
- ✅ tracker.db location and size
- ✅ Database integrity

---

## 🔍 Diagnostic Tools

### Quick Check (Terminal)

Once deployed, you can SSH into your Render service:

```bash
# Install Render CLI (one-time)
brew install render

# Login to Render
render login

# SSH into your service
render ssh bettys-bomb-tracker

# Check mount point
ls -lah /data
df -h /data
cat /proc/mounts | grep data

# Check database
ls -lah /data/*.db*
sqlite3 /data/tracker.db "SELECT COUNT(*) FROM markets;"
```

### Diagnostic URL

**After deployment, visit:**
```
https://bettys-bomb-tracker.onrender.com/?diagnostic=true
```

This will show a detailed HTML report with:
- Mount path status
- File permissions (read/write/delete)
- Disk usage
- Database integrity
- Table counts
- Environment variables

---

## 🐛 Common Issues & Solutions

### Issue 1: "⚠️ /data mount NOT FOUND"

**Cause:** Disk not created in Render dashboard

**Solution:**
1. Go to Dashboard → Disks → Add Disk
2. Name: `tracker-data`, Path: `/data`, Size: 1GB
3. Wait for service to restart
4. Check logs for "Using: /data/tracker.db"

---

### Issue 2: "Permission denied" when writing to /data

**Cause:** Incorrect disk permissions

**Solution:**
1. SSH into service: `render ssh bettys-bomb-tracker`
2. Check owner: `ls -ld /data`
3. Should be owned by your app user (usually `render`)
4. If not, contact Render support (rare issue)

---

### Issue 3: Disk shows in dashboard but not mounted

**Cause:** Service needs restart OR disk creation pending

**Solution:**
1. Click "Manual Deploy" → "Deploy latest commit"
2. Wait 2-3 minutes for restart
3. Check logs: should see "Mount /data" or similar
4. If still not working, delete disk and recreate

---

### Issue 4: Database resets after each deployment

**Cause:** Disk not properly configured

**Solution:**
1. Verify disk name EXACTLY matches `render.yaml`: `tracker-data`
2. Verify mount path EXACTLY matches: `/data`
3. Check persistence.py uses `/data` path (already correct)
4. Ensure no typos in disk configuration

---

## 📊 Expected Behavior After Fix

### Before Fix (Local Fallback):
```
⚠️ /data mount NOT FOUND (using local fallback)
Using: /Users/shuza/Downloads/gargi bot/data
```
❌ Data lost on each deployment

### After Fix (Persistent Disk):
```
✅ /data mount EXISTS
Using: /data/tracker.db
```
✅ Data persists across deployments

---

## 🚀 Deploy the Fix Now

```bash
cd "/Users/shuza/Downloads/gargi bot"

# Verify the fix in render.yaml
grep -A 3 "disks:" render.yaml

# Should show:
# disks:
#   - name: tracker-data
#     mountPath: /data
#     sizeGB: 1

# Push to GitHub
git add render.yaml
git commit -m "Fix persistent disk configuration in render.yaml"
git push origin main
```

**Then:**
1. Go to Render dashboard
2. Ensure disk is created (or create it now)
3. Wait for auto-deploy (2-5 minutes)
4. Visit `https://bettys-bomb-tracker.onrender.com/?diagnostic=true`
5. Verify "✅ /data mount EXISTS"

---

## 📞 Still Having Issues?

If disk still not mounting:

1. **Delete and Recreate Disk**
   - Dashboard → Disks → Delete `tracker-data`
   - Add new disk with exact same settings
   - Wait for restart

2. **Check Render Free Tier Limits**
   - Free tier includes 1GB persistent disk
   - Verify your account hasn't hit limits
   - Check billing page: https://dashboard.render.com/billing

3. **Contact Render Support**
   - Go to: https://render.com/help
   - Mention: "Persistent disk not mounting at /data"
   - Include: Service ID and disk name

---

## ✅ Verification Checklist

- [ ] `render.yaml` uses `disks:` (plural array)
- [ ] Disk created in Render dashboard
- [ ] Disk name: `tracker-data` (matches yaml)
- [ ] Mount path: `/data` (matches yaml)
- [ ] Disk size: 1 GB
- [ ] Disk status: Active/Mounted
- [ ] Code pushed to GitHub
- [ ] Render auto-deployed successfully
- [ ] Diagnostic URL shows "✅ /data mount EXISTS"
- [ ] tracker.db exists at `/data/tracker.db`

Once all checkboxes are ✅, your persistent storage is working! 🎉
