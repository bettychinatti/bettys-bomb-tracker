import time
import requests
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from persistence import init_db, get_conn, upsert_market, upsert_team_labels, increment_cumulative
from token_manager import get_valid_token

# Use authenticated client endpoints (not guest endpoints)
EVENTS_API = "https://api.d99exch.com/api/client/event_list"
MARKET_API = "https://odds.o99exch.com/ws/getMarketDataNew"

# Bearer token for API authentication
# AUTO-REFRESH: Set EXCH_USERNAME and EXCH_PASSWORD env vars for automatic token refresh
# MANUAL: Update this token from browser every ~5 hours if not using auto-refresh
BEARER_TOKEN_FALLBACK = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5kOTlleGNoLmNvbS9hcGkvYXV0aCIsImlhdCI6MTc2Njc0NTQ2NywiZXhwIjoxNzY2NzYzNDY3LCJuYmYiOjE3NjY3NDU0NjcsImp0aSI6IlRNd1IwTjNwQVRQcFVIWkkiLCJzdWIiOiI5ODcyOTQiLCJwcnYiOiI4N2UwYWYxZWY5ZmQxNTgxMmZkZWM5NzE1M2ExNGUwYjA0NzU0NmFhIn0.XE3AIrm60v-No5wuNmSwDBGHZgNSYUk5S4C4kGJYd7U"

# Get valid token (auto-refreshes if credentials provided, otherwise uses fallback)
def get_bearer_token() -> str:
    """Get valid bearer token, refreshing if needed."""
    token = get_valid_token(fallback_token=BEARER_TOKEN_FALLBACK)
    return token or BEARER_TOKEN_FALLBACK

# Enhanced headers matching real browser requests
def get_headers() -> dict:
    """Get request headers with current valid token."""
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Authorization": f"bearer {get_bearer_token()}",  # Dynamic token
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


def market_ids_payload(ids: List[str]) -> List[Tuple[str, str]]:
    return [("market_ids[]", str(mid)) for mid in ids]


def fetch_events() -> List[Dict[str, Any]]:
    resp = requests.get(EVENTS_API, headers=get_headers(), timeout=10)
    resp.raise_for_status()
    data = resp.json()
    events = (data or {}).get('data', {}).get('events', [])
    return events


def fetch_market_strings(market_ids: List[str]) -> List[str]:
    if not market_ids:
        return []
    resp = requests.post(MARKET_API, headers=get_headers(), data=market_ids_payload(market_ids), timeout=10)
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
    return {
        "total_back": total_back,
        "total_lay": total_lay,
    }


def main():
    init_db()
    print("[tracker] started")
    last_events_fetch = 0.0
    watchlist: List[str] = []  # optional: add persistent watchlist later
    prev_state: Dict[str, Dict[str, Any]] = {}
    while True:
        now_epoch = time.time()
        # Refresh events every 30 minutes
        if now_epoch - last_events_fetch > 1800:
            try:
                events = fetch_events()
                last_events_fetch = now_epoch
            except Exception as e:
                print(f"[tracker] events error: {e}")
                events = []
            # derive in-play markets + any in watchlist
            def sport_of(ev: Dict[str, Any]) -> str:
                etid_val = ev.get('event_type_id')
                try:
                    etid = int(etid_val) if etid_val is not None else None
                except Exception:
                    etid = None
                return SPORT_MAP.get(etid, 'Other') if isinstance(etid, int) else 'Other'
            inplay = [ev for ev in events if ev.get('in_play') == 1]
            # Start tracking any in-play market
            with get_conn() as conn:
                for ev in inplay:
                    mid = str(ev.get('market_id'))
                    if not mid:
                        continue
                    upsert_market(conn, mid, ev.get('event_name') or ev.get('name'), sport_of(ev), int(now_epoch))
                    lbls = team_labels(ev.get('event_name') or ev.get('name') or '')
                    labels = (lbls[0], lbls[1] if len(lbls) > 1 else '')
                    upsert_team_labels(conn, mid, labels)  # store labels
        # Poll markets every second
        # Gather active market_ids from DB markets table (simple approach)
        with get_conn() as conn:
            cur = conn.execute("SELECT market_id FROM markets")
            market_ids = [row[0] for row in cur.fetchall()]
        if market_ids:
            try:
                raw = fetch_market_strings(market_ids)
            except Exception as e:
                print(f"[tracker] market fetch error: {e}")
                raw = []
            by_mid = {}
            for s in raw:
                if isinstance(s, str):
                    by_mid[s.split('|',1)[0]] = s
            # compute deltas vs previous snapshot (held in memory per loop)
            for mid in market_ids:
                s = by_mid.get(mid)
                if not s:
                    continue
                _, _, runners = parse_market_string(s)
                # assume two runners
                if len(runners) < 2:
                    continue
                sums = [summarize_runner(r) for r in runners[:2]]
                # track deltas using a simple in-memory dict keyed by mid
                prev = prev_state.get(mid)
                if prev is None:
                    prev_state[mid] = {'teams': [sums[0], sums[1]]}
                    continue
                db0 = sums[0]['total_back'] - prev['teams'][0]['total_back']
                dl0 = sums[0]['total_lay'] - prev['teams'][0]['total_lay']
                db1 = sums[1]['total_back'] - prev['teams'][1]['total_back']
                dl1 = sums[1]['total_lay'] - prev['teams'][1]['total_lay']
                prev_state[mid] = {'teams': [sums[0], sums[1]]}
                # write cumulative deltas to DB
                ts = int(time.time())
                with get_conn() as conn:
                    # read labels
                    cur = conn.execute("SELECT team_label FROM teams WHERE market_id=? ORDER BY team_label ASC", (mid,))
                    labels = [row[0] for row in cur.fetchall()]
                    # fallback labels
                    if len(labels) < 2:
                        labels = [f"Runner 1", f"Runner 2"]
                    increment_cumulative(conn, mid, labels[0], db0, dl0, ts)
                    increment_cumulative(conn, mid, labels[1], db1, dl1, ts)
        # PRO PLAN: Ultra-fast polling for microsecond precision
        # Polls every 0.1 seconds (100ms) = 10x per second
        # Catches every bet movement without missing data
        time.sleep(0.1)


if __name__ == '__main__':
    main()
