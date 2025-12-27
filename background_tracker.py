"""""""""import time

Real-time Cumulative Market Tracker

Polls APIs every 2 seconds and tracks money movementsBackground Market Tracker - Polls API every 2 seconds and tracks cumulative stake changes

"""

import time"""Real-time Cumulative Market Trackerimport requests

import requests

import sqlite3import sqlite3

from datetime import datetime, timezone

from pathlib import Pathimport requestsPolls APIs every 2 seconds and tracks money movementsfrom datetime import datetime, timezone

from typing import Any, Dict, List, Optional, Tuple

import time

# Database configuration

if Path('/data').exists():from pathlib import Path"""from typing import Any, Dict, List, Optional, Tuple

    DB_PATH = Path('/data') / 'tracker.db'

else:from datetime import datetime

    DB_PATH = Path(__file__).parent / 'data' / 'tracker.db'

    DB_PATH.parent.mkdir(exist_ok=True)import requests



# API Configuration# Database path (same location as dashboard)

EVENTS_API = "https://api.d99exch.com/api/guest/event_list"

ODDS_API = "https://odds.o99exch.com/ws/getMarketDataNew"if Path('/data').exists():import sqlite3from persistence import init_db, get_conn, upsert_market, upsert_team_labels, increment_cumulative

HEADERS = {

    "accept": "application/json",    DB_PATH = Path('/data') / 'tracker.db'

    "origin": "https://d99exch.com",

    "referer": "https://d99exch.com/"else:import timefrom token_manager import get_valid_token

}

    DB_PATH = Path(__file__).parent / 'data' / 'tracker.db'

# Tracking configuration

POLL_INTERVAL = 2  # seconds    DB_PATH.parent.mkdir(exist_ok=True)from datetime import datetime

SPORT_ID = 4  # Cricket



def init_database():

    """Initialize SQLite database with schema for tracking"""def init_database():from pathlib import Path# Use authenticated client endpoints (not guest endpoints)

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()    """Initialize SQLite database with schema"""

    

    # Snapshots table - stores raw stake data at each poll    conn = sqlite3.connect(DB_PATH)import osEVENTS_API = "https://api.d99exch.com/api/client/event_list"

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS snapshots (    cursor = conn.cursor()

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            timestamp TEXT NOT NULL,    MARKET_API = "https://odds.o99exch.com/ws/getMarketDataNew"

            market_id TEXT NOT NULL,

            selection_id TEXT NOT NULL,    # Table for snapshots (raw data at each poll)

            team_label TEXT NOT NULL,

            back_stake REAL DEFAULT 0,    cursor.execute("""# Database path

            lay_stake REAL DEFAULT 0,

            back_odds REAL DEFAULT 0,        CREATE TABLE IF NOT EXISTS snapshots (

            lay_odds REAL DEFAULT 0

        )            id INTEGER PRIMARY KEY AUTOINCREMENT,if os.path.exists('/data'):# Bearer token for API authentication

    """)

                market_id TEXT,

    # Cumulative table - stores aggregated in/out/net flows

    cursor.execute("""            selection_id TEXT,    DB_PATH = Path('/data') / 'tracker.db'# AUTO-REFRESH: Set EXCH_USERNAME and EXCH_PASSWORD env vars for automatic token refresh

        CREATE TABLE IF NOT EXISTS cumulative (

            market_id TEXT NOT NULL,            team_label TEXT,

            selection_id TEXT NOT NULL,

            team_label TEXT NOT NULL,            back_stake REAL,else:# MANUAL: Update this token from browser every ~5 hours if not using auto-refresh

            in_back REAL DEFAULT 0,

            in_lay REAL DEFAULT 0,            lay_stake REAL,

            out_back REAL DEFAULT 0,

            out_lay REAL DEFAULT 0,            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP    DB_PATH = Path(__file__).parent / 'data' / 'tracker.db'BEARER_TOKEN_FALLBACK = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5kOTlleGNoLmNvbS9hcGkvYXV0aCIsImlhdCI6MTc2Njc0NTQ2NywiZXhwIjoxNzY2NzYzNDY3LCJuYmYiOjE3NjY3NDU0NjcsImp0aSI6IlRNd1IwTjNwQVRQcFVIWkkiLCJzdWIiOiI5ODcyOTQiLCJwcnYiOiI4N2UwYWYxZWY5ZmQxNTgxMmZkZWM5NzE1M2ExNGUwYjA0NzU0NmFhIn0.XE3AIrm60v-No5wuNmSwDBGHZgNSYUk5S4C4kGJYd7U"

            net_back REAL DEFAULT 0,

            net_lay REAL DEFAULT 0,        )

            updated_at TEXT NOT NULL,

            PRIMARY KEY (market_id, selection_id)    """)

        )

    """)    

    

    # Index for faster queries    # Table for cumulative tracking (aggregated changes)# Ensure parent directory exists# Get valid token (auto-refreshes if credentials provided, otherwise uses fallback)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_market ON snapshots(market_id, selection_id)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON snapshots(timestamp)")    cursor.execute("""

    

    conn.commit()        CREATE TABLE IF NOT EXISTS cumulative (DB_PATH.parent.mkdir(parents=True, exist_ok=True)def get_bearer_token() -> str:

    conn.close()

    print(f"✅ Database initialized at {DB_PATH}")            market_id TEXT,



def fetch_live_events() -> List[Dict[str, Any]]:            selection_id TEXT,    """Get valid bearer token, refreshing if needed."""

    """Fetch live cricket events"""

    try:            team_label TEXT,

        url = f"{EVENTS_API}?sport_id={SPORT_ID}"

        resp = requests.get(url, headers=HEADERS, timeout=10)            in_back REAL DEFAULT 0,def init_database():    token = get_valid_token(fallback_token=BEARER_TOKEN_FALLBACK)

        if resp.status_code == 200:

            data = resp.json()            in_lay REAL DEFAULT 0,

            events = data.get("data", {}).get("events", [])

            live_events = [e for e in events if e.get("in_play") == 1]            out_back REAL DEFAULT 0,    """Initialize database schema"""    return token or BEARER_TOKEN_FALLBACK

            return live_events

    except Exception as e:            out_lay REAL DEFAULT 0,

        print(f"❌ Error fetching events: {e}")

    return []            net_back REAL DEFAULT 0,    conn = sqlite3.connect(DB_PATH)



def parse_market_data(raw_data: str) -> Optional[Dict[str, Any]]:            net_lay REAL DEFAULT 0,

    """Parse pipe-delimited market data format"""

    try:            updated_at DATETIME,    cursor = conn.cursor()# Enhanced headers matching real browser requests

        parts = raw_data.split('~')

        if len(parts) < 8:            PRIMARY KEY (market_id, selection_id)

            return None

                )    def get_headers() -> dict:

        market_id = parts[0]

        selections = []    """)

        

        # Parse runner data (starts at index 7)        # Table for current snapshot    """Get request headers with current valid token."""

        i = 7

        while i < len(parts):    conn.commit()

            if '|' in parts[i]:

                runner_parts = parts[i].split('|')    conn.close()    cursor.execute("""    return {

                if len(runner_parts) >= 11:

                    selection_id = runner_parts[0]    print(f"✅ Database initialized at: {DB_PATH}")

                    team_label = runner_parts[10] if len(runner_parts) > 10 else "Unknown"

                            CREATE TABLE IF NOT EXISTS snapshots (        "Content-Type": "application/x-www-form-urlencoded",

                    # Parse back odds (index 1-3)

                    back_stakes = []def fetch_live_events():

                    if len(runner_parts) > 3:

                        for j in range(1, 4):    """Fetch all live cricket events"""            market_id TEXT,        "Accept": "application/json, text/plain, */*",

                            try:

                                back_stakes.append(float(runner_parts[j]))    try:

                            except (ValueError, IndexError):

                                back_stakes.append(0.0)        headers = {            selection_id TEXT,        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",

                    

                    # Parse lay odds (index 4-6)            "accept": "application/json",

                    lay_stakes = []

                    if len(runner_parts) > 6:            "origin": "https://d99exch.com",            timestamp TEXT,        "Accept-Encoding": "gzip, deflate, br, zstd",

                        for j in range(4, 7):

                            try:            "referer": "https://d99exch.com/"

                                lay_stakes.append(float(runner_parts[j]))

                            except (ValueError, IndexError):        }            back_total REAL,        "Authorization": f"bearer {get_bearer_token()}",  # Dynamic token

                                lay_stakes.append(0.0)

                            url = "https://api.d99exch.com/api/guest/event_list?sport_id=4"

                    # Parse odds (back at 7, lay at 8)

                    back_odds = float(runner_parts[7]) if len(runner_parts) > 7 and runner_parts[7] else 0.0        resp = requests.get(url, headers=headers, timeout=10)            lay_total REAL,        "Origin": "https://99exch.com",

                    lay_odds = float(runner_parts[8]) if len(runner_parts) > 8 and runner_parts[8] else 0.0

                            

                    selections.append({

                        'selection_id': selection_id,        if resp.status_code == 200:            PRIMARY KEY (market_id, selection_id, timestamp)        "Referer": "https://99exch.com/",

                        'team': team_label,

                        'back_stake': sum(back_stakes),            data = resp.json()

                        'lay_stake': sum(lay_stakes),

                        'back_odds': back_odds,            events = data.get("data", {}).get("events", [])        )        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",

                        'lay_odds': lay_odds

                    })            live_events = [e for e in events if e.get("in_play") == 1]

            i += 1

                    return live_events    """)        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',

        if selections:

            return {        return []

                'market_id': market_id,

                'selections': selections    except Exception as e:            "sec-ch-ua-mobile": "?0",

            }

    except Exception as e:        print(f"❌ Error fetching events: {e}")

        print(f"❌ Parse error: {e}")

    return None        return []    # Table for cumulative tracking        "sec-ch-ua-platform": '"macOS"',



def fetch_market_odds(market_id: str) -> Optional[Dict[str, Any]]:

    """Fetch odds data for a specific market"""

    try:def parse_market_data(raw_data):    cursor.execute("""        "sec-fetch-dest": "empty",

        url = f"{ODDS_API}?marketId={market_id}&eventTypeId={SPORT_ID}"

        resp = requests.get(url, headers=HEADERS, timeout=10)    """Parse pipe-delimited market data"""

        if resp.status_code == 200:

            data = resp.json()    teams = []        CREATE TABLE IF NOT EXISTS cumulative (        "sec-fetch-mode": "cors",

            if data.get("success") and data.get("data"):

                return parse_market_data(data["data"])    try:

    except Exception as e:

        print(f"❌ Error fetching odds for {market_id}: {e}")        parts = raw_data.split("|")            market_id TEXT,        "sec-fetch-site": "cross-site",

    return None

        

def get_last_snapshot(market_id: str, selection_id: str) -> Optional[Tuple[float, float]]:

    """Get the last recorded stakes for a selection"""        i = 0            selection_id TEXT,        "priority": "u=1, i",

    try:

        conn = sqlite3.connect(DB_PATH)        while i < len(parts):

        cursor = conn.execute("""

            SELECT back_stake, lay_stake            if "~" in parts[i]:            team_label TEXT,    }

            FROM snapshots

            WHERE market_id = ? AND selection_id = ?                team_info = parts[i].split("~")

            ORDER BY timestamp DESC

            LIMIT 1                if len(team_info) >= 2:            in_back REAL DEFAULT 0,

        """, (market_id, selection_id))

        row = cursor.fetchone()                    selection_id = team_info[0]

        conn.close()

        if row:                    team_label = team_info[1]            in_lay REAL DEFAULT 0,SPORT_MAP = {1: "Soccer", 2: "Tennis", 4: "Cricket"}

            return (row[0], row[1])

    except Exception as e:                    

        print(f"❌ Error getting last snapshot: {e}")

    return None                    # Parse back prices/sizes (next 3 pairs)            out_back REAL DEFAULT 0,



def save_snapshot(timestamp: str, market_id: str, selection_id: str, team_label: str,                     back_total = 0

                  back_stake: float, lay_stake: float, back_odds: float, lay_odds: float):

    """Save a snapshot to the database"""                    for j in range(3):            out_lay REAL DEFAULT 0,

    try:

        conn = sqlite3.connect(DB_PATH)                        if i + 1 + (j * 2) < len(parts):

        conn.execute("""

            INSERT INTO snapshots (timestamp, market_id, selection_id, team_label, back_stake, lay_stake, back_odds, lay_odds)                            try:            net_back REAL DEFAULT 0,def market_ids_payload(ids: List[str]) -> List[Tuple[str, str]]:

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        """, (timestamp, market_id, selection_id, team_label, back_stake, lay_stake, back_odds, lay_odds))                                size = float(parts[i + 2 + (j * 2)])

        conn.commit()

        conn.close()                                back_total += size            net_lay REAL DEFAULT 0,    return [("market_ids[]", str(mid)) for mid in ids]

    except Exception as e:

        print(f"❌ Error saving snapshot: {e}")                            except:



def update_cumulative(market_id: str, selection_id: str, team_label: str,                                pass            updated_at TEXT,

                      delta_back: float, delta_lay: float, timestamp: str):

    """Update cumulative tracking with deltas"""                    

    try:

        conn = sqlite3.connect(DB_PATH)                    # Parse lay prices/sizes (next 3 pairs after back)            PRIMARY KEY (market_id, selection_id)

        cursor = conn.cursor()

                            lay_total = 0

        # Get current cumulative data

        cursor.execute("""                    for j in range(3):        )def fetch_events() -> List[Dict[str, Any]]:

            SELECT in_back, in_lay, out_back, out_lay, net_back, net_lay

            FROM cumulative                        if i + 7 + (j * 2) < len(parts):

            WHERE market_id = ? AND selection_id = ?

        """, (market_id, selection_id))                            try:    """)    resp = requests.get(EVENTS_API, headers=get_headers(), timeout=10)

        row = cursor.fetchone()

                                        size = float(parts[i + 8 + (j * 2)])

        if row:

            in_back, in_lay, out_back, out_lay, net_back, net_lay = row                                lay_total += size        resp.raise_for_status()

        else:

            in_back = in_lay = out_back = out_lay = net_back = net_lay = 0.0                            except:

        

        # Calculate new values based on deltas                                pass    # Index for faster queries    data = resp.json()

        if delta_back > 0:

            in_back += delta_back                    

        elif delta_back < 0:

            out_back += abs(delta_back)                    teams.append({    cursor.execute("CREATE INDEX IF NOT EXISTS idx_market ON cumulative(market_id)")    events = (data or {}).get('data', {}).get('events', [])

        

        if delta_lay > 0:                        "selection_id": selection_id,

            in_lay += delta_lay

        elif delta_lay < 0:                        "team": team_label,    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON snapshots(timestamp)")    return events

            out_lay += abs(delta_lay)

                                "total_back": back_total,

        net_back = in_back - out_back

        net_lay = in_lay - out_lay                        "total_lay": lay_total    

        

        # Upsert cumulative data                    })

        cursor.execute("""

            INSERT OR REPLACE INTO cumulative (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at)                        conn.commit()

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, timestamp))                    i += 13  # Skip to next team data

        

        conn.commit()                    continue    conn.close()def fetch_market_strings(market_ids: List[str]) -> List[str]:

        conn.close()

    except Exception as e:            i += 1

        print(f"❌ Error updating cumulative: {e}")

    except Exception as e:    print(f"✅ Database initialized at {DB_PATH}")    if not market_ids:

def track_market(market_id: str):

    """Track a single market and calculate deltas"""        print(f"Parse error: {e}")

    market_data = fetch_market_odds(market_id)

    if not market_data:            return []

        return

        return teams

    timestamp = datetime.now(timezone.utc).isoformat()

    def fetch_live_events():    resp = requests.post(MARKET_API, headers=get_headers(), data=market_ids_payload(market_ids), timeout=10)

    for selection in market_data['selections']:

        selection_id = selection['selection_id']def track_market(market_id, market_name):

        team_label = selection['team']

        current_back = selection['back_stake']    """Track a single market - compare current vs last snapshot, update cumulative"""    """Fetch all live cricket events"""    resp.raise_for_status()

        current_lay = selection['lay_stake']

        back_odds = selection['back_odds']    try:

        lay_odds = selection['lay_odds']

                headers = {    try:    out = resp.json()

        # Get last snapshot

        last = get_last_snapshot(market_id, selection_id)            "accept": "application/json",

        

        if last:            "origin": "https://o99exch.com",        headers = {"accept": "application/json", "origin": "https://d99exch.com"}    return out if isinstance(out, list) else []

            last_back, last_lay = last

            delta_back = current_back - last_back            "referer": "https://o99exch.com/"

            delta_lay = current_lay - last_lay

                    }        url = "https://api.d99exch.com/api/guest/event_list?sport_id=4"

            # Only update if there's a change

            if delta_back != 0 or delta_lay != 0:        url = f"https://odds.o99exch.com/ws/getMarketDataNew?market_id={market_id}"

                update_cumulative(market_id, selection_id, team_label, delta_back, delta_lay, timestamp)

                print(f"📊 {team_label}: ΔBack={delta_back:+.2f}, ΔLay={delta_lay:+.2f}")        resp = requests.get(url, headers=headers, timeout=8)        resp = requests.get(url, headers=headers, timeout=10)

        

        # Save current snapshot        

        save_snapshot(timestamp, market_id, selection_id, team_label, current_back, current_lay, back_odds, lay_odds)

        if resp.status_code != 200:        if resp.status_code == 200:def parse_market_string(market_str: str) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:

def main():

    """Main tracking loop"""            return

    print("🚀 Starting Background Market Tracker")

    print(f"📂 Database: {DB_PATH}")                    data = resp.json()    f = market_str.split('|')

    print(f"⏱️  Poll interval: {POLL_INTERVAL}s")

    print("=" * 60)        data = resp.json()

    

    init_database()        if not data.get("data"):            events = data.get("data", {}).get("events", [])    mid = f[0]

    

    tracked_markets = set()            return

    

    while True:                    return [e for e in events if e.get("in_play") == 1 and e.get("market_id")]    total_matched: Optional[float] = None

        try:

            # Fetch live events        raw_odds = data["data"]

            events = fetch_live_events()

            current_markets = set()        current_teams = parse_market_data(raw_odds)        return []    if len(f) > 5:

            

            for event in events:        

                market_id = event.get("market_id")

                if market_id:        if not current_teams:    except Exception as e:        try:

                    current_markets.add(market_id)

                                return

                    # Track new markets

                    if market_id not in tracked_markets:                print(f"❌ Error fetching events: {e}")            total_matched = float(f[5])

                        event_name = event.get("event_name", "Unknown")

                        print(f"🆕 Tracking new market: {event_name} ({market_id})")        conn = sqlite3.connect(DB_PATH)

                        tracked_markets.add(market_id)

                            cursor = conn.cursor()        return []        except Exception:

                    # Track the market

                    track_market(market_id)        

            

            # Remove markets that are no longer live        for team in current_teams:            total_matched = None

            removed = tracked_markets - current_markets

            if removed:            selection_id = team["selection_id"]

                print(f"🔴 Markets finished: {len(removed)}")

                tracked_markets = current_markets            team_label = team["team"]def fetch_market_odds(market_id):    runners: List[Dict[str, Any]] = []

            

            # Wait before next poll            current_back = team["total_back"]

            time.sleep(POLL_INTERVAL)

                        current_lay = team["total_lay"]    """Fetch raw odds data for a market"""    i = 0

        except KeyboardInterrupt:

            print("\n⏹️  Tracker stopped by user")            

            break

        except Exception as e:            # Get last snapshot    try:    while i < len(f):

            print(f"❌ Error in main loop: {e}")

            time.sleep(POLL_INTERVAL)            cursor.execute("""



if __name__ == "__main__":                SELECT back_stake, lay_stake        url = "https://odds.o99exch.com/ws/getMarketDataNew"        if f[i] == 'ACTIVE':

    main()

                FROM snapshots

                WHERE market_id = ? AND selection_id = ?        headers = {"content-type": "application/x-www-form-urlencoded", "origin": "https://99exch.com"}            sel_id = f[i-1] if i-1 >= 0 else None

                ORDER BY timestamp DESC LIMIT 1

            """, (market_id, selection_id))        resp = requests.post(url, data=f"market_ids[]={market_id}", headers=headers, timeout=5)            i += 1

            

            last_row = cursor.fetchone()        if resp.status_code == 200:            pairs: List[Tuple[float, float]] = []

            

            if last_row:            result = resp.json()            read = 0

                last_back, last_lay = last_row

                            if result and result[0]:            while i + 1 < len(f) and read < 12:

                # Calculate deltas

                back_delta = current_back - last_back                return result[0]                try:

                lay_delta = current_lay - last_lay

                        return None                    odd = float(f[i]); amt = float(f[i+1])

                # Update cumulative based on deltas

                update_cumulative(cursor, market_id, selection_id, team_label, back_delta, lay_delta)    except Exception as e:                    pairs.append((odd, amt))

            else:

                # First snapshot - initialize cumulative        print(f"❌ Error fetching odds for {market_id}: {e}")                    i += 2; read += 2

                cursor.execute("""

                    INSERT OR REPLACE INTO cumulative         return None                except Exception:

                    (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at)

                    VALUES (?, ?, ?, 0, 0, 0, 0, 0, 0, ?)                    break

                """, (market_id, selection_id, team_label, datetime.now()))

            def parse_market_data(odds_str):            back_pairs = pairs[:3]

            # Save current snapshot

            cursor.execute("""    """Parse pipe-delimited odds data"""            lay_pairs = pairs[3:6]

                INSERT INTO snapshots (market_id, selection_id, team_label, back_stake, lay_stake)

                VALUES (?, ?, ?, ?, ?)    try:            runners.append({"selection_id": sel_id, "back": back_pairs, "lay": lay_pairs})

            """, (market_id, selection_id, team_label, current_back, current_lay))

                parts = odds_str.split('|')        else:

        conn.commit()

        conn.close()        selections = []            i += 1

        

    except Exception as e:            return mid, {"total_matched": total_matched}, runners

        print(f"❌ Track error for {market_name}: {e}")

        i = 0

def update_cumulative(cursor, market_id, selection_id, team_label, back_delta, lay_delta):

    """Update cumulative in/out/net based on deltas"""        selection_idx = 0

    # Get current cumulative

    cursor.execute("""        while i < len(parts):def team_labels(name: str) -> List[str]:

        SELECT in_back, in_lay, out_back, out_lay, net_back, net_lay

        FROM cumulative            if parts[i] == 'ACTIVE':    if not name:

        WHERE market_id = ? AND selection_id = ?

    """, (market_id, selection_id))                back_total = 0        return ["Team 1", "Team 2"]

    

    row = cursor.fetchone()                lay_total = 0    for sep in [' v ', ' vs ', ' VS ', ' Vs ', ' V ']:

    

    if row:                        if sep in name:

        in_back, in_lay, out_back, out_lay, net_back, net_lay = row

    else:                # Parse 3 back prices (price, size pairs)            parts = [p.strip() for p in name.split(sep) if p.strip()]

        in_back = in_lay = out_back = out_lay = net_back = net_lay = 0

                    j = i + 1            if len(parts) >= 2:

    # Update based on delta direction

    if back_delta > 0:                for _ in range(3):                return [parts[0], parts[1]]

        in_back += back_delta

        net_back += back_delta                    if j + 1 < len(parts):    return [name.strip(), '']

    elif back_delta < 0:

        out_back += abs(back_delta)                        try:

        net_back += back_delta

                                size = float(parts[j + 1])

    if lay_delta > 0:

        in_lay += lay_delta                            back_total += sizedef summarize_runner(r: Dict[str, Any]) -> Dict[str, Any]:

        net_lay += lay_delta

    elif lay_delta < 0:                        except:    back = r.get('back', [])

        out_lay += abs(lay_delta)

        net_lay += lay_delta                            pass    lay = r.get('lay', [])

    

    # Update database                        j += 2    total_back = float(sum(a for _, a in back))

    cursor.execute("""

        INSERT OR REPLACE INTO cumulative                     total_lay = float(sum(a for _, a in lay))

        (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at)

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)                # Parse 3 lay prices (price, size pairs)    return {

    """, (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, datetime.now()))

                for _ in range(3):        "total_back": total_back,

def main():

    """Main polling loop"""                    if j + 1 < len(parts):        "total_lay": total_lay,

    print("🚀 Starting background market tracker...")

    print(f"📍 Database: {DB_PATH}")                        try:    }

    

    init_database()                            size = float(parts[j + 1])

    

    poll_count = 0                            lay_total += size

    

    while True:                        except:def main():

        try:

            poll_count += 1                            pass    init_db()

            print(f"\n🔄 Poll #{poll_count} at {datetime.now().strftime('%H:%M:%S')}")

                                    j += 2    print("[tracker] started")

            events = fetch_live_events()

                                last_events_fetch = 0.0

            if not events:

                print("⏸️  No live events found")                selections.append({    watchlist: List[str] = []  # optional: add persistent watchlist later

                time.sleep(2)

                continue                    'selection_id': selection_idx,    prev_state: Dict[str, Dict[str, Any]] = {}

            

            print(f"📊 Tracking {len(events)} live events...")                    'back_total': back_total,    while True:

            

            for event in events:                    'lay_total': lay_total        now_epoch = time.time()

                market_id = event.get("market_id")

                event_name = event.get("event_name", "Unknown")                })        # Refresh events every 30 minutes

                

                if market_id:                        if now_epoch - last_events_fetch > 1800:

                    track_market(market_id, event_name)

                            selection_idx += 1            try:

            print(f"✅ Poll #{poll_count} complete")

                            i = j                events = fetch_events()

            time.sleep(2)  # Poll every 2 seconds

                        else:                last_events_fetch = now_epoch

        except KeyboardInterrupt:

            print("\n🛑 Tracker stopped by user")                i += 1            except Exception as e:

            break

        except Exception as e:                        print(f"[tracker] events error: {e}")

            print(f"❌ Main loop error: {e}")

            time.sleep(2)        return selections                events = []



if __name__ == "__main__":    except Exception as e:            # derive in-play markets + any in watchlist

    main()

        print(f"❌ Parse error: {e}")            def sport_of(ev: Dict[str, Any]) -> str:

        return []                etid_val = ev.get('event_type_id')

                try:

def get_last_snapshot(market_id, selection_id):                    etid = int(etid_val) if etid_val is not None else None

    """Get last recorded snapshot for comparison"""                except Exception:

    try:                    etid = None

        conn = sqlite3.connect(DB_PATH)                return SPORT_MAP.get(etid, 'Other') if isinstance(etid, int) else 'Other'

        cursor = conn.execute("""            inplay = [ev for ev in events if ev.get('in_play') == 1]

            SELECT back_total, lay_total, timestamp            # Start tracking any in-play market

            FROM snapshots            with get_conn() as conn:

            WHERE market_id = ? AND selection_id = ?                for ev in inplay:

            ORDER BY timestamp DESC                    mid = str(ev.get('market_id'))

            LIMIT 1                    if not mid:

        """, (market_id, str(selection_id)))                        continue

        row = cursor.fetchone()                    upsert_market(conn, mid, ev.get('event_name') or ev.get('name'), sport_of(ev), int(now_epoch))

        conn.close()                    lbls = team_labels(ev.get('event_name') or ev.get('name') or '')

                            labels = (lbls[0], lbls[1] if len(lbls) > 1 else '')

        if row:                    upsert_team_labels(conn, mid, labels)  # store labels

            return {'back': row[0], 'lay': row[1], 'timestamp': row[2]}        # Poll markets every second

        return None        # Gather active market_ids from DB markets table (simple approach)

    except:        with get_conn() as conn:

        return None            cur = conn.execute("SELECT market_id FROM markets")

            market_ids = [row[0] for row in cur.fetchall()]

def save_snapshot(market_id, selection_id, back_total, lay_total, timestamp):        if market_ids:

    """Save current snapshot"""            try:

    try:                raw = fetch_market_strings(market_ids)

        conn = sqlite3.connect(DB_PATH)            except Exception as e:

        conn.execute("""                print(f"[tracker] market fetch error: {e}")

            INSERT OR REPLACE INTO snapshots (market_id, selection_id, timestamp, back_total, lay_total)                raw = []

            VALUES (?, ?, ?, ?, ?)            by_mid = {}

        """, (market_id, str(selection_id), timestamp, back_total, lay_total))            for s in raw:

        conn.commit()                if isinstance(s, str):

        conn.close()                    by_mid[s.split('|',1)[0]] = s

    except Exception as e:            # compute deltas vs previous snapshot (held in memory per loop)

        print(f"❌ Error saving snapshot: {e}")            for mid in market_ids:

                s = by_mid.get(mid)

def update_cumulative(market_id, selection_id, team_label, delta_back, delta_lay):                if not s:

    """Update cumulative tracking with deltas"""                    continue

    try:                _, _, runners = parse_market_string(s)

        conn = sqlite3.connect(DB_PATH)                # assume two runners

        timestamp = datetime.now().isoformat()                if len(runners) < 2:

                            continue

        # Get current cumulative or create new                sums = [summarize_runner(r) for r in runners[:2]]

        cursor = conn.execute("""                # track deltas using a simple in-memory dict keyed by mid

            SELECT in_back, in_lay, out_back, out_lay, net_back, net_lay                prev = prev_state.get(mid)

            FROM cumulative                if prev is None:

            WHERE market_id = ? AND selection_id = ?                    prev_state[mid] = {'teams': [sums[0], sums[1]]}

        """, (market_id, str(selection_id)))                    continue

        row = cursor.fetchone()                db0 = sums[0]['total_back'] - prev['teams'][0]['total_back']

                        dl0 = sums[0]['total_lay'] - prev['teams'][0]['total_lay']

        if row:                db1 = sums[1]['total_back'] - prev['teams'][1]['total_back']

            in_back, in_lay, out_back, out_lay, net_back, net_lay = row                dl1 = sums[1]['total_lay'] - prev['teams'][1]['total_lay']

        else:                prev_state[mid] = {'teams': [sums[0], sums[1]]}

            in_back = in_lay = out_back = out_lay = net_back = net_lay = 0                # write cumulative deltas to DB

                        ts = int(time.time())

        # Update based on delta direction                with get_conn() as conn:

        if delta_back > 0:                    # read labels

            in_back += delta_back                    cur = conn.execute("SELECT team_label FROM teams WHERE market_id=? ORDER BY team_label ASC", (mid,))

        elif delta_back < 0:                    labels = [row[0] for row in cur.fetchall()]

            out_back += abs(delta_back)                    # fallback labels

                            if len(labels) < 2:

        if delta_lay > 0:                        labels = [f"Runner 1", f"Runner 2"]

            in_lay += delta_lay                    increment_cumulative(conn, mid, labels[0], db0, dl0, ts)

        elif delta_lay < 0:                    increment_cumulative(conn, mid, labels[1], db1, dl1, ts)

            out_lay += abs(delta_lay)        # PRO PLAN: Ultra-fast polling for microsecond precision

                # Polls every 0.1 seconds (100ms) = 10x per second

        net_back += delta_back        # Catches every bet movement without missing data

        net_lay += delta_lay        time.sleep(0.1)

        

        # Save updated cumulative

        conn.execute("""if __name__ == '__main__':

            INSERT OR REPLACE INTO cumulative     main()

            (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (market_id, str(selection_id), team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, timestamp))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"❌ Error updating cumulative: {e}")
        return False

def track_market(event):
    """Track a single market for money movements"""
    market_id = event.get('market_id')
    event_name = event.get('name', 'Unknown')
    
    odds_data = fetch_market_odds(market_id)
    if not odds_data:
        return
    
    selections = parse_market_data(odds_data)
    if not selections:
        return
    
    timestamp = datetime.now().isoformat()
    
    # Extract team names from event name
    team_names = []
    if ' v ' in event_name:
        team_names = [t.strip() for t in event_name.split(' v ', 1)]
    elif ' vs ' in event_name.lower():
        sep = ' VS ' if ' VS ' in event_name else ' vs '
        team_names = [t.strip() for t in event_name.split(sep, 1)]
    
    for idx, selection in enumerate(selections):
        selection_id = selection['selection_id']
        back_total = selection['back_total']
        lay_total = selection['lay_total']
        
        # Get team label
        team_label = team_names[idx] if idx < len(team_names) else f"Selection {idx + 1}"
        if idx == 2 and len(team_names) == 2:
            team_label = "Draw"
        
        # Get last snapshot for comparison
        last = get_last_snapshot(market_id, selection_id)
        
        if last:
            # Calculate deltas
            delta_back = back_total - last['back']
            delta_lay = lay_total - last['lay']
            
            # Only update if there's actual movement
            if abs(delta_back) > 0.01 or abs(delta_lay) > 0.01:
                update_cumulative(market_id, selection_id, team_label, delta_back, delta_lay)
                print(f"💰 {event_name[:30]} | {team_label[:15]} | BACK: {delta_back:+.2f} | LAY: {delta_lay:+.2f}")
        
        # Save current snapshot
        save_snapshot(market_id, selection_id, back_total, lay_total, timestamp)

def cleanup_old_data():
    """Clean up old snapshots (keep last 1000)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            DELETE FROM snapshots
            WHERE timestamp NOT IN (
                SELECT timestamp FROM snapshots
                ORDER BY timestamp DESC
                LIMIT 1000
            )
        """)
        conn.commit()
        conn.close()
    except:
        pass

def main():
    """Main tracking loop"""
    print("🚀 Starting Real-time Cumulative Tracker...")
    init_database()
    
    poll_count = 0
    
    while True:
        try:
            # Fetch live events
            events = fetch_live_events()
            print(f"\n📊 Poll #{poll_count + 1} | {datetime.now().strftime('%H:%M:%S')} | {len(events)} live matches")
            
            # Track each market
            for event in events:
                track_market(event)
            
            poll_count += 1
            
            # Cleanup every 100 polls
            if poll_count % 100 == 0:
                cleanup_old_data()
                print("🧹 Cleaned up old snapshots")
            
            # Wait 2 seconds before next poll
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n⛔ Tracker stopped by user")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
