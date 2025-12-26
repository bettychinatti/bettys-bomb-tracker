"""
Advanced Market Load Tracker - Real-time Odds + Market Load Dashboard
Shows both live odds AND cumulative money flow tracking
PRO PLAN OPTIMIZED: Ultra-fast refresh for microsecond-precision tracking
"""
import streamlit as st
import requests
import sqlite3
from datetime import datetime
from pathlib import Path
import os
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="Market Load Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# PRO PLAN: Auto-refresh every 500ms (0.5 seconds) for real-time odds
# This ensures you never miss any bet movements
# Background tracker polls every 100ms, dashboard updates every 500ms
st_autorefresh(interval=500, key="datarefresh")

# Database path (same as background tracker)
if os.path.exists('/data'):
    DB_PATH = Path('/data') / 'tracker.db'
else:
    DB_PATH = Path(__file__).parent / 'data' / 'tracker.db'

# Dark Theme CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding: 1rem 2rem; max-width: 1600px; }
    h1, h2, h3, h4, h5, p, span, label, .stMarkdown { color: #e2e8f0 !important; }
    .stButton > button {
        background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; border-radius: 12px; padding: 0.75rem 1.5rem; font-weight: 600;
    }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4); }
    .stButton > button[kind="secondary"] { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); }
    div[data-testid="stMetric"] {
        background: rgba(102, 126, 234, 0.1); border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px; padding: 1rem;
    }
    div[data-testid="stMetric"] label { color: #a0aec0 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #f7fafc !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
    .load-card {
        background: rgba(30,30,50,0.9);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        border-left: 4px solid;
    }
    .load-positive { border-color: #10b981; }
    .load-negative { border-color: #ef4444; }
    .load-neutral { border-color: #6b7280; }
</style>
""", unsafe_allow_html=True)

SPORTS = [
    {"id": 4, "name": "Cricket", "icon": "🏏"},
    {"id": 1, "name": "Soccer", "icon": "⚽"},
    {"id": 2, "name": "Tennis", "icon": "🎾"},
    {"id": 7, "name": "Horse Racing", "icon": "🏇"},
]

# PRO PLAN: Ultra-fast refresh - NO CACHE for odds (always fresh)
# Events cache reduced to 10 seconds (for match list stability)
# Odds have NO cache - fetched fresh every 500ms with auto-refresh
@st.cache_data(ttl=10)
def fetch_all_events():
    try:
        headers = {"accept": "application/json", "origin": "https://d99exch.com", "referer": "https://d99exch.com/"}
        url = "https://api.d99exch.com/api/guest/event_list?sport_id=4"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("data", {}).get("events", [])
            return [e for e in events if e.get("in_play") == 1]
        return []
    except:
        return []

def get_events_by_sport(all_events, sport_id):
    return [e for e in all_events if e.get("event_type_id") == sport_id]

def fetch_odds(market_id, event_name=""):
    try:
        url = "https://odds.o99exch.com/ws/getMarketDataNew"
        headers = {"content-type": "application/x-www-form-urlencoded", "origin": "https://99exch.com"}
        resp = requests.post(url, data=f"market_ids[]={market_id}", headers=headers, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            if result and result[0]:
                return parse_odds(result[0], event_name)
    except:
        pass
    return None

def parse_odds(odds_str, event_name=""):
    try:
        parts = odds_str.split('|')
        runners = []
        team_names = []
        if ' v ' in event_name:
            team_names = [t.strip() for t in event_name.split(' v ', 1)]
        elif ' VS ' in event_name or ' vs ' in event_name:
            sep = ' VS ' if ' VS ' in event_name else ' vs '
            team_names = [t.strip() for t in event_name.split(sep, 1)]
        
        runner_idx = 0
        i = 0
        while i < len(parts):
            if parts[i] == 'ACTIVE':
                back_prices, lay_prices = [], []
                j = i + 1
                for _ in range(3):
                    if j + 1 < len(parts):
                        try:
                            back_prices.append({"price": float(parts[j]), "size": float(parts[j+1])})
                        except:
                            pass
                        j += 2
                for _ in range(3):
                    if j + 1 < len(parts):
                        try:
                            lay_prices.append({"price": float(parts[j]), "size": float(parts[j+1])})
                        except:
                            pass
                        j += 2
                name = team_names[runner_idx] if runner_idx < len(team_names) else f"Selection {runner_idx + 1}"
                runners.append({"name": name, "back": back_prices, "lay": lay_prices})
                runner_idx += 1
                i = j
            else:
                i += 1
        if len(runners) == 3 and len(team_names) == 2:
            runners[2]['name'] = "Draw"
        return {"runners": runners} if runners else None
    except:
        return None

def get_market_loads(market_id):
    """Fetch cumulative market load tracking from database"""
    try:
        if not DB_PATH.exists():
            return []
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at
            FROM cumulative
            WHERE market_id = ?
            ORDER BY team_label
        """, (str(market_id),))
        rows = cursor.fetchall()
        conn.close()
        return [{
            'team': row[0],
            'in_back': row[1],
            'in_lay': row[2],
            'out_back': row[3],
            'out_lay': row[4],
            'net_back': row[5],
            'net_lay': row[6],
            'updated': row[7]
        } for row in rows]
    except:
        return []

def format_stake(val):
    if val >= 100000:
        return f"₹{val/100000:.2f}L"
    elif val >= 1000:
        return f"₹{val/1000:.1f}K"
    return f"₹{val:.0f}"

def format_money(val):
    """Format with +/- sign for deltas"""
    sign = "+" if val >= 0 else ""
    if abs(val) >= 100000:
        return f"{sign}₹{val/100000:.2f}L"
    elif abs(val) >= 1000:
        return f"{sign}₹{val/1000:.1f}K"
    return f"{sign}₹{val:.0f}"

# MAIN UI
st.markdown("## 📊 Advanced Market Load Tracker - PRO EDITION")
st.markdown(f"*⚡ Real-time • Auto-refresh: 500ms • Last: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}*")

if 'sport' not in st.session_state:
    st.session_state.sport = 4

st.markdown("### 🎯 Select Sport")
sport_cols = st.columns(len(SPORTS))
for i, sport in enumerate(SPORTS):
    with sport_cols[i]:
        is_active = st.session_state.sport == sport['id']
        if st.button(f"{sport['icon']} {sport['name']}", key=f"sport_{sport['id']}", use_container_width=True, type="primary" if is_active else "secondary"):
            st.session_state.sport = sport['id']
            st.rerun()

st.markdown("---")
sport_id = st.session_state.sport
sport_info = next((s for s in SPORTS if s['id'] == sport_id), SPORTS[0])

# Stats sidebar
col1, col2 = st.columns([4, 1])

with col2:
    st.markdown("### 📈 Stats")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown('<div style="background: rgba(16, 185, 129, 0.1); padding: 10px; border-radius: 8px; text-align: center;"><span style="color: #10b981; font-weight: bold;">🔴 LIVE</span></div>', unsafe_allow_html=True)
    
    # DB status
    if DB_PATH.exists():
        st.markdown('<div style="background: rgba(59, 130, 246, 0.1); padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px;"><span style="color: #3b82f6; font-size: 0.8rem;">✓ Tracker Active</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background: rgba(234, 179, 8, 0.1); padding: 10px; border-radius: 8px; text-align: center; margin-top: 10px;"><span style="color: #eab308; font-size: 0.8rem;">⚠ Tracker Starting</span></div>', unsafe_allow_html=True)

with col1:
    st.markdown(f"### {sport_info['icon']} Live {sport_info['name']} Matches")
    all_events = fetch_all_events()
    events = get_events_by_sport(all_events, sport_id)
    
    if not events:
        st.info(f"No live {sport_info['name']} matches right now. Try another sport!")
    else:
        st.metric("🔴 Live Matches", len(events))
        
        # Group by competition
        competitions = {}
        for event in events:
            comp = event.get('competition_name', 'Other')
            if comp not in competitions:
                competitions[comp] = []
            competitions[comp].append(event)
        
        for comp_name, comp_events in competitions.items():
            st.markdown(f"**🏆 {comp_name}** ({len(comp_events)} matches)")
            
            for event in comp_events:
                event_name = event.get('name', 'Unknown')
                market_id = event.get('market_id', '')
                
                st.markdown(f"##### 🔴 {event_name}")
                
                if market_id:
                    # Get odds AND market loads
                    odds_data = fetch_odds(market_id, event_name)
                    load_data = get_market_loads(market_id)
                    
                    if odds_data and odds_data.get('runners'):
                        runners = odds_data['runners']
                        
                        # Display odds
                        cols = st.columns(len(runners))
                        for idx, runner in enumerate(runners):
                            with cols[idx]:
                                name = runner.get('name', f'Team {idx+1}')
                                back = runner.get('back', [{}])
                                lay = runner.get('lay', [{}])
                                bp = back[0].get('price', '-') if back else '-'
                                bs = back[0].get('size', 0) if back else 0
                                lp = lay[0].get('price', '-') if lay else '-'
                                ls = lay[0].get('size', 0) if lay else 0
                                
                                # Find matching load data for this team
                                load = next((l for l in load_data if l['team'] in name or name in l['team']), None)
                                
                                net_total = 0
                                load_color = 'neutral'
                                if load:
                                    net_total = load['net_back'] + load['net_lay']
                                    load_color = 'positive' if net_total > 0 else ('negative' if net_total < 0 else 'neutral')
                                
                                st.markdown(f'''
                                <div class="load-card load-{load_color}">
                                    <div style="color: #e2e8f0; font-weight: bold; margin-bottom: 8px; font-size: 0.95rem;">{name[:20]}</div>
                                    
                                    <!-- Odds -->
                                    <div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 10px;">
                                        <div style="background: rgba(72, 187, 120, 0.3); border-radius: 6px; padding: 6px 12px;">
                                            <div style="color: #48bb78; font-weight: bold;">{bp}</div>
                                            <div style="color: #68d391; font-size: 0.7rem;">{format_stake(bs)}</div>
                                        </div>
                                        <div style="background: rgba(245, 101, 101, 0.3); border-radius: 6px; padding: 6px 12px;">
                                            <div style="color: #f56565; font-weight: bold;">{lp}</div>
                                            <div style="color: #fc8181; font-size: 0.7rem;">{format_stake(ls)}</div>
                                        </div>
                                    </div>
                                    
                                    <!-- Market Load (if available) -->
                                    {"" if not load else f'''
                                    <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                                        <div style="font-size: 0.75rem; color: #94a3b8; margin-bottom: 4px;">💰 Market Load</div>
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 0.7rem;">
                                            <div style="color: #10b981;">📈 In: {format_stake(load['in_back'] + load['in_lay'])}</div>
                                            <div style="color: #ef4444;">📉 Out: {format_stake(load['out_back'] + load['out_lay'])}</div>
                                        </div>
                                        <div style="margin-top: 4px; font-weight: bold; color: {'#10b981' if net_total > 0 else '#ef4444' if net_total < 0 else '#6b7280'}; font-size: 0.8rem;">
                                            Net: {format_money(net_total)}
                                        </div>
                                    </div>
                                    '''}
                                </div>
                                ''', unsafe_allow_html=True)
                    else:
                        st.caption("⏳ Odds loading...")
                else:
                    st.caption("No market data")
                
                st.markdown("---")

st.caption("Advanced Market Load Tracker • Real-time odds + cumulative tracking")
