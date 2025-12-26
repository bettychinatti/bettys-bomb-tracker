"""
Advanced Market Load Tracker - Modern Dynamic Dashboard
"""
import streamlit as st
import requests
import time
from datetime import datetime
from token_manager import get_valid_token

st.set_page_config(
    page_title="Advanced Market Load Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Dark Theme CSS
st.markdown("""
<style>
    /* Dark theme base */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Main container */
    .block-container {
        padding: 1rem 2rem;
        max-width: 1400px;
    }
    
    /* Header styling */
    .main-title {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #a0aec0;
        text-align: center;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Sport cards */
    .sport-card {
        background: linear-gradient(145deg, #1e1e2f 0%, #2d2d44 100%);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 16px;
        padding: 1rem;
        text-align: center;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .sport-card:hover {
        transform: translateY(-4px);
        border-color: #667eea;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    .sport-card.active {
        background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
        border-color: transparent;
    }
    .sport-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .sport-name {
        color: #e2e8f0;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Event cards */
    .event-card {
        background: linear-gradient(145deg, #1a1a2e 0%, #252542 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.3s ease;
    }
    .event-card:hover {
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .event-name {
        color: #f7fafc;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .live-dot {
        width: 8px;
        height: 8px;
        background: #ef4444;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    /* Odds display */
    .odds-container {
        display: flex;
        gap: 1rem;
        margin-top: 1rem;
    }
    .runner-card {
        flex: 1;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 1rem;
    }
    .runner-name {
        color: #cbd5e0;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
        text-align: center;
    }
    .odds-row {
        display: flex;
        gap: 8px;
    }
    .back-box {
        flex: 1;
        background: linear-gradient(145deg, #1e40af 0%, #3b82f6 100%);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .lay-box {
        flex: 1;
        background: linear-gradient(145deg, #9f1239 0%, #e11d48 100%);
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .odds-label {
        color: rgba(255,255,255,0.7);
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .odds-price {
        color: #ffffff;
        font-size: 1.4rem;
        font-weight: 700;
    }
    .odds-stake {
        color: rgba(255,255,255,0.6);
        font-size: 0.7rem;
        margin-top: 2px;
    }
    
    /* Stats panel */
    .stats-panel {
        background: linear-gradient(145deg, #1a1a2e 0%, #252542 100%);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
    }
    .stats-title {
        color: #a78bfa;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .stat-item {
        background: rgba(255,255,255,0.03);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
    }
    .stat-value {
        color: #f7fafc;
        font-size: 2rem;
        font-weight: 700;
    }
    .stat-label {
        color: #a0aec0;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(145deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .stButton > button[kind="secondary"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Text colors */
    h1, h2, h3, p, span, label {
        color: #e2e8f0 !important;
    }
    .stMarkdown {
        color: #e2e8f0;
    }
    
    /* Metric styling */
    div[data-testid="stMetric"] {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        padding: 1rem;
    }
    div[data-testid="stMetric"] label {
        color: #a0aec0 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f7fafc !important;
        font-size: 1.8rem !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.03) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
    }
    .streamlit-expanderContent {
        background: rgba(255,255,255,0.02) !important;
        border-radius: 0 0 12px 12px !important;
    }
    
    /* Checkbox */
    .stCheckbox label span {
        color: #a0aec0 !important;
    }
    
    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.1) !important;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Info box */
    .stAlert {
        background: rgba(59, 130, 246, 0.1) !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
    }
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
    """Fetch live events for a sport using GET request."""
    try:
        url = f"https://api.d99exch.com/api/guest/event_list?sport_id={sport_id}"
        headers = {
            "accept": "application/json, text/plain, */*",
            "origin": "https://d99exch.com",
            "referer": "https://d99exch.com/",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            events = data.get("data", {}).get("events", [])
            # Filter to only in-play events
            return [e for e in events if e.get("in_play") == 1]
        return []
    except Exception as e:
        st.error(f"API Error: {e}")
        return []


def fetch_odds(event_id, market_id):
    """Fetch real-time odds using form-urlencoded POST request."""
    try:
        url = "https://odds.o99exch.com/ws/getMarketDataNew"
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://99exch.com",
            "referer": "https://99exch.com/",
        }
        data = f"market_ids[]={market_id}"
        resp = requests.post(url, data=data, headers=headers, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result and result[0]:
                return parse_odds_string(result[0])
        return None
    except:
        return None


def parse_odds_string(odds_str):
    """Parse pipe-delimited odds string into structured data."""
    try:
        parts = odds_str.split('|')
        runners = []
        i = 0
        runner_idx = 0
        
        while i < len(parts):
            if parts[i] == 'ACTIVE':
                # Found a runner - read next 12 values (6 back + 6 lay as price/size pairs)
                back_prices = []
                lay_prices = []
                
                j = i + 1
                # Read 3 back prices
                for _ in range(3):
                    if j + 1 < len(parts):
                        try:
                            price = float(parts[j])
                            size = float(parts[j + 1])
                            back_prices.append({"price": price, "size": size})
                        except:
                            pass
                        j += 2
                
                # Read 3 lay prices
                for _ in range(3):
                    if j + 1 < len(parts):
                        try:
                            price = float(parts[j])
                            size = float(parts[j + 1])
                            lay_prices.append({"price": price, "size": size})
                        except:
                            pass
                        j += 2
                
                runner_idx += 1
                runners.append({
                    "name": f"Team {runner_idx}",
                    "back": back_prices,
                    "lay": lay_prices
                })
                i = j
            else:
                i += 1
        
        return {"runners": runners} if runners else None
    except:
        return None


def format_stake(val):
    if val >= 100000:
        return f"₹{val/100000:.1f}L"
    elif val >= 1000:
        return f"₹{val/1000:.1f}K"
    return f"₹{val:.0f}"


# Header
st.markdown('<div class="main-title">📊 Advanced Market Load Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-time odds monitoring & market analysis</div>', unsafe_allow_html=True)

# Initialize state
if 'sport' not in st.session_state:
    st.session_state.sport = 4

# Sport Selection
st.markdown("### 🎯 Select Sport")
sport_cols = st.columns(len(SPORTS))
for i, sport in enumerate(SPORTS):
    with sport_cols[i]:
        is_active = st.session_state.sport == sport['id']
        if st.button(
            f"{sport['icon']} {sport['name']}", 
            key=f"sport_{sport['id']}",
            use_container_width=True,
            type="primary" if is_active else "secondary"
        ):
            st.session_state.sport = sport['id']
            st.rerun()

st.markdown("---")

# Get current sport info
sport_id = st.session_state.sport
sport_name = next((s['name'] for s in SPORTS if s['id'] == sport_id), "Cricket")
sport_icon = next((s['icon'] for s in SPORTS if s['id'] == sport_id), "🏏")

# Main Layout
main_col, stats_col = st.columns([3, 1])

# Stats Panel (Right)
with stats_col:
    st.markdown("""
    <div class="stats-panel">
        <div class="stats-title">📈 Dashboard Stats</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    # Auto refresh
    auto_refresh = st.checkbox("⚡ Auto-refresh (30s)")
    
    # Current time
    st.markdown(f"""
    <div class="stat-item">
        <div class="stat-label">Last Updated</div>
        <div style="color: #a78bfa; font-size: 1.2rem; font-weight: 600;">
            {datetime.now().strftime('%H:%M:%S')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Selected sport
    st.markdown(f"""
    <div class="stat-item">
        <div style="font-size: 2rem;">{sport_icon}</div>
        <div class="stat-label">Current Sport</div>
        <div style="color: #f7fafc; font-weight: 600;">{sport_name}</div>
    </div>
    """, unsafe_allow_html=True)

# Events Panel (Left)
with main_col:
    st.markdown(f"### {sport_icon} Live {sport_name} Events")
    
    # Fetch events
    with st.spinner("Loading events..."):
        events = fetch_events(sport_id)
    
    if not events:
        st.markdown("""
        <div class="event-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🏟️</div>
            <div style="color: #a0aec0; font-size: 1.1rem;">No live events right now</div>
            <div style="color: #718096; font-size: 0.9rem; margin-top: 0.5rem;">Check back later or select another sport</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Event count metric
        st.metric("🔴 Live Events", len(events))
        
        # Group events by competition
        competitions = {}
        for event in events:
            comp = event.get('competition_name', 'Other')
            if comp not in competitions:
                competitions[comp] = []
            competitions[comp].append(event)
        
        # Display by competition
        for comp_name, comp_events in competitions.items():
            st.markdown(f"""
            <div style="background: rgba(102, 126, 234, 0.1); padding: 8px 16px; border-radius: 8px; margin: 16px 0 8px 0;">
                <span style="color: #a78bfa; font-weight: 600;">🏆 {comp_name}</span>
                <span style="color: #718096; font-size: 0.85rem; margin-left: 8px;">({len(comp_events)} events)</span>
            </div>
            """, unsafe_allow_html=True)
            
            for event in comp_events[:8]:  # Max 8 events per competition
                event_name = event.get('name', 'Unknown Event')
                event_id = event.get('event_id', '')
                market_id = event.get('market_id', '')
                
                # Event card using expander
                with st.expander(f"🔴 {event_name}", expanded=False):
                    if market_id:
                        odds_data = fetch_odds(event_id, market_id)
                        
                        if odds_data and 'runners' in odds_data:
                            runners = odds_data['runners']
                            runner_cols = st.columns(len(runners))
                            
                            for idx, runner in enumerate(runners):
                                with runner_cols[idx]:
                                    runner_name = runner.get('name', f'Team {idx+1}')
                                    back_prices = runner.get('back', [{}])
                                    lay_prices = runner.get('lay', [{}])
                                    
                                    back_price = back_prices[0].get('price', '-') if back_prices else '-'
                                    back_size = back_prices[0].get('size', 0) if back_prices else 0
                                    lay_price = lay_prices[0].get('price', '-') if lay_prices else '-'
                                    lay_size = lay_prices[0].get('size', 0) if lay_prices else 0
                                    
                                    # Runner card HTML
                                    st.markdown(f"""
                                    <div class="runner-card">
                                        <div class="runner-name">{runner_name[:25]}</div>
                                        <div class="odds-row">
                                            <div class="back-box">
                                                <div class="odds-label">Back</div>
                                                <div class="odds-price">{back_price}</div>
                                                <div class="odds-stake">{format_stake(back_size)}</div>
                                            </div>
                                            <div class="lay-box">
                                                <div class="odds-label">Lay</div>
                                                <div class="odds-price">{lay_price}</div>
                                                <div class="odds-stake">{format_stake(lay_size)}</div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="text-align: center; padding: 1rem; color: #718096;">
                                ⏳ Loading odds data...
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div style="text-align: center; padding: 1rem; color: #718096;">
                            📊 No market data available
                        </div>
                        """, unsafe_allow_html=True)

# Auto refresh logic
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <span style="color: #4a5568; font-size: 0.8rem;">
        Advanced Market Load Tracker • Built for real-time analysis
    </span>
</div>
""", unsafe_allow_html=True)
