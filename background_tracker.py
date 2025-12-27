"""
Real-time Cumulative Market Tracker
Polls APIs every 100ms for ultra-precise tracking
"""
import time
import requests
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Database path - Use Render persistent disk at /data
if Path('/data').exists():
    DB_PATH = Path('/data') / 'tracker.db'
else:
    DB_PATH = Path(__file__).parent / 'data' / 'tracker.db'
    DB_PATH.parent.mkdir(exist_ok=True)

# API Configuration
EVENTS_API = "https://api.d99exch.com/api/guest/event_list"
ODDS_API = "https://odds.o99exch.com/ws/getMarketDataNew"
HEADERS = {
    "accept": "application/json",
    "origin": "https://d99exch.com",
    "referer": "https://d99exch.com/"
}

# Tracking - 100ms for ultra-precise tracking
POLL_INTERVAL = 0.1
SPORTS_TO_TRACK = [4, 1, 2, 7]  # Cricket, Soccer, Tennis, Horse Racing

def init_database():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Drop old table if it exists to ensure correct schema
        cursor.execute("DROP TABLE IF EXISTS cumulative")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cumulative (
                market_id TEXT NOT NULL,
                selection_id TEXT NOT NULL,
                team_label TEXT NOT NULL,
                in_back REAL DEFAULT 0,
                in_lay REAL DEFAULT 0,
                out_back REAL DEFAULT 0,
                out_lay REAL DEFAULT 0,
                net_back REAL DEFAULT 0,
                net_lay REAL DEFAULT 0,
                last_back_stake REAL DEFAULT 0,
                last_lay_stake REAL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (market_id, selection_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cumulative_market ON cumulative(market_id)")
        conn.commit()
        conn.close()
        print(f"✅ Database initialized (fresh schema): {DB_PATH}")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def fetch_live_events():
    """Fetch live events from all tracked sports"""
    all_events = []
    for sport_id in SPORTS_TO_TRACK:
        try:
            url = f"{EVENTS_API}?sport_id={sport_id}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("data", {}).get("events", [])
                live_events = [e for e in events if e.get("in_play") == 1]
                all_events.extend(live_events)
        except:
            pass
    return all_events

def parse_market_data(raw_data):
    """Parse pipe-delimited market data"""
    try:
        parts = raw_data.split('~')
        if len(parts) < 8:
            return None
        
        market_id = parts[0]
        selections = []
        
        i = 7
        while i < len(parts):
            if '|' in parts[i]:
                runner_parts = parts[i].split('|')
                if len(runner_parts) >= 11:
                    selection_id = runner_parts[0]
                    team_label = runner_parts[10] if len(runner_parts) > 10 else "Unknown"
                    
                    back_stakes = []
                    for j in range(1, 4):
                        try:
                            back_stakes.append(float(runner_parts[j]) if runner_parts[j] else 0.0)
                        except:
                            back_stakes.append(0.0)
                    
                    lay_stakes = []
                    for j in range(4, 7):
                        try:
                            lay_stakes.append(float(runner_parts[j]) if runner_parts[j] else 0.0)
                        except:
                            lay_stakes.append(0.0)
                    
                    selections.append({
                        'selection_id': selection_id,
                        'team': team_label,
                        'back_stake': sum(back_stakes),
                        'lay_stake': sum(lay_stakes)
                    })
            i += 1
        
        if selections:
            return {'market_id': market_id, 'selections': selections}
    except:
        pass
    return None

def fetch_market_odds(market_id, sport_id=4):
    """Fetch odds for a market"""
    try:
        url = f"{ODDS_API}?marketId={market_id}&eventTypeId={sport_id}"
        resp = requests.get(url, headers=HEADERS, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success") and data.get("data"):
                return parse_market_data(data["data"])
    except:
        pass
    return None

def get_last_cumulative(market_id, selection_id):
    """Get last cumulative record"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute("""
            SELECT in_back, in_lay, out_back, out_lay, last_back_stake, last_lay_stake
            FROM cumulative
            WHERE market_id = ? AND selection_id = ?
        """, (market_id, selection_id))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'in_back': row[0], 'in_lay': row[1],
                'out_back': row[2], 'out_lay': row[3],
                'last_back_stake': row[4], 'last_lay_stake': row[5]
            }
    except:
        pass
    return None

def update_cumulative(market_id, selection_id, team_label, current_back, current_lay, timestamp):
    """Update cumulative tracking"""
    try:
        last = get_last_cumulative(market_id, selection_id)
        
        if last:
            delta_back = current_back - last['last_back_stake']
            delta_lay = current_lay - last['last_lay_stake']
            
            in_back = last['in_back']
            in_lay = last['in_lay']
            out_back = last['out_back']
            out_lay = last['out_lay']
            
            if delta_back > 0:
                in_back += delta_back
            elif delta_back < 0:
                out_back += abs(delta_back)
            
            if delta_lay > 0:
                in_lay += delta_lay
            elif delta_lay < 0:
                out_lay += abs(delta_lay)
            
            if abs(delta_back) > 100 or abs(delta_lay) > 100:
                print(f"💰 {team_label}: ΔBack={delta_back:+.2f}, ΔLay={delta_lay:+.2f}")
        else:
            in_back = current_back
            in_lay = current_lay
            out_back = 0.0
            out_lay = 0.0
            print(f"🆕 {team_label}: Back={current_back:.2f}, Lay={current_lay:.2f}")
        
        net_back = in_back - out_back
        net_lay = in_lay - out_lay
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT OR REPLACE INTO cumulative 
            (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, 
             net_back, net_lay, last_back_stake, last_lay_stake, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (market_id, selection_id, team_label, in_back, in_lay, out_back, out_lay, 
              net_back, net_lay, current_back, current_lay, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ Update error: {e}")

def track_market(market_id, sport_id=4):
    """Track a market"""
    market_data = fetch_market_odds(market_id, sport_id)
    if not market_data:
        return False
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    for selection in market_data['selections']:
        update_cumulative(
            market_id, 
            selection['selection_id'], 
            selection['team'],
            selection['back_stake'], 
            selection['lay_stake'], 
            timestamp
        )
    
    return True

def main():
    """Main loop"""
    print("=" * 60)
    print("🚀 ULTRA-PRECISE TRACKER (100ms polling)")
    print(f"📂 Database: {DB_PATH}")
    print("=" * 60)
    
    if not init_database():
        return
    
    tracked_markets = {}
    poll_count = 0
    
    while True:
        try:
            loop_start = time.time()
            events = fetch_live_events()
            current_markets = {}
            
            for event in events:
                market_id = event.get("market_id")
                event_name = event.get("name", event.get("event_name", "Unknown"))
                sport_id = event.get("sport_id", 4)  # Get sport_id from event
                
                if market_id:
                    current_markets[market_id] = event_name
                    
                    if market_id not in tracked_markets:
                        sport_name = {1: "⚽", 2: "🎾", 4: "🏏", 7: "🏇"}.get(sport_id, "🎯")
                        print(f"🆕 {sport_name} {event_name} ({market_id})")
                        tracked_markets[market_id] = event_name
                    
                    track_market(market_id, sport_id)
            
            finished = set(tracked_markets.keys()) - set(current_markets.keys())
            for market_id in finished:
                print(f"🏁 {tracked_markets[market_id]}")
                del tracked_markets[market_id]
            
            poll_count += 1
            if poll_count % 50 == 0:
                print(f"✅ Poll #{poll_count} | {len(tracked_markets)} matches")
            
            elapsed = time.time() - loop_start
            time.sleep(max(0, POLL_INTERVAL - elapsed))
            
        except KeyboardInterrupt:
            print("\n⏹️  Stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
