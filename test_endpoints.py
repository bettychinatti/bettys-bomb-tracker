#!/usr/bin/env python3
"""
Comprehensive endpoint test script for Betty's Bomb Tracker
Tests all critical API endpoints and deployment health
"""

import requests
import time
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# Endpoints to test
EVENTS_API = "https://api.d99hub.com/api/guest/event_list"
MARKET_API = "https://odds.o99hub.com/ws/getMarketDataNew"
FLY_APP_URL = "https://bettys-bomb-tracker.fly.dev"

HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "Origin": "https://gin247.net",
    "Referer": "https://gin247.net/inplay",
    "User-Agent": "Mozilla/5.0",
}


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_test(name: str, status: bool, message: str = "", latency: float = 0.0):
    """Print test result with color coding"""
    status_icon = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
    latency_str = f" ({latency:.3f}s)" if latency > 0 else ""
    print(f"{status_icon} {name}{latency_str}")
    if message:
        color = Colors.GREEN if status else Colors.RED
        print(f"  {color}{message}{Colors.RESET}")


def test_events_api() -> Tuple[bool, Dict[str, Any]]:
    """Test the Events API endpoint"""
    print_header("Testing Events API")
    
    results = {
        "endpoint": EVENTS_API,
        "status": False,
        "http_code": None,
        "latency": 0.0,
        "event_count": 0,
        "in_play_count": 0,
        "sports": [],
        "errors": []
    }
    
    try:
        start = time.time()
        resp = requests.get(EVENTS_API, timeout=10)
        latency = time.time() - start
        results["latency"] = latency
        results["http_code"] = resp.status_code
        
        # Check HTTP status
        if resp.status_code != 200:
            results["errors"].append(f"HTTP {resp.status_code}")
            print_test("HTTP Status", False, f"Expected 200, got {resp.status_code}", latency)
            return False, results
        
        print_test("HTTP Status", True, "200 OK", latency)
        
        # Parse JSON
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            results["errors"].append(f"JSON parse error: {e}")
            print_test("JSON Response", False, "Failed to parse JSON")
            return False, results
        
        print_test("JSON Response", True, "Valid JSON")
        
        # Check structure
        if not isinstance(data, dict):
            results["errors"].append("Response is not a dict")
            print_test("Response Structure", False, "Expected dict")
            return False, results
        
        if 'data' not in data or 'events' not in data.get('data', {}):
            results["errors"].append("Missing data.events field")
            print_test("Response Structure", False, "Missing data.events")
            return False, results
        
        events = data['data']['events']
        if not isinstance(events, list):
            results["errors"].append("events is not a list")
            print_test("Response Structure", False, "events is not a list")
            return False, results
        
        print_test("Response Structure", True, f"data.events is list")
        
        # Count events
        results["event_count"] = len(events)
        results["in_play_count"] = sum(1 for ev in events if ev.get('in_play') == 1)
        
        # Extract sports
        sport_map = {1: "Soccer", 2: "Tennis", 4: "Cricket"}
        sports_present = set()
        for ev in events:
            etid = ev.get('event_type_id')
            if etid in sport_map:
                sports_present.add(sport_map[etid])
        results["sports"] = list(sports_present)
        
        print_test("Event Count", True, f"{results['event_count']} total events")
        print_test("In-Play Count", True, f"{results['in_play_count']} in-play events")
        print_test("Sports Found", True, f"{', '.join(sorted(results['sports']))}")
        
        # Sample event validation
        if events:
            sample = events[0]
            required_fields = ['event_id', 'market_id', 'event_name']
            missing = [f for f in required_fields if f not in sample]
            if missing:
                print_test("Event Fields", False, f"Missing: {', '.join(missing)}")
            else:
                print_test("Event Fields", True, "All required fields present")
        
        results["status"] = True
        return True, results
        
    except requests.Timeout:
        results["errors"].append("Request timeout")
        print_test("Request", False, "Timeout after 10s")
        return False, results
    except requests.RequestException as e:
        results["errors"].append(str(e))
        print_test("Request", False, str(e))
        return False, results
    except Exception as e:
        results["errors"].append(str(e))
        print_test("Unexpected Error", False, str(e))
        return False, results


def test_markets_api() -> Tuple[bool, Dict[str, Any]]:
    """Test the Markets API endpoint"""
    print_header("Testing Markets API")
    
    results = {
        "endpoint": MARKET_API,
        "status": False,
        "http_code": None,
        "latency": 0.0,
        "market_count": 0,
        "parsable": False,
        "errors": []
    }
    
    # First get a live market ID from events API
    try:
        resp = requests.get(EVENTS_API, timeout=10)
        data = resp.json()
        events = data.get('data', {}).get('events', [])
        in_play_events = [ev for ev in events if ev.get('in_play') == 1]
        
        if not in_play_events:
            print_test("Prerequisites", False, "No in-play events found")
            results["errors"].append("No in-play events available for testing")
            return False, results
        
        sample_market_id = str(in_play_events[0].get('market_id'))
        print_test("Prerequisites", True, f"Using market ID: {sample_market_id}")
        
    except Exception as e:
        print_test("Prerequisites", False, f"Failed to get market ID: {e}")
        results["errors"].append(f"Prerequisites failed: {e}")
        return False, results
    
    try:
        # Test Markets API
        payload = [("market_ids[]", sample_market_id)]
        start = time.time()
        resp = requests.post(MARKET_API, headers=HEADERS, data=payload, timeout=10)
        latency = time.time() - start
        results["latency"] = latency
        results["http_code"] = resp.status_code
        
        # Check HTTP status
        if resp.status_code != 200:
            results["errors"].append(f"HTTP {resp.status_code}")
            print_test("HTTP Status", False, f"Expected 200, got {resp.status_code}", latency)
            return False, results
        
        print_test("HTTP Status", True, "200 OK", latency)
        
        # Parse JSON
        try:
            data = resp.json()
        except json.JSONDecodeError as e:
            results["errors"].append(f"JSON parse error: {e}")
            print_test("JSON Response", False, "Failed to parse JSON")
            return False, results
        
        print_test("JSON Response", True, "Valid JSON")
        
        # Check structure
        if not isinstance(data, list):
            results["errors"].append("Response is not a list")
            print_test("Response Structure", False, "Expected list")
            return False, results
        
        results["market_count"] = len(data)
        print_test("Response Structure", True, f"{results['market_count']} markets returned")
        
        # Test parsing
        if data:
            market_str = data[0]
            if not isinstance(market_str, str):
                results["errors"].append("Market data is not string")
                print_test("Market Format", False, "Expected string")
                return False, results
            
            print_test("Market Format", True, "Pipe-delimited string")
            
            # Parse market string
            fields = market_str.split('|')
            mid = fields[0]
            
            # Check basic structure
            if len(fields) < 6:
                results["errors"].append("Insufficient fields in market string")
                print_test("Field Count", False, f"Only {len(fields)} fields")
                return False, results
            
            print_test("Field Count", True, f"{len(fields)} fields")
            
            # Extract total_matched
            try:
                total_matched = float(fields[5])
                print_test("Total Matched", True, f"₹{total_matched:,.2f}")
            except Exception as e:
                print_test("Total Matched", False, f"Parse error: {e}")
            
            # Check for ACTIVE markers
            active_count = fields.count('ACTIVE')
            print_test("Runners (ACTIVE)", True, f"{active_count} runners")
            
            # Try to parse ladder
            try:
                i = 0
                runners_parsed = 0
                while i < len(fields):
                    if fields[i] == 'ACTIVE':
                        i += 1
                        pairs = []
                        read = 0
                        while i + 1 < len(fields) and read < 12:
                            try:
                                odd = float(fields[i])
                                amt = float(fields[i+1])
                                pairs.append((odd, amt))
                                i += 2
                                read += 2
                            except:
                                break
                        if len(pairs) >= 6:
                            runners_parsed += 1
                    else:
                        i += 1
                
                if runners_parsed >= 2:
                    results["parsable"] = True
                    print_test("Ladder Parsing", True, f"{runners_parsed} complete ladders")
                else:
                    print_test("Ladder Parsing", False, f"Only {runners_parsed} complete ladders")
                    
            except Exception as e:
                print_test("Ladder Parsing", False, str(e))
        
        results["status"] = True
        return True, results
        
    except requests.Timeout:
        results["errors"].append("Request timeout")
        print_test("Request", False, "Timeout after 10s")
        return False, results
    except requests.RequestException as e:
        results["errors"].append(str(e))
        print_test("Request", False, str(e))
        return False, results
    except Exception as e:
        results["errors"].append(str(e))
        print_test("Unexpected Error", False, str(e))
        return False, results


def test_fly_deployment() -> Tuple[bool, Dict[str, Any]]:
    """Test the Fly.io deployment"""
    print_header("Testing Fly.io Deployment")
    
    results = {
        "endpoint": FLY_APP_URL,
        "status": False,
        "http_code": None,
        "latency": 0.0,
        "https": False,
        "errors": []
    }
    
    try:
        start = time.time()
        resp = requests.get(FLY_APP_URL, timeout=15, allow_redirects=True)
        latency = time.time() - start
        results["latency"] = latency
        results["http_code"] = resp.status_code
        results["https"] = resp.url.startswith("https://")
        
        # Check HTTP status
        if resp.status_code != 200:
            results["errors"].append(f"HTTP {resp.status_code}")
            print_test("HTTP Status", False, f"Expected 200, got {resp.status_code}", latency)
            return False, results
        
        print_test("HTTP Status", True, "200 OK", latency)
        print_test("HTTPS Enabled", results["https"], "Secure connection")
        
        # Check content type
        content_type = resp.headers.get('content-type', '')
        is_html = 'text/html' in content_type
        print_test("Content Type", is_html, content_type)
        
        # Check for Streamlit indicators
        content = resp.text
        has_streamlit = any(marker in content for marker in ['streamlit', 'Streamlit', 'st-emotion'])
        print_test("Streamlit App", has_streamlit, "Detected Streamlit markers" if has_streamlit else "No Streamlit markers")
        
        # Check for app title
        has_title = "Betty" in content or "Bomb" in content or "Tracker" in content
        print_test("App Title", has_title, "Betty's Bomb Tracker found" if has_title else "Title not found")
        
        # Check response size
        size_kb = len(content) / 1024
        print_test("Response Size", size_kb > 10, f"{size_kb:.1f} KB")
        
        results["status"] = True
        return True, results
        
    except requests.Timeout:
        results["errors"].append("Request timeout")
        print_test("Request", False, "Timeout after 15s")
        return False, results
    except requests.RequestException as e:
        results["errors"].append(str(e))
        print_test("Request", False, str(e))
        return False, results
    except Exception as e:
        results["errors"].append(str(e))
        print_test("Unexpected Error", False, str(e))
        return False, results


def main():
    """Run all endpoint tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Betty's Bomb Tracker - Endpoint Test Suite{Colors.RESET}")
    print(f"{Colors.BOLD}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
    
    all_results = {}
    
    # Test Events API
    status1, results1 = test_events_api()
    all_results["events_api"] = results1
    
    # Test Markets API
    status2, results2 = test_markets_api()
    all_results["markets_api"] = results2
    
    # Test Fly deployment
    status3, results3 = test_fly_deployment()
    all_results["fly_deployment"] = results3
    
    # Summary
    print_header("Test Summary")
    
    total_tests = 3
    passed = sum([status1, status2, status3])
    
    print(f"Total Tests: {total_tests}")
    print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
    if passed < total_tests:
        print(f"{Colors.RED}Failed: {total_tests - passed}{Colors.RESET}")
    
    overall = all([status1, status2, status3])
    
    if overall:
        print(f"\n{Colors.BOLD}{Colors.GREEN}✓ All endpoints are operational{Colors.RESET}")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}✗ Some endpoints have issues{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Errors:{Colors.RESET}")
        for name, res in all_results.items():
            if res["errors"]:
                print(f"  {name}:")
                for err in res["errors"]:
                    print(f"    - {err}")
    
    # Performance summary
    print(f"\n{Colors.BOLD}Performance:{Colors.RESET}")
    for name, res in all_results.items():
        if res["latency"] > 0:
            label = name.replace('_', ' ').title()
            print(f"  {label}: {res['latency']:.3f}s")
    
    print(f"\n{Colors.BOLD}Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")
    
    return 0 if overall else 1


if __name__ == "__main__":
    exit(main())
