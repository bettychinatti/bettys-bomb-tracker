import json
import time
import requests
from typing import Any, Dict, List, Optional, Tuple

EVENTS_API = "https://api.d99hub.com/api/guest/event_list"
MARKET_API = "https://odds.o99hub.com/ws/getMarketDataNew"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "Origin": "https://gin247.net",
    "Referer": "https://gin247.net/inplay",
    "User-Agent": "Mozilla/5.0",
}


def fetch_events() -> Dict[str, Any]:
    resp = requests.get(EVENTS_API, timeout=10)
    resp.raise_for_status()
    return resp.json()


def market_ids_payload(ids: List[str]) -> Dict[str, List[str]]:
    return {"market_ids[]": ids}


def fetch_market_strings(market_id: str) -> List[str]:
    data = market_ids_payload([market_id])
    resp = requests.post(MARKET_API, headers=HEADERS, data=data, timeout=10)
    resp.raise_for_status()
    out = resp.json()
    return out if isinstance(out, list) else []


def parse_market_string(market_str: str) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    fields = market_str.split('|')
    mid = fields[0]
    total_matched: Optional[float] = None
    if len(fields) > 5:
        try:
            total_matched = float(fields[5])
        except Exception:
            total_matched = None
    runners: List[Dict[str, Any]] = []
    i = 0
    while i < len(fields):
        if fields[i] == 'ACTIVE':
            # selection_id is previous token
            sel_id = None
            if i - 1 >= 0:
                sel_id = fields[i-1]
            i += 1
            pairs: List[Tuple[float, float]] = []
            # read up to 12 tokens (6 pairs) safely
            read = 0
            while i + 1 < len(fields) and read < 12:
                try:
                    odd = float(fields[i])
                    amt = float(fields[i+1])
                    pairs.append((odd, amt))
                    i += 2
                    read += 2
                except Exception:
                    break
            # Map: first 3 pairs are BACK, next 3 are LAY
            back_pairs = pairs[:3]
            lay_pairs = pairs[3:6]
            runners.append({
                "selection_id": sel_id,
                "back": back_pairs,
                "lay": lay_pairs,
            })
        else:
            i += 1
    meta = {"total_matched": total_matched}
    return mid, meta, runners


def team_labels_for_market(market_id: str) -> List[str]:
    try:
        data = fetch_events()
        events = (data or {}).get('data', {}).get('events', [])
        for ev in events:
            if str(ev.get('market_id')) == str(market_id):
                name = ev.get('event_name') or ev.get('name') or ''
                for sep in [' v ', ' vs ', ' VS ', ' Vs ', ' V ']:
                    if sep in name:
                        parts = [p.strip() for p in name.split(sep) if p.strip()]
                        if len(parts) >= 2:
                            return [parts[0], parts[1]]
                return [name.strip(), '']
    except Exception:
        pass
    return ["Team 1", "Team 2"]


def summarize_runner(r: Dict[str, Any]) -> Dict[str, Any]:
    back = r.get('back', [])
    lay = r.get('lay', [])
    total_back = sum(a for _, a in back)
    total_lay = sum(a for _, a in lay)
    best_back = back[0][0] if back else None
    best_lay = lay[0][0] if lay else None
    return {
        "selection_id": r.get('selection_id'),
        "total_back": total_back,
        "total_lay": total_lay,
        "best_back": best_back,
        "best_lay": best_lay,
        "back_top3": back[:3],
        "lay_top3": lay[:3],
    }


def track_market(market_id: str, interval: int = 1, forever: bool = True):
    teams = team_labels_for_market(market_id)
    prev_market: Dict[str, Optional[float]] = {"total_matched": None}
    prev: Dict[str, Dict[str, float]] = {}
    # Session cumulative stats since start (approximating "staked" as gross inflow of available amounts)
    session: Dict[str, Dict[str, float]] = {
        (teams[0] if len(teams) > 0 else 'Team 1'): {
            'in_back': 0.0, 'in_lay': 0.0, 'out_back': 0.0, 'out_lay': 0.0, 'net_back': 0.0, 'net_lay': 0.0
        },
        (teams[1] if len(teams) > 1 else 'Team 2'): {
            'in_back': 0.0, 'in_lay': 0.0, 'out_back': 0.0, 'out_lay': 0.0, 'net_back': 0.0, 'net_lay': 0.0
        },
    }
    print(f"Tracking market_id={market_id} (interval={interval}s, forever={forever})")
    try:
        while True:
            now = time.strftime('%H:%M:%S')
            try:
                arr = fetch_market_strings(market_id)
            except Exception as e:
                print(f"[{now}] ERROR fetching: {e}")
                time.sleep(interval)
                continue
            mstr = next((s for s in arr if isinstance(s, str) and s.startswith(market_id)), None)
            if not mstr:
                print(f"[{now}] No market string for {market_id}")
                time.sleep(interval)
                continue
            mid, meta, runners = parse_market_string(mstr)
            tm = meta.get('total_matched')
            tm_prev = prev_market.get('total_matched')
            tm_delta = None if tm_prev is None or tm is None else (tm - tm_prev)
            tm_str = f"{tm:,.2f}" if isinstance(tm, (int, float)) else "-"
            tm_delta_str = '' if tm_delta is None else f" (Δ {'+' if tm_delta>=0 else ''}{tm_delta:,.2f})"
            print(f"\n[{now}] Market {mid} total_matched={tm_str}{tm_delta_str}")
            if isinstance(tm, (int, float)):
                prev_market['total_matched'] = tm

            # Summaries per runner
            for idx, r in enumerate(runners):
                label = teams[idx] if idx < len(teams) and teams[idx] else f"Runner-{idx+1}"
                s = summarize_runner(r)
                key = label
                pb = prev.get(key, {})
                # deltas
                db = None if 'total_back' not in pb else (s['total_back'] - pb['total_back'])
                dl = None if 'total_lay' not in pb else (s['total_lay'] - pb['total_lay'])
                dbb = None if 'best_back' not in pb else (None if s['best_back'] is None else (s['best_back'] - pb['best_back']))
                dbl = None if 'best_lay' not in pb else (None if s['best_lay'] is None else (s['best_lay'] - pb['best_lay']))

                tb = f"{s['total_back']:.2f}"; tl = f"{s['total_lay']:.2f}"
                dbs = '' if db is None else f" (Δ {'+' if db>=0 else ''}{db:.2f})"
                dls = '' if dl is None else f" (Δ {'+' if dl>=0 else ''}{dl:.2f})"
                bb = '-' if s['best_back'] is None else f"{s['best_back']:.2f}"
                bl = '-' if s['best_lay'] is None else f"{s['best_lay']:.2f}"
                dbbs = '' if dbb is None else f" (Δ {'+' if dbb>=0 else ''}{dbb:.2f})"
                dbls = '' if dbl is None else f" (Δ {'+' if dbl>=0 else ''}{dbl:.2f})"

                back3 = ", ".join([f"{o:.2f}@{a:.2f}" for o,a in s['back_top3']]) or '-'
                lay3 = ", ".join([f"{o:.2f}@{a:.2f}" for o,a in s['lay_top3']]) or '-'

                print(f"  {label}:")
                print(f"    BACK: total={tb}{dbs} | best={bb}{dbbs} | top3={back3}")
                print(f"    LAY:  total={tl}{dls} | best={bl}{dbls} | top3={lay3}")

                prev[key] = {
                    'total_back': float(s['total_back']),
                    'total_lay': float(s['total_lay']),
                    'best_back': float(s['best_back']) if s['best_back'] is not None else pb.get('best_back', 0.0),
                    'best_lay': float(s['best_lay']) if s['best_lay'] is not None else pb.get('best_lay', 0.0),
                }

                # Update session cumulative stats
                if key not in session:
                    session[key] = {'in_back': 0.0, 'in_lay': 0.0, 'out_back': 0.0, 'out_lay': 0.0, 'net_back': 0.0, 'net_lay': 0.0}
                if db is not None:
                    if db > 0:
                        session[key]['in_back'] += db
                    elif db < 0:
                        session[key]['out_back'] += (-db)
                    session[key]['net_back'] += db if db is not None else 0.0
                if dl is not None:
                    if dl > 0:
                        session[key]['in_lay'] += dl
                    elif dl < 0:
                        session[key]['out_lay'] += (-dl)
                    session[key]['net_lay'] += dl if dl is not None else 0.0

            # Session summary line (cumulative since start)
            print("  Session totals since start:", flush=True)
            for label in [teams[0] if len(teams)>0 else 'Team 1', teams[1] if len(teams)>1 else 'Team 2']:
                st = session.get(label, {'in_back':0,'in_lay':0,'out_back':0,'out_lay':0,'net_back':0,'net_lay':0})
                inflow = st['in_back'] + st['in_lay']
                outflow = st['out_back'] + st['out_lay']
                net = st['net_back'] + st['net_lay']
                print(f"    {label}: staked≈{inflow:.2f}, withdrawn≈{outflow:.2f}, net≈{net:.2f} (BACK net {st['net_back']:.2f}, LAY net {st['net_lay']:.2f})", flush=True)

            # Compact one-liner for quick glance
            s1 = session.get(teams[0] if len(teams)>0 else 'Team 1', {'in_back':0,'in_lay':0})
            s2 = session.get(teams[1] if len(teams)>1 else 'Team 2', {'in_back':0,'in_lay':0})
            c1 = (s1.get('in_back',0.0) + s1.get('in_lay',0.0))
            c2 = (s2.get('in_back',0.0) + s2.get('in_lay',0.0))
            print(f"  CUMULATIVE (since start): { (teams[0] if len(teams)>0 else 'Team 1') }={c1:.2f} | { (teams[1] if len(teams)>1 else 'Team 2') }={c2:.2f}", flush=True)

            time.sleep(interval)
            if not forever:
                break
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Team-wise live market tracker (amounts & odds with deltas)")
    parser.add_argument('--market-id', dest='market_id', help='Market ID to track (e.g., 1.249073694)')
    parser.add_argument('--event-id', dest='event_id', type=int, help='Event ID to resolve to market ID (e.g., 34841379)')
    parser.add_argument('--interval', dest='interval', type=int, default=1, help='Polling interval (seconds)')
    parser.add_argument('--once', action='store_true', help='Run a single iteration and exit')
    args = parser.parse_args()

    mid: Optional[str] = args.market_id
    if not mid and args.event_id:
        data = fetch_events()
        events = (data or {}).get('data', {}).get('events', [])
        match = next((e for e in events if int(e.get('event_id', -1)) == args.event_id), None)
        if match:
            mid = str(match.get('market_id'))
    if not mid:
        raise SystemExit('Provide --market-id or --event-id to track')

    track_market(mid, interval=args.interval, forever=(not args.once))
