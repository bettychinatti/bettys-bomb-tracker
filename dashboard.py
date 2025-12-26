import streamlit as st
import requests
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Tuple
from persistence import get_conn, get_cumulative
from token_manager import get_valid_token

# Fast, precise, and clean dashboard mirroring the terminal tracker

# Use India Standard Time across the app
IST = ZoneInfo("Asia/Kolkata")

# Health check endpoint for keep-alive monitoring
# Access with ?health=true to get simple status response
query_params = st.query_params
if query_params.get("health") == "true":
    st.write("✅ HEALTHY")
    st.write(f"Timestamp: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    st.write("Status: Running")
    st.stop()

# Use authenticated client endpoints (not guest endpoints)
EVENTS_API = "https://api.d99exch.com/api/client/event_list"
MARKET_API = "https://odds.o99exch.com/ws/getMarketDataNew"

# Bearer token for API authentication
# AUTO-REFRESH: Set EXCH_USERNAME and EXCH_PASSWORD env vars for automatic token refresh
# MANUAL: Update this token from browser every ~5 hours if not using auto-refresh
BEARER_TOKEN_FALLBACK = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5kOTlleGNoLmNvbS9hcGkvYXV0aCIsImlhdCI6MTc2Njc0NTQ2NywiZXhwIjoxNzY2NzYzNDY3LCJuYmYiOjE3NjY3NDU0NjcsImp0aSI6IlRNd1IwTjNwQVRQcFVIWkkiLCJzdWIiOiI5ODcyOTQiLCJwcnYiOiI4N2UwYWYxZWY5ZmQxNTgxMmZkZWM5NzE1M2ExNGUwYjA0NzU0NmFhIn0.XE3AIrm60v-No5wuNmSwDBGHZgNSYUk5S4C4kGJYd7U"

# Get valid token (auto-refreshes if credentials provided, otherwise uses fallback)
BEARER_TOKEN = get_valid_token(fallback_token=BEARER_TOKEN_FALLBACK)

# Enhanced headers matching real browser requests
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Authorization": f"bearer {BEARER_TOKEN}",  # Authentication required
    "Origin": "https://99exch.com",
    "Referer": "https://99exch.com/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "priority": "u=1, i",
}

SPORT_MAP = {1: "Soccer", 2: "Tennis", 4: "Cricket"}

# Events cache interval (seconds) to minimize API calls
EVENTS_REFRESH_INTERVAL_S = 30 * 60  # 30 minutes


def fetch_events() -> List[Dict[str, Any]]:
    resp = requests.get(EVENTS_API, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    events = (data or {}).get('data', {}).get('events', [])
    return events


def get_events_cached(force: bool = False) -> Tuple[List[Dict[str, Any]], Optional[str], float]:
    """
    Returns (events, error_message, last_fetch_epoch).
    Respects a 30-minute refresh interval unless force=True.
    """
    if 'events_cache' not in st.session_state:
        st.session_state['events_cache'] = {
            'events': [], 'last_fetch_epoch': 0.0, 'error': None
        }
    cache = st.session_state['events_cache']
    now_epoch = time.time()
    should_refresh = force or (now_epoch - cache['last_fetch_epoch'] > EVENTS_REFRESH_INTERVAL_S) or (not cache['events'] and cache['error'] is not None)
    if should_refresh:
        try:
            evs = fetch_events()
            cache['events'] = evs
            cache['error'] = None
            cache['last_fetch_epoch'] = now_epoch
        except Exception as e:
            cache['error'] = str(e)
            cache['last_fetch_epoch'] = now_epoch
    return cache['events'], cache['error'], cache['last_fetch_epoch']


def market_ids_payload(ids: List[str]) -> List[Tuple[str, str]]:
    return [("market_ids[]", str(mid)) for mid in ids]


def fetch_market_strings(market_ids: List[str]) -> List[str]:
    if not market_ids:
        return []
    resp = requests.post(MARKET_API, headers=HEADERS, data=market_ids_payload(market_ids), timeout=10)
    resp.raise_for_status()
    out = resp.json()
    return out if isinstance(out, list) else []


def parse_market_string(market_str: str) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    f = market_str.split('|')
    mid = f[0]
    total_matched: Optional[float] = None
    if len(f) > 5:
        try:
            total_matched = float(f[5])
        except Exception:
            total_matched = None
    runners: List[Dict[str, Any]] = []
    i = 0
    while i < len(f):
        if f[i] == 'ACTIVE':
            sel_id = f[i-1] if i-1 >= 0 else None
            i += 1
            pairs: List[Tuple[float, float]] = []
            read = 0
            while i + 1 < len(f) and read < 12:
                try:
                    odd = float(f[i]); amt = float(f[i+1])
                    pairs.append((odd, amt))
                    i += 2; read += 2
                except Exception:
                    break
            back_pairs = pairs[:3]
            lay_pairs = pairs[3:6]
            runners.append({"selection_id": sel_id, "back": back_pairs, "lay": lay_pairs})
        else:
            i += 1
    return mid, {"total_matched": total_matched}, runners


def team_labels(name: str) -> List[str]:
    if not name:
        return ["Team 1", "Team 2"]
    for sep in [' v ', ' vs ', ' VS ', ' Vs ', ' V ']:
        if sep in name:
            parts = [p.strip() for p in name.split(sep) if p.strip()]
            if len(parts) >= 2:
                return [parts[0], parts[1]]
    return [name.strip(), '']


def summarize_runner(r: Dict[str, Any]) -> Dict[str, Any]:
    back = r.get('back', [])
    lay = r.get('lay', [])
    total_back = float(sum(a for _, a in back))
    total_lay = float(sum(a for _, a in lay))
    best_back = back[0][0] if back else None
    best_lay = lay[0][0] if lay else None
    return {
        "total_back": total_back,
        "total_lay": total_lay,
        "best_back": best_back,
        "best_lay": best_lay,
        "back_top3": back[:3],
        "lay_top3": lay[:3],
    }


def ensure_state():
    if 'prev' not in st.session_state:
        st.session_state['prev'] = {}
    if 'session' not in st.session_state:
        st.session_state['session'] = {}
    if 'labels' not in st.session_state:
        st.session_state['labels'] = {}


def update_cumulative(mid: str, label: str, db: Optional[float], dl: Optional[float]):
    sess = st.session_state['session']
    if mid not in sess:
        sess[mid] = {}
    if label not in sess[mid]:
        sess[mid][label] = {'in_back':0.0,'in_lay':0.0,'out_back':0.0,'out_lay':0.0,'net_back':0.0,'net_lay':0.0}
    s = sess[mid][label]
    if db is not None:
        if db > 0: s['in_back'] += db
        elif db < 0: s['out_back'] += (-db)
        s['net_back'] += db
    if dl is not None:
        if dl > 0: s['in_lay'] += dl
        elif dl < 0: s['out_lay'] += (-dl)
        s['net_lay'] += dl


def render_team_card(col, label: str, summ: Dict[str, Any], prev_s: Dict[str, Any], sess_s: Dict[str, Any]):
    tb = summ['total_back']; tl = summ['total_lay']
    bb = '-' if summ['best_back'] is None else f"{summ['best_back']:.2f}"
    bl = '-' if summ['best_lay'] is None else f"{summ['best_lay']:.2f}"
    db = None if 'total_back' not in prev_s else tb - prev_s['total_back']
    dl = None if 'total_lay' not in prev_s else tl - prev_s['total_lay']
    dbb = None if 'best_back' not in prev_s or summ['best_back'] is None else (summ['best_back'] - prev_s['best_back'])
    dbl = None if 'best_lay' not in prev_s or summ['best_lay'] is None else (summ['best_lay'] - prev_s['best_lay'])

    with col.container():
        # Minimal card header
        col.markdown(f"### {label}")
        col.markdown("---")
        
        # Metrics in clean grid
        c1, c2 = col.columns(2)
        with c1:
            st.metric("BACK Total", f"₹{tb:,.2f}", None if db is None else f"{db:+.2f}")
        with c2:
            st.metric("LAY Total", f"₹{tl:,.2f}", None if dl is None else f"{dl:+.2f}")
        
        c3, c4 = col.columns(2)
        with c3:
            st.metric("Best BACK", bb, None if dbb is None else f"{dbb:+.2f}")
        with c4:
            st.metric("Best LAY", bl, None if dbl is None else f"{dbl:+.2f}")
        
        # Top 3 odds
        col.markdown("")  # Spacing
        back3 = ", ".join([f"{o:.2f}@₹{a:.0f}" for o,a in summ['back_top3']]) or 'No data'
        lay3 = ", ".join([f"{o:.2f}@₹{a:.0f}" for o,a in summ['lay_top3']]) or 'No data'
        col.caption(f"**BACK top 3:** {back3}")
        col.caption(f"**LAY top 3:** {lay3}")
        
        # Session cumulative (minimal display)
        inflow = sess_s.get('in_back',0.0) + sess_s.get('in_lay',0.0)
        outflow = sess_s.get('out_back',0.0) + sess_s.get('out_lay',0.0)
        net = sess_s.get('net_back',0.0) + sess_s.get('net_lay',0.0)
        
        # Color-coded net
        net_color = "#16a34a" if net > 0 else "#dc2626" if net < 0 else "#6b7280"
        col.markdown(f"""
        <div style='margin-top: 1rem; padding: 0.75rem; background: #F9FAFB; border-radius: 6px; border-left: 3px solid {net_color};'>
            <div style='font-size: 0.85rem; color: #6b7280;'>Session Flow</div>
            <div style='font-size: 0.9rem; color: #404040; margin-top: 0.25rem;'>
                <span style='color: #16a34a;'>+₹{inflow:,.0f}</span> staked · 
                <span style='color: #dc2626;'>-₹{outflow:,.0f}</span> withdrawn · 
                <span style='color: {net_color}; font-weight: 500;'>₹{net:+,.0f}</span> net
            </div>
        </div>
        """, unsafe_allow_html=True)


def main():
    # Minimal light theme configuration
    st.set_page_config(
        page_title="Advanced Market Load Tracker",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for minimal light theme
    st.markdown("""
    <style>
        /* Light minimal theme */
        .stApp {
            background-color: #FAFAFA;
        }
        
        /* Clean header */
        h1 {
            font-weight: 300;
            letter-spacing: -0.5px;
            color: #1a1a1a;
            font-size: 2rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        h3 {
            font-weight: 400;
            color: #404040;
            font-size: 1.1rem !important;
        }
        
        /* Minimal cards */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            background: white;
            border: 1px solid #E8E8E8;
            border-radius: 8px;
            padding: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        
        /* Metrics styling */
        [data-testid="stMetricValue"] {
            font-size: 1.4rem;
            font-weight: 500;
            color: #1a1a1a;
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 0.9rem;
        }
        
        /* Positive/negative colors */
        [data-testid="stMetricDelta"] svg {
            display: none;
        }
        
        /* Buttons minimal */
        .stButton button {
            background: white;
            border: 1px solid #D0D0D0;
            border-radius: 6px;
            color: #404040;
            font-weight: 400;
            padding: 0.4rem 1rem;
            transition: all 0.15s;
        }
        
        .stButton button:hover {
            border-color: #1a1a1a;
            background: #F5F5F5;
        }
        
        /* Sidebar minimal */
        [data-testid="stSidebar"] {
            background: #FFFFFF;
            border-right: 1px solid #E8E8E8;
        }
        
        /* Caption text */
        .stCaptionContainer {
            color: #707070;
            font-size: 0.85rem;
        }
        
        /* Divider */
        hr {
            border-color: #E8E8E8;
            margin: 1.5rem 0;
        }
        
        /* Selectbox/inputs */
        .stSelectbox, .stSlider {
            background: white;
        }
        
        /* Remove default padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# Advanced Market Load Tracker")
        st.caption("Real-time money flow analysis · Accurate delta tracking")
    with col2:
        now_ist = datetime.now(IST).strftime('%H:%M:%S IST')
        st.metric("", now_ist, label_visibility="collapsed")
    
    st.divider()
    
    ensure_state()

    # Minimal controls in expander
    with st.expander("⚙️ Settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            refresh_ms = st.slider("Update interval (ms)", 500, 3000, 1000, step=250)
        with col2:
            track_scope = st.radio("Scope", ["Selected sport", "All sports"], index=0, horizontal=True)
        with col3:
            manual_mode = st.checkbox("Manual mode", help="Enter Market IDs manually")
    
    # Fetch events with cache
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("📡 Live data feed active")
    with col2:
        do_refresh = st.button("↻ Refresh", use_container_width=True)
    with col3:
        do_clear = st.button("✕ Clear", help="Clear cache", use_container_width=True)
    
    if do_clear:
        st.session_state['events_cache'] = {'events': [], 'last_fetch_epoch': 0.0, 'error': None}
    
    events, events_error, last_fetch_epoch = get_events_cached(force=(do_refresh or do_clear))
    count = len(events) if isinstance(events, list) else 0
    
    if events_error:
        st.warning(f"⚠️ Events API unavailable. Switch to Manual mode. Error: {events_error}")
    
    if last_fetch_epoch:
        last_fetch_str = datetime.fromtimestamp(last_fetch_epoch, IST).strftime('%H:%M:%S')
        st.caption(f"Last updated: {last_fetch_str} · {count} events · Auto-refresh every 30 min")

    def sport_of(ev: Dict[str, Any]) -> str:
        etid_val = ev.get('event_type_id')
        etid: Optional[int] = None
        if etid_val is not None:
            try:
                etid = int(etid_val)
            except Exception:
                etid = None
        return SPORT_MAP.get(etid, 'Other') if isinstance(etid, int) else 'Other'

    def is_in_play(ev: Dict[str, Any]) -> bool:
        # Prioritize explicit live/in-play status across multiple possible fields/encodings
        candidates = [
            ev.get('in_play'), ev.get('inplay'), ev.get('inPlay'), ev.get('is_inplay'),
            ev.get('status'), ev.get('status_name'), ev.get('event_status'), ev.get('state'),
        ]
        for v in candidates:
            if v is None:
                continue
            # Numeric/boolean truthy
            if v is True or v == 1 or (isinstance(v, str) and v.strip() == '1'):
                return True
            if isinstance(v, str):
                s = v.strip().lower()
                if s in {
                    'true', 'yes', 'y', 'on', 'live', 'inplay', 'in-play', 'in play',
                    'running', 'started', 'active', 'playing'
                }:
                    return True
        return False

    # Sports list (used when not in manual mode)
    sports_present = sorted({sport_of(ev) for ev in events})
    sports_present = [s for s in sports_present if s != 'Other'] or ['Cricket', 'Tennis', 'Soccer']
    
    # Sport selector
    st.divider()
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_sport = st.selectbox("Sport", options=sports_present, label_visibility="collapsed")
    with col2:
        st.caption(f"Showing {selected_sport} markets")

    # Partition events
    # Current time in IST
    now = datetime.now(IST)
    def parse_time(s: Optional[str]) -> Optional[datetime]:
        if not s:
            return None
        try:
            # Normalize 'Z' to '+00:00' and parse
            dt = datetime.fromisoformat(s.strip().replace('Z', '+00:00'))
        except Exception:
            return None
        # Ensure timezone-aware (assume UTC if missing)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def event_label(ev: Dict[str, Any]) -> str:
        return ev.get('event_name') or ev.get('name') or f"Event {ev.get('event_id')}"

    # Choose which events to track this tick (or switch to manual inputs)
    started_by_time: List[Dict[str, Any]] = []  # time-based fallback list
    if manual_mode:
        st.subheader("Manual Input Mode")
        col1, col2 = st.columns(2)
        with col1:
            markets_text = st.text_input("Market IDs (comma-separated)", value="")
        with col2:
            match_label = st.text_input("Match label", value="", placeholder="e.g., Team A vs Team B")
        
        # Derive team labels from the match label if present
        t1, t2 = team_labels(match_label)
        if not match_label:
            st.info("💡 Enter a match label to name the team cards")
        # Build synthetic in-play events for the specified market IDs
        manual_market_ids = [m.strip() for m in markets_text.split(',') if m.strip()]
        filtered = []
        inplay = [{
            'market_id': mid,
            'event_name': match_label or f"Market {mid}",
            'in_play': 1,
        } for mid in manual_market_ids]
        upcoming = []
    else:
        filtered = events if track_scope == "All sports" else [ev for ev in events if sport_of(ev) == selected_sport]
        inplay = [ev for ev in filtered if is_in_play(ev)]
        upcoming = [ev for ev in filtered if not is_in_play(ev)]

        # Time-based start trigger (secondary): include markets in polling and (optionally) display as fallback
        def has_started_by_time(ev: Dict[str, Any]) -> bool:
            start = parse_time(ev.get('open_date'))
            if not start:
                return False
            # Assume UTC if missing tzinfo; compare aware datetimes (now is IST)
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            return now >= start

        started_by_time = [ev for ev in upcoming if has_started_by_time(ev)]

    # Quick navigation sidebar removed - now inline
    if 'focus_mid' not in st.session_state:
        st.session_state['focus_mid'] = None
        for ev in upcoming[:10]:
            start = parse_time(ev.get('open_date'))
            start_str = start.astimezone(IST).strftime('%H:%M') if start else '-'
            mid = str(ev.get('market_id'))
            label = event_label(ev)
            if st.sidebar.button(f"⏰ {label} at {start_str}", key=f"goto_s_{mid}"):
                st.session_state['focus_mid'] = mid
                if hasattr(st, 'rerun'):
                    st.rerun()
        # Secondary time-based section for quick navigation
        if started_by_time:
            st.sidebar.subheader("Time-started (fallback)")
            for ev in started_by_time[:10]:
                start = parse_time(ev.get('open_date'))
                start_str = start.astimezone(IST).strftime('%H:%M') if start else '-'
                mid = str(ev.get('market_id'))
                label = event_label(ev)
                if st.sidebar.button(f"⏱ {label} since {start_str}", key=f"goto_t_{mid}"):
                    st.session_state['focus_mid'] = mid
                    if hasattr(st, 'rerun'):
                        st.rerun()
    # Focus controls
    focus_only = st.sidebar.checkbox("Show only selected match", value=False)
    if st.sidebar.button("Clear selection"):
        st.session_state['focus_mid'] = None
        if hasattr(st, 'rerun'):
            st.rerun()

    # Determine markets to poll
    market_ids_set = set([str(ev.get('market_id')) for ev in inplay if ev.get('market_id')])
    # Also poll events that have reached their scheduled start time (time-based fallback)
    if not manual_mode:
        for ev in started_by_time:
            if ev.get('market_id'):
                market_ids_set.add(str(ev.get('market_id')))
    market_ids = list(market_ids_set)

    # Initialize seen_inplay tracking to reset cumulatives exactly when match starts (in_play or time-based)
    if 'seen_inplay' not in st.session_state:
        st.session_state['seen_inplay'] = {}
    for ev in inplay:
        mid = str(ev.get('market_id'))
        if mid and not st.session_state['seen_inplay'].get(mid):
            # Reset cumulative session for this market at the moment it enters in-play
            if 'session' in st.session_state and mid in st.session_state['session']:
                st.session_state['session'][mid] = {}
            st.session_state['seen_inplay'][mid] = True

    # Prefetch labels (in-play + time-based fallback)
    for ev in inplay:
        mid = str(ev.get('market_id'))
        if mid and mid not in st.session_state['labels']:
            # In manual mode, derive from the provided match label; else from event
            st.session_state['labels'][mid] = team_labels(event_label(ev))
    if not manual_mode:
        for ev in started_by_time:
            mid = str(ev.get('market_id'))
            if mid and mid not in st.session_state['labels']:
                st.session_state['labels'][mid] = team_labels(event_label(ev))

    # Poll all markets in one shot
    raw_strings: List[str] = []
    if market_ids:
        try:
            raw_strings = fetch_market_strings(market_ids)
        except Exception as e:
            st.error(f"Error fetching market data: {e}")
            raw_strings = []

    # Index by market_id
    by_mid: Dict[str, str] = {}
    for s in raw_strings:
        if isinstance(s, str):
            mid = s.split('|', 1)[0]
            by_mid[mid] = s

    # Combine true in-play with time-based fallback (secondary)
    time_based_ids = set()
    if not manual_mode:
        time_based_ids = {str(ev.get('market_id')) for ev in started_by_time if ev.get('market_id')}
    inplay_display = list(inplay)
    if not manual_mode:
        # Append time-based only if not already in in-play
        inplay_display += [ev for ev in started_by_time if str(ev.get('market_id')) not in {str(e.get('market_id')) for e in inplay}]
    
    # Render matches
    st.divider()
    if not inplay_display:
        if manual_mode:
            st.info("💡 Enter Market IDs above to start tracking")
        else:
            msg = "No live markets available" if not events_error else f"⚠️ API Error: {events_error}"
            st.info(msg)
    else:
        # Display live markets
        for ev in inplay_display:
            mid = str(ev.get('market_id'))
            name = event_label(ev)
            labels = st.session_state['labels'].get(mid, ["Team 1", "Team 2"])
            
            # Market container
            st.markdown("")  # Spacing
            suffix = " 🕐" if mid in time_based_ids and ev not in inplay else " 🔴 LIVE"
            st.markdown(f"### {name}{suffix}")
            st.caption(f"Market ID: {mid}")

            s = by_mid.get(mid)
            if not s:
                st.warning("⏳ Waiting for market data...")
                continue
            mid2, meta, runners = parse_market_string(s)

            # Prepare prev state structures
            prev = st.session_state['prev'].get(mid2, {"market": {"total_matched": None}, "teams": {}})
            if mid2 not in st.session_state['prev']:
                st.session_state['prev'][mid2] = prev

            # Market total matched metric (minimal display)
            tm = meta.get('total_matched')
            tm_prev = prev['market'].get('total_matched')
            tm_delta = None if tm_prev is None or tm is None else (tm - tm_prev)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.metric("Total Matched", "-" if tm is None else f"₹{tm:,.0f}")
            with col2:
                if tm_delta is not None:
                    delta_color = "#16a34a" if tm_delta > 0 else "#6b7280"
                    st.markdown(f"<div style='padding: 0.5rem 0;'><span style='color: {delta_color}; font-size: 0.9rem;'>Δ {tm_delta:+,.0f}</span></div>", unsafe_allow_html=True)
            with col3:
                st.caption(f"Updated {datetime.now(IST).strftime('%H:%M:%S')}")
            
            prev['market']['total_matched'] = tm

            # Team cards in clean grid
            st.markdown("")
            cols = st.columns(2)
            for idx, r in enumerate(runners[:2]):
                label = labels[idx] if idx < len(labels) else f"Runner {idx+1}"
                summ = summarize_runner(r)
                prev_team = prev['teams'].get(label, {})
                # deltas (for cumulative update)
                db = None if 'total_back' not in prev_team else (summ['total_back'] - prev_team['total_back'])
                dl = None if 'total_lay' not in prev_team else (summ['total_lay'] - prev_team['total_lay'])
                update_cumulative(mid2, label, db, dl)
                # Merge persisted cumulative (24/7) with session deltas for display
                persisted = {}
                try:
                    with get_conn() as conn:
                        persisted_all = get_cumulative(conn, mid2)
                        persisted = persisted_all.get(label, {})
                except Exception:
                    persisted = {}
                sess_s = st.session_state['session'].get(mid2, {}).get(label, {})
                merged = {
                    'in_back': (persisted.get('in_back', 0.0) + sess_s.get('in_back', 0.0)),
                    'in_lay': (persisted.get('in_lay', 0.0) + sess_s.get('in_lay', 0.0)),
                    'out_back': (persisted.get('out_back', 0.0) + sess_s.get('out_back', 0.0)),
                    'out_lay': (persisted.get('out_lay', 0.0) + sess_s.get('out_lay', 0.0)),
                    'net_back': (persisted.get('net_back', 0.0) + sess_s.get('net_back', 0.0)),
                    'net_lay': (persisted.get('net_lay', 0.0) + sess_s.get('net_lay', 0.0)),
                }
                render_team_card(cols[idx], label, summ, prev_team, merged)
                prev['teams'][label] = {
                    'total_back': summ['total_back'],
                    'total_lay': summ['total_lay'],
                    'best_back': summ['best_back'] if summ['best_back'] is not None else prev_team.get('best_back'),
                    'best_lay': summ['best_lay'] if summ['best_lay'] is not None else prev_team.get('best_lay'),
                }

            st.session_state['prev'][mid2] = prev
            st.divider()

    # Auto-refresh footer
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Last update: {datetime.now(IST).strftime('%H:%M:%S IST')} · Auto-refresh every {refresh_ms}ms")
    with col2:
        auto = st.checkbox("Auto", value=True, help="Auto-refresh")
    
    if auto:
        time.sleep(max(0.1, refresh_ms/1000.0))
        if hasattr(st, 'rerun'):
            st.rerun()


if __name__ == "__main__":
    main()
