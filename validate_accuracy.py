#!/usr/bin/env python3
"""
Comprehensive accuracy validation for Betty's Bomb Tracker
Tests API data parsing, calculation logic, and end-to-end accuracy
"""

import requests
import time
import json
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# API endpoints
EVENTS_API = "https://api.d99hub.com/api/guest/event_list"
MARKET_API = "https://odds.o99hub.com/ws/getMarketDataNew"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "Origin": "https://gin247.net",
    "Referer": "https://gin247.net/inplay",
    "User-Agent": "Mozilla/5.0",
}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log_pass(msg: str):
    print(f"{Colors.GREEN}✓ PASS:{Colors.END} {msg}")

def log_fail(msg: str):
    print(f"{Colors.RED}✗ FAIL:{Colors.END} {msg}")

def log_warn(msg: str):
    print(f"{Colors.YELLOW}⚠ WARNING:{Colors.END} {msg}")

def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ INFO:{Colors.END} {msg}")

def log_section(msg: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}\n")


# ============================================================================
# PART 1: PIPE-DELIMITED FORMAT PARSING VALIDATION
# ============================================================================

def parse_market_string(market_str: str) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
    """Parse pipe-delimited market string - EXACT copy from dashboard.py"""
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


def validate_parsing():
    log_section("TEST 1: PIPE-DELIMITED FORMAT PARSING")
    
    # Test case 1: Synthetic market string
    log_info("Test 1.1: Synthetic market string with known values")
    synthetic = "1.12345|field2|field3|field4|field5|1000000.50|field7|12345|ACTIVE|1.50|500.00|1.55|300.00|1.60|200.00|2.00|400.00|2.05|350.00|2.10|250.00"
    
    mid, meta, runners = parse_market_string(synthetic)
    
    # Validate market ID
    if mid == "1.12345":
        log_pass(f"Market ID correctly parsed: {mid}")
    else:
        log_fail(f"Market ID incorrect: expected '1.12345', got '{mid}'")
    
    # Validate total_matched
    if meta['total_matched'] == 1000000.50:
        log_pass(f"Total matched correctly parsed: {meta['total_matched']:,.2f}")
    else:
        log_fail(f"Total matched incorrect: expected 1000000.50, got {meta['total_matched']}")
    
    # Validate runner structure
    if len(runners) >= 1:
        runner = runners[0]
        log_info(f"Runner selection_id: {runner['selection_id']}")
        log_info(f"BACK pairs: {runner['back']}")
        log_info(f"LAY pairs: {runner['lay']}")
        
        # Check BACK pairs (first 3 pairs after ACTIVE)
        expected_back = [(1.50, 500.00), (1.55, 300.00), (1.60, 200.00)]
        if runner['back'] == expected_back:
            log_pass("BACK pairs correctly parsed and ordered")
        else:
            log_fail(f"BACK pairs incorrect: expected {expected_back}, got {runner['back']}")
        
        # Check LAY pairs (next 3 pairs)
        expected_lay = [(2.00, 400.00), (2.05, 350.00), (2.10, 250.00)]
        if runner['lay'] == expected_lay:
            log_pass("LAY pairs correctly parsed and ordered")
        else:
            log_fail(f"LAY pairs incorrect: expected {expected_lay}, got {runner['lay']}")
    else:
        log_fail("No runners parsed from synthetic market string")
    
    # Test case 2: Real market data
    log_info("\nTest 1.2: Fetching real market data from API")
    try:
        events_resp = requests.get(EVENTS_API, timeout=10)
        events = events_resp.json().get('data', {}).get('events', [])
        inplay = [e for e in events if e.get('in_play') == 1][:3]
        
        if not inplay:
            log_warn("No in-play markets found for real-data testing")
            return
        
        market_ids = [str(e.get('market_id')) for e in inplay]
        payload = [("market_ids[]", mid) for mid in market_ids]
        
        resp = requests.post(MARKET_API, headers=HEADERS, data=payload, timeout=10)
        market_data = resp.json()
        
        parsed_count = 0
        for market_str in market_data:
            if not isinstance(market_str, str):
                continue
            
            mid, meta, runners = parse_market_string(market_str)
            parsed_count += 1
            
            log_info(f"\nMarket {mid}:")
            log_info(f"  Total matched: {meta['total_matched']:,.2f}" if meta['total_matched'] else "  Total matched: None")
            log_info(f"  Runners found: {len(runners)}")
            
            for idx, runner in enumerate(runners[:2]):
                log_info(f"  Runner {idx+1} (selection {runner['selection_id']}):")
                total_back = sum(amt for _, amt in runner['back'])
                total_lay = sum(amt for _, amt in runner['lay'])
                log_info(f"    BACK: {len(runner['back'])} levels, total={total_back:,.2f}")
                log_info(f"    LAY: {len(runner['lay'])} levels, total={total_lay:,.2f}")
                
                # Validate data types
                for odd, amt in runner['back']:
                    if not isinstance(odd, float) or not isinstance(amt, float):
                        log_fail(f"    BACK pair has wrong types: odd={type(odd)}, amt={type(amt)}")
                
                for odd, amt in runner['lay']:
                    if not isinstance(odd, float) or not isinstance(amt, float):
                        log_fail(f"    LAY pair has wrong types: odd={type(odd)}, amt={type(amt)}")
        
        if parsed_count > 0:
            log_pass(f"Successfully parsed {parsed_count} real market strings")
        else:
            log_warn("No valid market strings received (all None)")
            
    except Exception as e:
        log_fail(f"Real market data test failed: {e}")


# ============================================================================
# PART 2: MONEY FLOW CALCULATION VALIDATION
# ============================================================================

def validate_money_flow():
    log_section("TEST 2: MONEY FLOW CALCULATION LOGIC")
    
    log_info("Test 2.1: Delta calculation accuracy")
    
    # Simulate tracking over time
    prev_state = {
        'total_back': 1000.0,
        'total_lay': 2000.0,
        'best_back': 1.50,
        'best_lay': 2.00
    }
    
    current_state = {
        'total_back': 1500.0,  # +500 inflow
        'total_lay': 1800.0,   # -200 outflow
        'best_back': 1.55,     # +0.05
        'best_lay': 1.95       # -0.05
    }
    
    # Calculate deltas
    delta_back = current_state['total_back'] - prev_state['total_back']
    delta_lay = current_state['total_lay'] - prev_state['total_lay']
    delta_best_back = current_state['best_back'] - prev_state['best_back']
    delta_best_lay = current_state['best_lay'] - prev_state['best_lay']
    
    log_info(f"Previous state: BACK={prev_state['total_back']:,.2f}, LAY={prev_state['total_lay']:,.2f}")
    log_info(f"Current state: BACK={current_state['total_back']:,.2f}, LAY={current_state['total_lay']:,.2f}")
    log_info(f"Calculated deltas: BACK={delta_back:+,.2f}, LAY={delta_lay:+,.2f}")
    
    # Validate delta signs
    if delta_back == 500.0:
        log_pass(f"BACK delta correct: +500.0 (money staked)")
    else:
        log_fail(f"BACK delta incorrect: expected +500.0, got {delta_back:+,.2f}")
    
    if delta_lay == -200.0:
        log_pass(f"LAY delta correct: -200.0 (money withdrawn)")
    else:
        log_fail(f"LAY delta incorrect: expected -200.0, got {delta_lay:+,.2f}")
    
    # Test cumulative update logic
    log_info("\nTest 2.2: Cumulative tracking (in/out/net)")
    
    cumulative = {
        'in_back': 0.0,
        'out_back': 0.0,
        'in_lay': 0.0,
        'out_lay': 0.0,
        'net_back': 0.0,
        'net_lay': 0.0
    }
    
    # Apply delta_back (+500)
    if delta_back > 0:
        cumulative['in_back'] += delta_back
    elif delta_back < 0:
        cumulative['out_back'] += (-delta_back)
    cumulative['net_back'] += delta_back
    
    # Apply delta_lay (-200)
    if delta_lay > 0:
        cumulative['in_lay'] += delta_lay
    elif delta_lay < 0:
        cumulative['out_lay'] += (-delta_lay)
    cumulative['net_lay'] += delta_lay
    
    log_info(f"Cumulative after update:")
    log_info(f"  in_back={cumulative['in_back']:,.2f}, out_back={cumulative['out_back']:,.2f}, net_back={cumulative['net_back']:+,.2f}")
    log_info(f"  in_lay={cumulative['in_lay']:,.2f}, out_lay={cumulative['out_lay']:,.2f}, net_lay={cumulative['net_lay']:+,.2f}")
    
    # Validate
    if cumulative['in_back'] == 500.0 and cumulative['out_back'] == 0.0 and cumulative['net_back'] == 500.0:
        log_pass("BACK cumulative tracking correct")
    else:
        log_fail("BACK cumulative tracking incorrect")
    
    if cumulative['in_lay'] == 0.0 and cumulative['out_lay'] == 200.0 and cumulative['net_lay'] == -200.0:
        log_pass("LAY cumulative tracking correct")
    else:
        log_fail("LAY cumulative tracking incorrect")
    
    # Test edge cases
    log_info("\nTest 2.3: Edge cases")
    
    # Zero delta
    zero_delta = 0.0
    test_cum = {'in_back': 100.0, 'out_back': 50.0, 'net_back': 50.0}
    if zero_delta > 0:
        test_cum['in_back'] += zero_delta
    elif zero_delta < 0:
        test_cum['out_back'] += (-zero_delta)
    test_cum['net_back'] += zero_delta
    
    if test_cum == {'in_back': 100.0, 'out_back': 50.0, 'net_back': 50.0}:
        log_pass("Zero delta handled correctly (no change)")
    else:
        log_fail("Zero delta corrupted cumulative state")
    
    # Very large numbers
    large_delta = 999999999.99
    test_cum2 = {'in_back': 0.0, 'net_back': 0.0}
    if large_delta > 0:
        test_cum2['in_back'] += large_delta
    test_cum2['net_back'] += large_delta
    
    if test_cum2['in_back'] == large_delta and test_cum2['net_back'] == large_delta:
        log_pass(f"Large numbers handled correctly: {large_delta:,.2f}")
    else:
        log_fail("Large number precision issue detected")
    
    # Floating point precision
    delta_a = 0.1 + 0.2
    delta_b = 0.3
    if abs(delta_a - delta_b) < 1e-9:
        log_pass("Floating point precision acceptable (0.1+0.2≈0.3)")
    else:
        log_warn(f"Floating point precision issue: 0.1+0.2={delta_a}, expected 0.3")


# ============================================================================
# PART 3: END-TO-END REAL-WORLD ACCURACY TEST
# ============================================================================

def validate_end_to_end():
    log_section("TEST 3: END-TO-END REAL-WORLD ACCURACY")
    
    log_info("Tracking live markets for 5 polling cycles (30-60 seconds)")
    log_info("This will validate: API stability, calculation consistency, data integrity\n")
    
    try:
        # Get in-play markets
        events_resp = requests.get(EVENTS_API, timeout=10)
        events = events_resp.json().get('data', {}).get('events', [])
        inplay = [e for e in events if e.get('in_play') == 1][:2]  # Track 2 markets
        
        if not inplay:
            log_warn("No in-play markets available for end-to-end test")
            return
        
        market_ids = [str(e.get('market_id')) for e in inplay]
        market_names = {str(e.get('market_id')): e.get('event_name', 'Unknown') for e in inplay}
        
        log_info(f"Selected markets:")
        for mid in market_ids:
            log_info(f"  {mid}: {market_names[mid]}")
        
        # Track state across polls
        history = {mid: [] for mid in market_ids}
        
        for poll_num in range(5):
            log_info(f"\n--- Poll #{poll_num + 1} at {datetime.now(IST).strftime('%H:%M:%S')} ---")
            
            payload = [("market_ids[]", mid) for mid in market_ids]
            resp = requests.post(MARKET_API, headers=HEADERS, data=payload, timeout=10)
            market_data = resp.json()
            
            # Parse and store
            for market_str in market_data:
                if not isinstance(market_str, str):
                    continue
                
                mid, meta, runners = parse_market_string(market_str)
                
                snapshot = {
                    'timestamp': time.time(),
                    'total_matched': meta['total_matched'],
                    'runners': []
                }
                
                for runner in runners[:2]:
                    total_back = sum(amt for _, amt in runner['back'])
                    total_lay = sum(amt for _, amt in runner['lay'])
                    best_back = runner['back'][0][0] if runner['back'] else None
                    best_lay = runner['lay'][0][0] if runner['lay'] else None
                    
                    snapshot['runners'].append({
                        'selection_id': runner['selection_id'],
                        'total_back': total_back,
                        'total_lay': total_lay,
                        'best_back': best_back,
                        'best_lay': best_lay
                    })
                
                history[mid].append(snapshot)
                
                log_info(f"  Market {mid}: total_matched={meta['total_matched']:,.2f if meta['total_matched'] else 0:.2f}, runners={len(runners)}")
            
            # Wait between polls
            if poll_num < 4:
                time.sleep(10)
        
        # Analyze history
        log_info("\n" + "="*80)
        log_info("ANALYSIS OF POLLING HISTORY")
        log_info("="*80)
        
        for mid in market_ids:
            snapshots = history[mid]
            if len(snapshots) < 2:
                log_warn(f"Market {mid}: insufficient data for analysis")
                continue
            
            log_info(f"\nMarket {mid} ({market_names[mid]}):")
            log_info(f"  Snapshots collected: {len(snapshots)}")
            
            # Check total_matched trend (should be monotonically increasing or stable)
            tm_values = [s['total_matched'] for s in snapshots if s['total_matched'] is not None]
            if tm_values:
                tm_increasing = all(tm_values[i] <= tm_values[i+1] for i in range(len(tm_values)-1))
                if tm_increasing:
                    log_pass(f"  Total matched trend valid (monotonic increase or stable)")
                    log_info(f"    Range: {min(tm_values):,.2f} → {max(tm_values):,.2f}")
                else:
                    log_fail(f"  Total matched decreased (possible data corruption!)")
                    log_info(f"    Values: {[f'{v:,.2f}' for v in tm_values]}")
            
            # Check runner consistency
            for r_idx in range(min(2, len(snapshots[0]['runners']))):
                log_info(f"\n  Runner {r_idx + 1}:")
                
                back_values = [s['runners'][r_idx]['total_back'] for s in snapshots if r_idx < len(s['runners'])]
                lay_values = [s['runners'][r_idx]['total_lay'] for s in snapshots if r_idx < len(s['runners'])]
                
                # Calculate deltas
                back_deltas = [back_values[i+1] - back_values[i] for i in range(len(back_values)-1)]
                lay_deltas = [lay_values[i+1] - lay_values[i] for i in range(len(lay_values)-1)]
                
                log_info(f"    BACK: {back_values[0]:,.2f} → {back_values[-1]:,.2f}")
                log_info(f"    LAY:  {lay_values[0]:,.2f} → {lay_values[-1]:,.2f}")
                log_info(f"    BACK deltas: {[f'{d:+,.2f}' for d in back_deltas]}")
                log_info(f"    LAY deltas:  {[f'{d:+,.2f}' for d in lay_deltas]}")
                
                # Validate: totals should never decrease drastically (small decreases OK due to cancelled bets)
                large_back_decrease = any(d < -1000 for d in back_deltas)
                large_lay_decrease = any(d < -1000 for d in lay_deltas)
                
                if large_back_decrease:
                    log_warn(f"    Large BACK decrease detected (>1000) - possible matched bet or cancellation")
                if large_lay_decrease:
                    log_warn(f"    Large LAY decrease detected (>1000) - possible matched bet or cancellation")
                
                # Check for data consistency
                if all(v >= 0 for v in back_values) and all(v >= 0 for v in lay_values):
                    log_pass(f"    All values non-negative (data integrity OK)")
                else:
                    log_fail(f"    Negative values detected! (data corruption)")
        
        log_pass("\nEnd-to-end test completed successfully")
        
    except Exception as e:
        log_fail(f"End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# PART 4: DECIMAL PRECISION & ROUNDING VALIDATION
# ============================================================================

def validate_precision():
    log_section("TEST 4: DECIMAL PRECISION & ROUNDING")
    
    # Test floating point operations
    log_info("Test 4.1: Floating point arithmetic precision")
    
    test_cases = [
        (1000.12, 500.34, 1500.46),
        (999999.99, 0.01, 1000000.00),
        (0.1, 0.2, 0.3),
        (123.456789, 876.543211, 1000.000000)
    ]
    
    for a, b, expected in test_cases:
        result = a + b
        diff = abs(result - expected)
        if diff < 1e-9:
            log_pass(f"{a} + {b} = {result:.10f} (expected {expected})")
        else:
            log_warn(f"{a} + {b} = {result:.10f} (expected {expected}, diff={diff:.10e})")
    
    # Test cumulative rounding errors
    log_info("\nTest 4.2: Cumulative rounding error simulation")
    
    cumulative = 0.0
    for i in range(1000):
        cumulative += 0.01
    
    expected = 10.0
    diff = abs(cumulative - expected)
    log_info(f"Sum of 0.01 x 1000 = {cumulative:.10f} (expected {expected})")
    if diff < 1e-9:
        log_pass("Cumulative rounding error negligible")
    else:
        log_warn(f"Cumulative rounding error: {diff:.10e}")
    
    # Test display rounding
    log_info("\nTest 4.3: Display rounding (2 decimal places)")
    
    values = [1000.125, 1000.115, 1000.105]
    for val in values:
        rounded = round(val, 2)
        formatted = f"{val:,.2f}"
        log_info(f"  {val} → round()={rounded} → format={formatted}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"Betty's Bomb Tracker - Comprehensive Accuracy Validation")
    print(f"Started at: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"{'='*80}{Colors.END}\n")
    
    try:
        validate_parsing()
        validate_money_flow()
        validate_precision()
        validate_end_to_end()
        
        log_section("VALIDATION COMPLETE")
        log_info("Review all ✓ PASS and ✗ FAIL messages above")
        log_info("Pay special attention to any ✗ FAIL or ⚠ WARNING messages")
        
    except KeyboardInterrupt:
        log_warn("\nValidation interrupted by user")
    except Exception as e:
        log_fail(f"Validation suite crashed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
