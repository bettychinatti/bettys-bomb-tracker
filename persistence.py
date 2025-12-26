import sqlite3
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Use /data mount path on Render.com (persistent disk), fallback to local ./data
if os.path.exists('/data'):
    DB_PATH = Path('/data') / 'tracker.db'
else:
    DB_PATH = Path(__file__).parent / 'data' / 'tracker.db'

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS markets (
  market_id TEXT PRIMARY KEY,
  event_name TEXT,
  sport TEXT,
  started_at INTEGER
);
CREATE TABLE IF NOT EXISTS teams (
  market_id TEXT,
  team_label TEXT,
  PRIMARY KEY (market_id, team_label)
);
CREATE TABLE IF NOT EXISTS cumulative (
  market_id TEXT,
  team_label TEXT,
  in_back REAL DEFAULT 0,
  in_lay REAL DEFAULT 0,
  out_back REAL DEFAULT 0,
  out_lay REAL DEFAULT 0,
  net_back REAL DEFAULT 0,
  net_lay REAL DEFAULT 0,
  updated_at INTEGER,
  PRIMARY KEY (market_id, team_label)
);
CREATE TABLE IF NOT EXISTS prev_snapshot (
  market_id TEXT PRIMARY KEY,
  payload TEXT,
  total_matched REAL,
  updated_at INTEGER
);
"""

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def upsert_market(conn: sqlite3.Connection, market_id: str, event_name: Optional[str], sport: Optional[str], started_at: Optional[int]):
    conn.execute(
        "INSERT INTO markets(market_id, event_name, sport, started_at) VALUES(?,?,?,?)\n         ON CONFLICT(market_id) DO UPDATE SET event_name=excluded.event_name, sport=excluded.sport, started_at=COALESCE(markets.started_at, excluded.started_at)",
        (market_id, event_name, sport, started_at)
    )


def upsert_team_labels(conn: sqlite3.Connection, market_id: str, labels: Tuple[str, str]):
    for label in labels:
        conn.execute(
            "INSERT INTO teams(market_id, team_label) VALUES(?,?) ON CONFLICT(market_id, team_label) DO NOTHING",
            (market_id, label)
        )


def increment_cumulative(conn: sqlite3.Connection, market_id: str, team_label: str, db: float, dl: float, updated_at: int):
    # Read existing
    cur = conn.execute("SELECT in_back, in_lay, out_back, out_lay, net_back, net_lay FROM cumulative WHERE market_id=? AND team_label=?", (market_id, team_label))
    row = cur.fetchone()
    if row is None:
        in_back = max(db, 0)
        out_back = max(-db, 0)
        net_back = db
        in_lay = max(dl, 0)
        out_lay = max(-dl, 0)
        net_lay = dl
        conn.execute("INSERT INTO cumulative(market_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                     (market_id, team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at))
    else:
        in_back, in_lay, out_back, out_lay, net_back, net_lay = row[0], row[1], row[2], row[3], row[4], row[5]
        in_back += max(db, 0)
        out_back += max(-db, 0)
        net_back += db
        in_lay += max(dl, 0)
        out_lay += max(-dl, 0)
        net_lay += dl
        conn.execute("UPDATE cumulative SET in_back=?, in_lay=?, out_back=?, out_lay=?, net_back=?, net_lay=?, updated_at=? WHERE market_id=? AND team_label=?",
                     (in_back, in_lay, out_back, out_lay, net_back, net_lay, updated_at, market_id, team_label))


def get_cumulative(conn: sqlite3.Connection, market_id: str) -> Dict[str, Dict[str, float]]:
    cur = conn.execute("SELECT team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay FROM cumulative WHERE market_id=?", (market_id,))
    result: Dict[str, Dict[str, float]] = {}
    for team_label, in_back, in_lay, out_back, out_lay, net_back, net_lay in cur.fetchall():
        result[team_label] = {
            'in_back': in_back or 0.0,
            'in_lay': in_lay or 0.0,
            'out_back': out_back or 0.0,
            'out_lay': out_lay or 0.0,
            'net_back': net_back or 0.0,
            'net_lay': net_lay or 0.0,
        }
    return result

