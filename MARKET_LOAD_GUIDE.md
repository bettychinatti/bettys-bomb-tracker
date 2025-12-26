# 📊 Market Load Tracking - Complete Guide

## What is Market Load Tracking?

**Market Load** = The cumulative flow of money (stakes) on each team over time

The background tracker monitors every single bet placed on every live match and tracks:
- **Money IN** (stakes placed) 
- **Money OUT** (stakes withdrawn/cancelled)
- **NET FLOW** (total money movement)

---

## 🔍 What You See in the Dashboard

### 1. **Live Odds** (Top Section)
- 🟢 **BACK** (green) - Best price to bet FOR a team + stake available
- 🔴 **LAY** (red) - Best price to bet AGAINST a team + stake available
- Updates every 5 seconds from live API

### 2. **Market Load** (Bottom Section - NEW!)
Each team card now shows:

```
💰 Market Load
📈 In: ₹2.5L    📉 Out: ₹1.2L
Net: +₹1.3L
```

**What this means:**

| Metric | Meaning | Color |
|--------|---------|-------|
| **📈 In** | Total money STAKED on this team | Green |
| **📉 Out** | Total money WITHDRAWN from this team | Red |
| **Net** | Net money flow (In - Out) | Green if +, Red if - |

---

## 💡 How to Read Market Load

### Example 1: Heavy Backing
```
📈 In: ₹5.2L    📉 Out: ₹0.8L
Net: +₹4.4L (GREEN)
```
**Interpretation:** 
- ✅ Strong confidence in this team
- Big money flowing IN (+5.2L)
- Little money being withdrawn (0.8L)
- **NET +4.4L = Heavy backing**

---

### Example 2: Money Draining Out
```
📈 In: ₹1.0L    📉 Out: ₹3.5L
Net: -₹2.5L (RED)
```
**Interpretation:**
- ❌ Bettors losing confidence
- More money being withdrawn (3.5L) than staked (1.0L)
- **NET -2.5L = Money draining away**

---

### Example 3: Balanced Market
```
📈 In: ₹2.0L    📉 Out: ₹1.9L
Net: +₹0.1L (NEUTRAL)
```
**Interpretation:**
- ⚖️ Market is balanced
- Equal amounts coming in and going out
- **NET ≈0 = No strong sentiment**

---

## 🎯 Trading Strategies Using Market Load

### Strategy 1: Follow the Money
If you see:
- **Team A: Net +₹5.0L** (green, heavy backing)
- **Team B: Net -₹2.0L** (red, money leaving)

**Signal:** Smart money is on Team A → Consider backing Team A

---

### Strategy 2: Contrarian Play
If odds DON'T match the money flow:
- **Team A: Net +₹10L but odds are drifting OUT (getting longer)**

**Signal:** Market might be overreacting → Possible value bet

---

### Strategy 3: Late Money
Watch for sudden spikes in Net flow near match start:
- **5 mins before: Net +₹0.5L**
- **1 min before: Net +₹5.0L**

**Signal:** Late insider money → Strong signal

---

## 🔄 How the Tracking Works

### Background Tracker (Runs Automatically)
```
Every 1 second:
  ├─ Fetch odds for all live markets
  ├─ Calculate BACK/LAY stake changes
  ├─ Detect money IN (+) or OUT (-)
  └─ Store cumulative totals in database
```

### Dashboard (Shows Data)
```
Every 5 seconds:
  ├─ Fetch live odds (for current prices)
  ├─ Fetch cumulative load (from database)
  └─ Display BOTH together
```

---

## 📊 Understanding the Numbers

### Units (Indian Rupees)
- **₹1K** = ₹1,000 (thousand)
- **₹1L** = ₹1,00,000 (lakh = 100,000)
- **₹1Cr** = ₹1,00,00,000 (crore = 10,000,000)

### Time Windows
The tracker starts when a match goes **IN-PLAY (live)**:
- **Net +₹5L** = Total +5L since match started
- Not per-minute, but cumulative from start

---

## 🚨 Important Notes

### 1. Market Load ≠ Final Score
Market load shows **betting confidence**, not guaranteed outcome.

### 2. Data Availability
- **Tracked markets:** Show "💰 Market Load" section
- **New markets:** Show "⚠ Tracker Starting" (data available after 30s-1min)
- **No data:** Only shows odds (tracker not reached this market yet)

### 3. Refresh Rate
- **Odds:** Update every 5 seconds
- **Market Load:** Updates every 1-2 seconds (from background tracker)
- Click "🔄 Refresh" button to force update

---

## 🎨 Visual Indicators

### Card Border Colors
- **🟢 Green border:** Net positive (money flowing in)
- **🔴 Red border:** Net negative (money draining out)  
- **⚪ Gray border:** Neutral (balanced)

### Net Flow Colors
- **Green text:** Positive net flow (+)
- **Red text:** Negative net flow (-)
- **Gray text:** Zero flow (0)

---

## 🔧 Troubleshooting

### "No Market Load showing"
**Possible reasons:**
1. Match just went live (wait 30-60 seconds)
2. Background tracker starting (check "Stats" panel for "✓ Tracker Active")
3. Database not mounted (check Render disk configuration)

**Fix:**
- Wait 1 minute for tracker to start
- Click "🔄 Refresh" button
- Check Render logs for "tracker started"

---

### "Tracker Starting" message persists
**Cause:** Database not created yet

**Fix:**
1. SSH into Render: `render ssh bettys-bomb-tracker`
2. Check: `ls -lah /data/tracker.db`
3. Should exist after ~1 minute of runtime
4. Check logs: `grep "tracker" /var/log/*.log`

---

### Market Load shows 0 for all teams
**Cause:** No deltas detected yet (market just started)

**Fix:**
- Wait for bets to be placed (30-60 seconds)
- More active markets show data faster
- Less liquid markets may take 2-3 minutes

---

## 🎓 Real-World Example

### Live Cricket Match: Australia v England

#### Team Cards Display:

**🇦🇺 Australia**
```
🟢 2.50     🔴 2.52
₹250K       ₹180K

💰 Market Load
📈 In: ₹8.5L    📉 Out: ₹1.2L
Net: +₹7.3L
```
✅ Heavy backing (net +7.3L) → Market confident in Australia

**🏴󐁧󐁢󐁥󐁮󐁧󐁿 England**
```
🟢 1.80     🔴 1.82
₹120K       ₹200K

💰 Market Load
📈 In: ₹2.0L    📉 Out: ₹4.5L
Net: -₹2.5L
```
❌ Money draining (net -2.5L) → Market losing confidence in England

**Interpretation:**
- Smart money is on Australia (heavy net inflow)
- England money being withdrawn (negative net)
- **Trade:** Back Australia or Lay England

---

## 📈 Advanced: Tracking Market Momentum

### Watching Net Flow Changes

Use "🔄 Refresh" button every 30 seconds to see momentum:

**10:30 AM**
- Australia: Net +₹2.0L
- England: Net +₹1.5L

**10:31 AM** (after refresh)
- Australia: Net +₹5.2L ⬆️ (+3.2L in 1 min!)
- England: Net +₹1.6L ➡️ (barely moved)

**Signal:** Sudden ₹3.2L spike on Australia = Strong momentum!

---

## 🎯 Key Takeaways

1. **Green Net (+)** = Money flowing IN → Confidence HIGH
2. **Red Net (-)** = Money flowing OUT → Confidence LOW
3. **Sudden spikes** = Important signal (insider info?)
4. **Match odds + Load together** = Complete picture
5. **Refresh regularly** = Catch momentum shifts early

---

## 🚀 Next Steps

1. **Watch a few matches** to understand the patterns
2. **Compare Net Flow vs Actual Results** over time
3. **Note which signals work best** for your strategy
4. **Use with other indicators** (form, pitch, weather, etc.)

**Remember:** Market load is ONE tool. Always combine with:
- Match situation (score, wickets, overs)
- Form and team strength  
- Weather and pitch conditions
- Your own analysis

---

## 📞 Questions?

- Not showing market load? → Check "Tracker Active" indicator in Stats panel
- Wrong team names? → Background tracker uses event name parsing
- Numbers seem off? → Wait 2-3 minutes for accurate cumulative data

**Happy tracking! 📊💰**
