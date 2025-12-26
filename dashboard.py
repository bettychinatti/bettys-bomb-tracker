import streamlit as st
import requests
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Optional, Tuple
from persistence import get_conn, get_cumulative

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

EVENTS_API = "https://api.d99hub.com/api/guest/event_list"
MARKET_API = "https://odds.o99hub.com/ws/getMarketDataNew"

# Enhanced headers to mimic real browser and avoid IP blocking
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://gin247.net",
    "Referer": "https://gin247.net/inplay",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
    "Connection": "keep-alive",
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

    with col.container(border=True):
        col.subheader(label)
        c1, c2 = col.columns(2)
        c1.metric("BACK total", f"{tb:,.2f}", None if db is None else f"{db:+.2f}")
        c2.metric("LAY total", f"{tl:,.2f}", None if dl is None else f"{dl:+.2f}")
        c3, c4 = col.columns(2)
        c3.metric("Best BACK", bb, None if dbb is None else f"{dbb:+.2f}")
        c4.metric("Best LAY", bl, None if dbl is None else f"{dbl:+.2f}")
        back3 = ", ".join([f"{o:.2f}@{a:.2f}" for o,a in summ['back_top3']]) or '-'
        lay3 = ", ".join([f"{o:.2f}@{a:.2f}" for o,a in summ['lay_top3']]) or '-'
        col.caption(f"BACK top3: {back3}")
        col.caption(f"LAY top3: {lay3}")
        # session cumulative
        inflow = sess_s.get('in_back',0.0) + sess_s.get('in_lay',0.0)
        outflow = sess_s.get('out_back',0.0) + sess_s.get('out_lay',0.0)
        net = sess_s.get('net_back',0.0) + sess_s.get('net_lay',0.0)
        col.write(f"Session staked≈{inflow:,.2f} • withdrawn≈{outflow:,.2f} • net≈{net:,.2f}")


def main():
    st.set_page_config(page_title="Betty's Bomb Tracker", layout="wide")
    st.title("Betty's Bomb Tracker")
    ensure_state()

    # Controls
    st.sidebar.header("Controls")
    refresh_ms = st.sidebar.slider("Refresh interval (ms)", 500, 3000, 1000, step=250)
    track_scope = st.sidebar.radio("Track scope", ["Selected sport", "All sports"], index=0)
    st.sidebar.caption("Tracking starts automatically for in-play events. Upcoming events appear as 'Scheduled'.")

    # Fetch events with 30-min cache and manual refresh controls
    b1, b2 = st.sidebar.columns(2)
    do_refresh = b1.button("Refresh matches now")
    do_clear = b2.button("Clear cache", help="Drops the 30‑min cache and refetches")
    if do_clear:
        # Reset cache so the next fetch is guaranteed to refetch
        st.session_state['events_cache'] = {'events': [], 'last_fetch_epoch': 0.0, 'error': None}
    events, events_error, last_fetch_epoch = get_events_cached(force=(do_refresh or do_clear))
    # Status line: last updated + count
    count = len(events) if isinstance(events, list) else 0
    if events_error:
        st.sidebar.warning("Events API unavailable. Switch to Manual input mode below to track by Market ID.")
        st.sidebar.caption("Tip: Click Clear cache, then Refresh.")
    if last_fetch_epoch:
        last_fetch_str = datetime.fromtimestamp(last_fetch_epoch, IST).strftime('%H:%M:%S')
        st.sidebar.caption(f"Events last updated: {last_fetch_str} • {count} events • auto every 30 min")

    # Manual fallback toggle
    manual_mode = st.sidebar.checkbox(
        "Manual input mode", value=(events_error is not None),
        help="Enable to enter Market IDs and labels manually when events feed is down"
    )

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
    selected_sport = st.sidebar.selectbox("Sport", options=sports_present)

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
        st.sidebar.subheader("Manual inputs")
        markets_text = st.sidebar.text_input("Market IDs (comma-separated)", value="")
        match_label = st.sidebar.text_input("Match label (e.g., Team A vs Team B)", value="")
        # Derive team labels from the match label if present
        t1, t2 = team_labels(match_label)
        if not match_label:
            st.sidebar.info("Enter a match label to name the team cards (e.g., 'Sharjah vs Dubai').")
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

    # Sidebar: list of events with quick navigation
    if 'focus_mid' not in st.session_state:
        st.session_state['focus_mid'] = None
    st.sidebar.subheader("In-play matches")
    for ev in inplay:
        mid = str(ev.get('market_id'))
        label = event_label(ev)
        if st.sidebar.button(f"🎯 {label}", key=f"goto_{mid}"):
            st.session_state['focus_mid'] = mid
            if hasattr(st, 'rerun'):
                st.rerun()
    if not manual_mode:
        st.sidebar.subheader("Scheduled")
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

    # Render matches
    st.subheader("Live matches")
    # Combine true in-play with time-based fallback (secondary)
    time_based_ids = set()
    if not manual_mode:
        time_based_ids = {str(ev.get('market_id')) for ev in started_by_time if ev.get('market_id')}
    inplay_display = list(inplay)
    if not manual_mode:
        # Append time-based only if not already in in-play
        inplay_display += [ev for ev in started_by_time if str(ev.get('market_id')) not in {str(e.get('market_id')) for e in inplay}]

    # Reorder or filter by focus
    if st.session_state.get('focus_mid'):
        fm = st.session_state['focus_mid']
        inplay_display = [ev for ev in inplay_display if str(ev.get('market_id')) == fm] + [ev for ev in inplay_display if str(ev.get('market_id')) != fm]
        if focus_only:
            inplay_display = [ev for ev in inplay_display if str(ev.get('market_id')) == fm]

    if not inplay_display:
        if manual_mode:
            st.info("Enter one or more Market IDs in the sidebar to start tracking.")
        else:
            msg = "No in-play matches in the selected scope." if not events_error else f"Events feed unavailable: {events_error}"
            st.info(msg)
    else:
        # Chunk into rows of two
        for ev in inplay_display:
            mid = str(ev.get('market_id'))
            name = event_label(ev)
            labels = st.session_state['labels'].get(mid, ["Team 1", "Team 2"])
            container = st.container(border=True)
            # Mark time-based items for clarity
            suffix = " • time-based" if mid in time_based_ids and ev not in inplay else ""
            container.markdown(f"#### {name}  •  Market {mid}{suffix}")

            s = by_mid.get(mid)
            if not s:
                container.warning("No market data yet.")
                continue
            mid2, meta, runners = parse_market_string(s)

            # Prepare prev state structures
            prev = st.session_state['prev'].get(mid2, {"market": {"total_matched": None}, "teams": {}})
            if mid2 not in st.session_state['prev']:
                st.session_state['prev'][mid2] = prev

            # Market total matched metric
            tm = meta.get('total_matched')
            tm_prev = prev['market'].get('total_matched')
            tm_delta = None if tm_prev is None or tm is None else (tm - tm_prev)
            mcol = container.container()
            mcol.metric("Market total matched", "-" if tm is None else f"{tm:,.2f}", None if tm_delta is None else f"{tm_delta:+.2f}")
            prev['market']['total_matched'] = tm

            # Team cards
            cols = container.columns(2)
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

    st.caption(f"Last updated: {datetime.now(IST).strftime('%H:%M:%S')}")
    # Robust auto-refresh compatible across Streamlit versions
    auto = st.sidebar.checkbox("Auto refresh", value=True, help="Re-run the dashboard automatically at the chosen interval")
    if auto:
        time.sleep(max(0.1, refresh_ms/1000.0))
        if hasattr(st, 'rerun'):
            st.rerun()


if __name__ == "__main__":
    main()
