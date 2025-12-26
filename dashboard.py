"""
Advanced Market Load Tracker - Real-time Odds Dashboard
"""
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Market Load Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Dark Theme CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding: 1rem 2rem; max-width: 1400px; }
    h1, h2, h3, h4, h5, p, span, label, .stMarkdown { color: #e2e8f0 !important; }
    .stButton > button {
        background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }
    div[data-testid="stMetric"] {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label { color: #a0aec0 !important; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #f7fafc !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)

SPORTS = [
    {"id": 4, "name": "Cricket", "icon": "🏏"},
    {"id": 1, "name": "Soccer", "icon": "⚽"},
    {"id": 2, "name": "Tennis", "icon": "��"},
    {"id": 7, "name": "Horse Racing", "icon": "🏇"},
]

@st.cache_data(ttl=5)
def fetch_events_by_sport(sport_id):
    """Fetch live events for a specific sport"""
    try:
        headers = {"accept": "application/json", "origin": "https://d99exch.com", "referer": "https://d99exch.com/"}
        url = f"https://api.d99exch.com/api/guest/event_list?sport_id={sport_id}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("data", {}).get("events", [])
            # Return only live events and remove duplicates by market_id
            live_events = [e for e in events if e.get("in_play") == 1]
            # Deduplicate by market_id
            seen_markets = set()
            unique_events = []
            for event in live_events:
                market_id = event.get("market_id")
                if market_id and market_id not in seen_markets:
                    seen_markets.add(market_id)
                    unique_events.append(event)
            return unique_events
        return []
    except:
        return []

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

def format_stake(val):
    if val >= 100000:
        return f"₹{val/100000:.1f}L"
    elif val >= 1000:
        return f"₹{val/1000:.1f}K"
    return f"₹{val:.0f}"

def sort_events_by_odds_availability(events):
    """Sort events so matches with available odds appear first"""
    events_with_status = []
    
    for event in events:
        market_id = event.get('market_id', '')
        has_odds = False
        odds_data = None
        
        if market_id:
            # Fetch odds once and cache in wrapper
            odds_data = fetch_odds(market_id, event.get('name', ''))
            if odds_data and odds_data.get('runners'):
                has_odds = True
        
        events_with_status.append({
            'event': event,
            'has_odds': has_odds,
            'odds_data': odds_data  # Cache the odds data
        })
    
    # Sort: odds available first (True before False)
    events_with_status.sort(key=lambda x: x['has_odds'], reverse=True)
    
    # Return sorted events with their odds status
    return events_with_status

# MAIN UI
st.markdown("## 📊 Advanced Market Load Tracker")
st.markdown(f"*Real-time odds • Last updated: {datetime.now().strftime('%H:%M:%S')}*")

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

col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("### 📈 Stats")
    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown('<div style="background: rgba(16, 185, 129, 0.1); padding: 10px; border-radius: 8px; text-align: center;"><span style="color: #10b981;">🔴 LIVE</span></div>', unsafe_allow_html=True)

with col1:
    st.markdown(f"### {sport_info['icon']} Live {sport_info['name']} Matches")
    events = fetch_events_by_sport(sport_id)
    
    if not events:
        st.info(f"No live {sport_info['name']} matches right now. Try another sport!")
    else:
        st.metric("🔴 Live Matches", len(events))
        
        # Sort events: odds available first
        sorted_events = sort_events_by_odds_availability(events)
        
        # Group by competition (maintaining sort order)
        competitions = {}
        for event_wrapper in sorted_events:
            event = event_wrapper['event']
            comp = event.get('competition_name', 'Other')
            if comp not in competitions:
                competitions[comp] = []
            competitions[comp].append(event_wrapper)
        
        for comp_name, comp_events in competitions.items():
            st.markdown(f"**🏆 {comp_name}** ({len(comp_events)} matches)")
            
            for event_wrapper in comp_events:
                event = event_wrapper['event']
                has_odds = event_wrapper['has_odds']
                odds_data = event_wrapper['odds_data']  # Use cached odds
                event_name = event.get('name', 'Unknown')
                market_id = event.get('market_id', '')
                
                # Add visual indicator for odds availability
                odds_icon = "✅" if has_odds else "⏳"
                st.markdown(f"##### {odds_icon} {event_name}")
                
                if has_odds and odds_data and odds_data.get('runners'):
                    runners = odds_data['runners']
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
                            st.markdown(f'''
                            <div style="background: rgba(30,30,50,0.8); border-radius: 10px; padding: 10px; text-align: center;">
                                <div style="color: #e2e8f0; font-weight: bold; margin-bottom: 8px;">{name[:18]}</div>
                                <div style="display: flex; justify-content: center; gap: 8px;">
                                    <div style="background: rgba(72, 187, 120, 0.3); border-radius: 6px; padding: 6px 12px;">
                                        <div style="color: #48bb78; font-weight: bold;">{bp}</div>
                                        <div style="color: #68d391; font-size: 0.7rem;">{format_stake(bs)}</div>
                                    </div>
                                    <div style="background: rgba(245, 101, 101, 0.3); border-radius: 6px; padding: 6px 12px;">
                                        <div style="color: #f56565; font-weight: bold;">{lp}</div>
                                        <div style="color: #fc8181; font-size: 0.7rem;">{format_stake(ls)}</div>
                                    </div>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)
                elif not has_odds:
                    st.caption("⏳ Odds not available yet")
                else:
                    st.caption("⏳ Odds loading...")
                st.markdown("---")

st.caption("Advanced Market Load Tracker • Built for live analysis")
