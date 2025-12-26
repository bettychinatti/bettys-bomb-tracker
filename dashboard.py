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

def calculate_market_load(runners):
    """Calculate total bets and P/L for each runner"""
    market_load = []
    
    for runner in runners:
        name = runner.get('name', 'Unknown')
        back_prices = runner.get('back', [])
        lay_prices = runner.get('lay', [])
        
        # Calculate total back stakes (money on this team to win)
        total_back = sum(b.get('size', 0) for b in back_prices)
        
        # Calculate total lay stakes (money against this team)
        total_lay = sum(l.get('size', 0) for l in lay_prices)
        
        # Total bet on this runner
        total_bet = total_back + total_lay
        
        # P/L if this runner wins (simplified calculation)
        # If runner wins: you get back stakes but lose lay stakes
        best_back_price = back_prices[0].get('price', 1) if back_prices else 1
        pl_if_win = (total_back * (best_back_price - 1)) - total_lay
        
        market_load.append({
            'name': name,
            'total_bet': total_bet,
            'pl_if_win': pl_if_win,
            'percentage': 0  # Will calculate after we have all totals
        })
    
    # Calculate percentages
    total_all_bets = sum(m['total_bet'] for m in market_load)
    if total_all_bets > 0:
        for m in market_load:
            m['percentage'] = (m['total_bet'] / total_all_bets) * 100
    
    return market_load

def quick_check_odds_available(market_id):
    """Quick check if odds are available without full parsing"""
    try:
        url = "https://odds.o99exch.com/ws/getMarketDataNew"
        headers = {"content-type": "application/x-www-form-urlencoded", "origin": "https://99exch.com"}
        resp = requests.post(url, data=f"market_ids[]={market_id}", headers=headers, timeout=3)
        if resp.status_code == 200:
            result = resp.json()
            # Just check if we got data, don't parse it
            return bool(result and result[0] and 'ACTIVE' in str(result[0]))
        return False
    except:
        return False

def sort_events_by_odds_availability(events):
    """Sort events - prioritize those with available odds"""
    events_with_status = []
    
    for event in events:
        market_id = event.get('market_id', '')
        has_odds = False
        odds_data = None
        
        if market_id:
            # Fetch odds to check availability (will be cached)
            odds_data = fetch_odds(market_id, event.get('name', ''))
            if odds_data and odds_data.get('runners'):
                has_odds = True
        
        events_with_status.append({
            'event': event,
            'market_id': market_id,
            'has_odds': has_odds,
            'odds_data': odds_data  # Cache for later use
        })
    
    # Sort by odds availability (True before False)
    events_with_status.sort(key=lambda x: x['has_odds'], reverse=True)
    
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
    
    # Show loading spinner while fetching events and sorting by odds
    with st.spinner('🔄 Loading & sorting matches...'):
        events = fetch_events_by_sport(sport_id)
        
        if events:
            # Sort by odds availability (matches with odds first)
            sorted_events = sort_events_by_odds_availability(events)
        else:
            sorted_events = []
    
    if not sorted_events:
        st.info(f"No live {sport_info['name']} matches right now. Try another sport!")
    else:
        st.metric("🔴 Live Matches", len(sorted_events))
        
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
                event_name = event.get('name', 'Unknown')
                market_id = event_wrapper['market_id']
                has_odds = event_wrapper['has_odds']
                cached_odds = event_wrapper['odds_data']
                
                # Add visual indicator for odds availability
                odds_icon = "✅" if has_odds else "⏳"
                st.markdown(f"##### {odds_icon} {event_name}")
                
                if has_odds and cached_odds:
                    # Use cached odds data (already fetched during sorting)
                    runners = cached_odds['runners']
                    
                    # Calculate market load
                    market_load = calculate_market_load(runners)
                    
                    # Display Market Load Bar (only for 2-runner markets)
                    if len(market_load) == 2:
                        team1 = market_load[0]
                        team2 = market_load[1]
                        
                        st.markdown(f"""
                        <div style="background: rgba(30,30,50,0.9); border-radius: 10px; padding: 15px; margin: 10px 0;">
                            <div style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px; text-align: center;">Match Load</div>
                            <div style="display: flex; height: 25px; border-radius: 8px; overflow: hidden; margin-bottom: 8px;">
                                <div style="background: #ef4444; width: {team1['percentage']:.1f}%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: white; font-weight: bold;">
                                    {team1['percentage']:.1f}%
                                </div>
                                <div style="background: #10b981; width: {team2['percentage']:.1f}%; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; color: white; font-weight: bold;">
                                    {team2['percentage']:.1f}%
                                </div>
                            </div>
                            <div style="display: flex; justify-content: space-between; color: #94a3b8; font-size: 0.75rem;">
                                <span>{team1['name'][:20]}: {team1['percentage']:.1f}%</span>
                                <span>{team2['name'][:20]}: {team2['percentage']:.1f}%</span>
                            </div>
                            <div style="color: #3b82f6; font-size: 0.75rem; text-align: center; margin-top: 5px;">
                                Match Load on <span style="color: #60a5fa;">{team1['name'] if team1['percentage'] > team2['percentage'] else team2['name']}</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Display team stats with Total Bet and P/L
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
                            
                            # Get market load data for this runner
                            load_data = market_load[idx] if idx < len(market_load) else None
                            total_bet_display = format_stake(load_data['total_bet']) if load_data else "N/A"
                            pl_display = format_stake(load_data['pl_if_win']) if load_data else "N/A"
                            pl_color = "#10b981" if load_data and load_data['pl_if_win'] > 0 else "#ef4444"
                            
                            st.markdown(f'''
                            <div style="background: rgba(30,30,50,0.8); border-radius: 10px; padding: 12px; text-align: center;">
                                <div style="color: #e2e8f0; font-weight: bold; margin-bottom: 8px; font-size: 0.95rem;">{name[:18]}</div>
                                
                                <!-- Odds Display -->
                                <div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 12px;">
                                    <div style="background: rgba(72, 187, 120, 0.3); border-radius: 6px; padding: 6px 12px;">
                                        <div style="color: #48bb78; font-weight: bold;">{bp}</div>
                                        <div style="color: #68d391; font-size: 0.7rem;">{format_stake(bs)}</div>
                                    </div>
                                    <div style="background: rgba(245, 101, 101, 0.3); border-radius: 6px; padding: 6px 12px;">
                                        <div style="color: #f56565; font-weight: bold;">{lp}</div>
                                        <div style="color: #fc8181; font-size: 0.7rem;">{format_stake(ls)}</div>
                                    </div>
                                </div>
                                
                                <!-- Market Load Stats -->
                                <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                                    <div style="background: rgba(59, 130, 246, 0.15); border-radius: 6px; padding: 8px; margin-bottom: 6px;">
                                        <div style="color: #94a3b8; font-size: 0.65rem;">Total Bet</div>
                                        <div style="color: #3b82f6; font-weight: bold; font-size: 0.95rem;">{total_bet_display}</div>
                                    </div>
                                    <div style="background: rgba(239, 68, 68, 0.15); border-radius: 6px; padding: 8px;">
                                        <div style="color: #94a3b8; font-size: 0.65rem;">P/L if Win</div>
                                        <div style="color: {pl_color}; font-weight: bold; font-size: 0.95rem;">{pl_display}</div>
                                    </div>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)
                else:
                    st.caption("⏳ Odds not available")
                st.markdown("---")

st.caption("Advanced Market Load Tracker • Built for live analysis")
