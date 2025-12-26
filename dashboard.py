"""
Advanced Market Load Tracker - Clean Modern Dashboard
"""
import streamlit as st
import requests
import time
from datetime import datetime
from token_manager import get_valid_token

st.set_page_config(
    page_title="Advanced Market Load Tracker",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {background:#fff}
    [data-testid="stHeader"] {background:#fff}
    .block-container {padding-top:2rem}
    div[data-testid="stMetric"] {background:#f8f9fa;padding:12px;border-radius:8px}
    #MainMenu {visibility:hidden}
    footer {visibility:hidden}
    .stDeployButton {display:none}
</style>
""", unsafe_allow_html=True)


def get_headers():
    token = get_valid_token()
    return {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token}" if token else "",
        "content-type": "application/json",
        "origin": "https://d99exch.com",
        "referer": "https://d99exch.com/",
    }


SPORTS = [
    {"id": 4, "name": "Cricket", "icon": "🏏"},
    {"id": 1, "name": "Soccer", "icon": "⚽"},
    {"id": 2, "name": "Tennis", "icon": "🎾"},
    {"id": 7, "name": "Horse Racing", "icon": "🏇"},
    {"id": 4339, "name": "Kabaddi", "icon": "🤼"},
]


def fetch_events(sport_id):
    try:
        url = "https://api.d99exch.com/api/client/event_list"
        payload = {"sport_id": sport_id, "is_inplay": True}
        resp = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("status") and "data" in data:
                return data["data"]
        return []
    except Exception as e:
        return []


def fetch_odds(event_id, market_id):
    try:
        url = "https://odds.o99exch.com/ws/getMarketDataNew"
        payload = {"event_id": str(event_id), "market_id": str(market_id)}
        resp = requests.post(url, json=payload, headers=get_headers(), timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None


def format_stake(val):
    if val >= 100000:
        return f"₹{val/100000:.1f}L"
    elif val >= 1000:
        return f"₹{val/1000:.1f}K"
    return f"₹{val:.0f}"


# Header
st.markdown("## 📊 Advanced Market Load Tracker")
st.caption("Real-time odds monitoring")

# Initialize
if 'sport' not in st.session_state:
    st.session_state.sport = 4

# Sport selector
st.markdown("### Select Sport")
sport_cols = st.columns(len(SPORTS))
for i, sport in enumerate(SPORTS):
    with sport_cols[i]:
        btn = st.button(
            f"{sport['icon']} {sport['name']}", 
            key=f"s{sport['id']}",
            use_container_width=True,
            type="primary" if st.session_state.sport == sport['id'] else "secondary"
        )
        if btn:
            st.session_state.sport = sport['id']
            st.rerun()

st.divider()

# Get sport info
sport_id = st.session_state.sport
sport_name = next((s['name'] for s in SPORTS if s['id'] == sport_id), "Cricket")
sport_icon = next((s['icon'] for s in SPORTS if s['id'] == sport_id), "🏏")

# Layout
left, right = st.columns([3, 1])

with right:
    st.markdown("### 📈 Stats")
    refresh = st.button("🔄 Refresh", use_container_width=True)
    if refresh:
        st.rerun()
    auto = st.checkbox("Auto-refresh (30s)")
    st.markdown(f"**Last update:** {datetime.now().strftime('%H:%M:%S')}")

with left:
    st.markdown(f"### {sport_icon} Live {sport_name} Events")
    
    events = fetch_events(sport_id)
    
    if not events:
        st.info(f"No live {sport_name.lower()} events right now")
    else:
        st.metric("Live Events", len(events))
        
        for event in events[:15]:
            name = event.get('event_name', 'Unknown')
            eid = event.get('event_id', '')
            mid = event.get('market_id', '')
            
            with st.expander(f"🔴 {name}", expanded=False):
                if mid:
                    odds = fetch_odds(eid, mid)
                    if odds and 'runners' in odds:
                        runners = odds['runners']
                        cols = st.columns(len(runners))
                        for idx, runner in enumerate(runners):
                            with cols[idx]:
                                rname = runner.get('name', f'Team {idx+1}')
                                backs = runner.get('back', [{}])
                                lays = runner.get('lay', [{}])
                                
                                bp = backs[0].get('price', '-') if backs else '-'
                                bs = backs[0].get('size', 0) if backs else 0
                                lp = lays[0].get('price', '-') if lays else '-'
                                ls = lays[0].get('size', 0) if lays else 0
                                
                                st.markdown(f"**{rname[:20]}**")
                                c1, c2 = st.columns(2)
                                with c1:
                                    st.markdown(f"🔵 Back: **{bp}**")
                                    st.caption(format_stake(bs))
                                with c2:
                                    st.markdown(f"🔴 Lay: **{lp}**")
                                    st.caption(format_stake(ls))
                    else:
                        st.caption("Loading odds...")
                else:
                    st.caption("No market data")

if auto:
    time.sleep(30)
    st.rerun()
