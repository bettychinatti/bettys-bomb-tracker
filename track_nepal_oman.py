import requests
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

MARKET_API = "https://odds.o99hub.com/ws/getMarketDataNew"
EVENTS_API = "https://api.d99hub.com/api/guest/event_list"
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "Origin": "https://gin247.net",
    "Referer": "https://gin247.net/inplay",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
}

# Helper: parse a single market string into runners (selection_id, pairs of (odd, liquidity))
def parse_market_string(market_str: str):
    fields = market_str.split('|')
    market_id = fields[0]
    # Market-level totals (based on observed key mapping): index 5 => total_matched
    total_matched = None
    if len(fields) > 5:
        try:
            total_matched = float(fields[5])
        except Exception:
            total_matched = None
    runners: List[Dict[str, Any]] = []
    i = 0
    while i < len(fields):
        if fields[i] == 'ACTIVE':
            # Try to read selection_id from previous token if numeric
            sel_id = None
            if i - 1 >= 0:
                try:
                    _ = int(fields[i-1])
                    sel_id = fields[i-1]
                except Exception:
                    sel_id = None
            i += 1
            pairs: List[Tuple[float, float]] = []
            # Read pairs of (odd, liquidity) until we hit a non-float token
            while i + 1 < len(fields):
                try:
                    odd = float(fields[i])
                    liq = float(fields[i+1])
                    pairs.append((odd, liq))
                    i += 2
                except Exception:
                    break
            runners.append({
                'selection_id': sel_id,
                'pairs': pairs,
        })
        else:
            i += 1
    return market_id, runners, {"total_matched": total_matched}


def split_pairs_into_lay_back(pairs: List[Tuple[float, float]]):
    """
    Split combined (odd, amount) ladder into (lay, back).
    Observed mapping (gin247): first 3 pairs are BACK, next 3 are LAY.
    Heuristics:
    1) If we have 6 or more pairs: BACK = pairs[:3], LAY = pairs[3:6].
    2) If even length (>0): BACK = first half, LAY = second half.
    3) Else pivot at min odd: BACK = left (lower odds region), LAY = right.
    Returns (lay_pairs, back_pairs).
    """
    n = len(pairs)
    if n >= 6:
        back = pairs[:3]
        lay = pairs[3:6]
        return lay, back
    if n % 2 == 0 and n > 0:
        mid = n // 2
        back = pairs[:mid]
        lay = pairs[mid:]
        return lay, back
    # Pivot heuristic
    if n >= 3:
        odds = [p[0] for p in pairs]
        try:
            pivot_idx = odds.index(min(odds))
            back = pairs[:pivot_idx+1]
            lay = pairs[pivot_idx+1:]
            return lay, back
        except Exception:
            pass
    return [], pairs


def summarize_runners(runners: List[Dict[str, Any]]):
    summary = []
    for idx, r in enumerate(runners):
        pairs = r['pairs']
        lay_pairs, back_pairs = split_pairs_into_lay_back(pairs)
        total_liq_lay = sum(p[1] for p in lay_pairs)
        total_liq_back = sum(p[1] for p in back_pairs)
        best_lay = lay_pairs[0][0] if lay_pairs else None
        best_back = back_pairs[0][0] if back_pairs else None
        top3_lay = lay_pairs[:3]
        top3_back = back_pairs[:3]
        summary.append({
            'label': f"Runner-{idx+1}" + (f" ({r['selection_id']})" if r.get('selection_id') else ''),
            'selection_id': r.get('selection_id'),
            'total_liquidity_lay': total_liq_lay,
            'total_liquidity_back': total_liq_back,
            'best_lay': best_lay,
            'best_back': best_back,
            'top3_lay': top3_lay,
            'top3_back': top3_back,
        })
    return summary


def fetch_market_data_single(market_id: str):
    # API expects repeated market_ids[] fields; for single id we still use that key
    data = {"market_ids[]": market_id}
    resp = requests.post(MARKET_API, headers=HEADERS, data=data, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_team_labels_for_market(market_id: str) -> List[str]:
    """
    Resolve team names from the events feed, based on market_id. Returns [team1, team2].
    We split event name on common separators (" v ", " vs ") and fallback to full name.
    Assumption: runner order aligns with [team1, team2].
    """
    try:
        r = requests.get(EVENTS_API, timeout=10)
        r.raise_for_status()
        data = r.json()
        events = (data or {}).get('data', {}).get('events', [])
        for ev in events:
            if str(ev.get('market_id')) == str(market_id):
                name = ev.get('event_name') or ev.get('name') or ''
                s = name.strip()
                # normalize
                for sep in [' v ', ' vs ', ' VS ', ' Vs ', ' V ']:
                    if sep in s:
                        parts = [p.strip() for p in s.split(sep) if p.strip()]
                        if len(parts) >= 2:
                            return [parts[0], parts[1]]
                # fallback: return the whole as first team and empty second
                return [s, '']
    except Exception:
        pass
    return ["Team 1", "Team 2"]


def tracker(market_id: str, interval_sec: int = 3, iterations: int = 10):
    prev: Dict[str, Dict[str, float]] = {}
    prev_market: Dict[str, Optional[float]] = {"total_matched": None}  # type: ignore[name-defined]
    teams = get_team_labels_for_market(market_id)
    # Map index -> team label
    def label_for_index(idx: int, fallback: str) -> str:
        if idx < len(teams) and teams[idx]:
            return teams[idx]
        return fallback
    print(f"Tracking market_id={market_id} (interval={interval_sec}s, iterations={iterations})")
    for k in range(iterations):
        ts = datetime.now().strftime('%H:%M:%S')
        try:
            data = fetch_market_data_single(market_id)
        except Exception as e:
            print(f"[{ts}] ERROR fetching market: {e}")
            time.sleep(interval_sec)
            continue

        if not data:
            print(f"[{ts}] No data returned")
            time.sleep(interval_sec)
            continue

        # Find our market string; response is typically an array
        market_str = None
        if isinstance(data, list):
            for s in data:
                if isinstance(s, str) and s.startswith(market_id):
                    market_str = s
                    break
        elif isinstance(data, dict):
            # Fallback if API shape changes
            market_str = data.get('data') if isinstance(data.get('data'), str) else None

        if not market_str:
            print(f"[{ts}] Market string for {market_id} not found in response of len={len(data) if isinstance(data, list) else 'dict'}")
            time.sleep(interval_sec)
            continue

        mid, runners, meta = parse_market_string(market_str)
        summary = summarize_runners(runners)
        tm = meta.get('total_matched') if isinstance(meta, dict) else None

        # Market-level matched total and delta
        tm_prev = prev_market.get('total_matched')
        tm_delta = None if tm_prev is None or tm is None else (tm - tm_prev)
        tm_str = f"{tm:,.2f}" if isinstance(tm, (int, float)) else "-"
        tm_delta_str = '' if tm_delta is None else (f" (Δ {'+' if tm_delta>=0 else ''}{tm_delta:,.2f})")

        print(f"\n[{ts}] Market {mid} updates: total_matched={tm_str}{tm_delta_str}")
        if isinstance(tm, (int, float)):
            prev_market['total_matched'] = tm
        for idx, item in enumerate(summary):
            # Override label with team name when available
            display_label = label_for_index(idx, item['label'])
            key = display_label
            lay_liq = item['total_liquidity_lay']
            back_liq = item['total_liquidity_back']
            best_lay = item['best_lay']
            best_back = item['best_back']
            top3_lay = item.get('top3_lay', [])
            top3_back = item.get('top3_back', [])
            top3_lay_str = ", ".join([f"{o:.2f}@{a:.2f}" for o, a in top3_lay]) if top3_lay else "-"
            top3_back_str = ", ".join([f"{o:.2f}@{a:.2f}" for o, a in top3_back]) if top3_back else "-"

            prev_lay_liq = prev.get(key, {}).get('lay_liq')
            prev_back_liq = prev.get(key, {}).get('back_liq')
            prev_best_lay = prev.get(key, {}).get('best_lay')
            prev_best_back = prev.get(key, {}).get('best_back')

            d_lay_liq = None if prev_lay_liq is None else (lay_liq - prev_lay_liq)
            d_back_liq = None if prev_back_liq is None else (back_liq - prev_back_liq)
            d_best_lay = None if prev_best_lay is None else (None if best_lay is None else (best_lay - prev_best_lay))
            d_best_back = None if prev_best_back is None else (None if best_back is None else (best_back - prev_best_back))

            lay_delta = '' if d_lay_liq is None else (f" (Δ {'+' if d_lay_liq>=0 else ''}{d_lay_liq:.2f})")
            back_delta = '' if d_back_liq is None else (f" (Δ {'+' if d_back_liq>=0 else ''}{d_back_liq:.2f})")
            best_lay_delta = '' if d_best_lay is None else (f" (Δ {'+' if d_best_lay>=0 else ''}{d_best_lay:.2f})")
            best_back_delta = '' if d_best_back is None else (f" (Δ {'+' if d_best_back>=0 else ''}{d_best_back:.2f})")

            lay_liq_str = f"{lay_liq:.2f}" if lay_liq is not None else "-"
            back_liq_str = f"{back_liq:.2f}" if back_liq is not None else "-"
            best_lay_str = f"{best_lay:.2f}" if best_lay is not None else "-"
            best_back_str = f"{best_back:.2f}" if best_back is not None else "-"

            print(f"  {key}:")
            print(f"    LAY:  total={lay_liq_str}{lay_delta} | best={best_lay_str}{best_lay_delta} | top3={top3_lay_str}")
            print(f"    BACK: total={back_liq_str}{back_delta} | best={best_back_str}{best_back_delta} | top3={top3_back_str}")

            prev[key] = {
                'lay_liq': float(lay_liq) if lay_liq is not None else 0.0,
                'back_liq': float(back_liq) if back_liq is not None else 0.0,
                'best_lay': float(best_lay) if best_lay is not None else (float(prev_best_lay) if isinstance(prev_best_lay, (int, float)) else 0.0),
                'best_back': float(best_back) if best_back is not None else (float(prev_best_back) if isinstance(prev_best_back, (int, float)) else 0.0),
            }

        time.sleep(interval_sec)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Live market tracker for Oman vs Nepal (or any market_id)")
    parser.add_argument("--market-id", dest="market_id", default="1.249053452", help="Market ID to track")
    parser.add_argument("--interval", dest="interval", type=int, default=3, help="Polling interval in seconds")
    parser.add_argument("--iterations", dest="iterations", type=int, default=10, help="Number of iterations (ignored in --forever mode)")
    parser.add_argument("--forever", action="store_true", help="Run until stopped (Ctrl+C)")
    args = parser.parse_args()

    if args.forever:
        try:
            print(f"Running forever. Press Ctrl+C to stop. market_id={args.market_id}, interval={args.interval}s")
            while True:
                tracker(market_id=args.market_id, interval_sec=args.interval, iterations=1)
        except KeyboardInterrupt:
            print("\nStopped by user.")
    else:
        tracker(market_id=args.market_id, interval_sec=args.interval, iterations=args.iterations)
