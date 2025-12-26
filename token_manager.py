"""
Automated Bearer Token Management for 99exch.com API

This module provides automated token refresh capabilities to avoid manual updates every 5 hours.
"""

import os
import time
import json
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import base64


class TokenManager:
    """Manages Bearer token authentication with automatic refresh."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize token manager.
        
        Args:
            username: 99exch.com username (optional, can use env var)
            password: 99exch.com password (optional, can use env var)
        """
        self.username = username or os.getenv("EXCH_USERNAME")
        self.password = password or os.getenv("EXCH_PASSWORD")
        self.token: Optional[str] = None
        self.token_expiry: Optional[int] = None
        
    def decode_token_payload(self, token: str) -> Dict[str, Any]:
        """
        Decode JWT token payload to check expiration.
        
        Args:
            token: JWT bearer token
            
        Returns:
            Decoded payload dict with iss, iat, exp, sub, etc.
        """
        try:
            # JWT format: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                return {}
            
            # Decode payload (base64url)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            print(f"[token] decode error: {e}")
            return {}
    
    def is_token_expired(self, token: str, buffer_seconds: int = 300) -> bool:
        """
        Check if token is expired or will expire soon.
        
        Args:
            token: JWT bearer token
            buffer_seconds: Refresh if expiring within this many seconds (default 5 min)
            
        Returns:
            True if expired or expiring soon, False otherwise
        """
        payload = self.decode_token_payload(token)
        exp = payload.get('exp')
        if not exp:
            return True
        
        current_time = int(time.time())
        time_until_expiry = exp - current_time
        
        return time_until_expiry <= buffer_seconds
    
    def login_demo_and_get_token(self) -> Optional[str]:
        """
        Login using demo account and extract bearer token.
        
        Demo accounts typically have public credentials and easier access.
        
        Returns:
            Bearer token string if successful, None otherwise
        """
        # Try demo login endpoint (common patterns)
        demo_endpoints = [
            "https://api.d99exch.com/api/demo/auth",
            "https://api.d99exch.com/api/auth/demo",
            "https://api.d99exch.com/api/guest/auth",
        ]
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://99exch.com",
            "Referer": "https://99exch.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        
        # Try demo/guest login without credentials
        for endpoint in demo_endpoints:
            try:
                print(f"[token] Trying demo login: {endpoint}")
                resp = requests.post(endpoint, json={}, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    token = (
                        data.get("token") or 
                        data.get("access_token") or 
                        (data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None)
                    )
                    if token:
                        payload = self.decode_token_payload(token)
                        exp = payload.get('exp')
                        if exp:
                            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
                            print(f"[token] ✅ Demo login successful! Token expires at {exp_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        else:
                            print("[token] ✅ Demo login successful! (No expiration info)")
                        return token
            except Exception as e:
                continue
        
        print("[token] ❌ Demo login failed on all endpoints")
        return None
    
    def login_and_get_token(self) -> Optional[str]:
        """
        Login to 99exch.com and extract bearer token.
        
        This attempts to authenticate via the login API endpoint.
        
        Returns:
            Bearer token string if successful, None otherwise
        """
        # First try demo login (no credentials needed)
        if os.getenv("USE_DEMO_LOGIN") == "true":
            print("[token] USE_DEMO_LOGIN enabled, trying demo login first...")
            demo_token = self.login_demo_and_get_token()
            if demo_token:
                return demo_token
        
        # Fall back to regular login with credentials
        if not self.username or not self.password:
            print("[token] Missing username or password. Set EXCH_USERNAME and EXCH_PASSWORD env vars.")
            return None
        
        login_url = "https://api.d99exch.com/api/auth"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://99exch.com",
            "Referer": "https://99exch.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        }
        
        payload = {
            "username": self.username,
            "password": self.password,
        }
        
        try:
            print(f"[token] Attempting login for user: {self.username}")
            resp = requests.post(login_url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            
            data = resp.json()
            
            # Common response structures:
            # Option 1: {"token": "eyJ0..."}
            # Option 2: {"data": {"token": "eyJ0..."}}
            # Option 3: {"access_token": "eyJ0..."}
            token = (
                data.get("token") or 
                data.get("access_token") or 
                (data.get("data", {}).get("token") if isinstance(data.get("data"), dict) else None)
            )
            
            if token:
                payload = self.decode_token_payload(token)
                exp = payload.get('exp')
                if exp:
                    exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
                    print(f"[token] ✅ Login successful! Token expires at {exp_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                else:
                    print("[token] ✅ Login successful! (No expiration info)")
                
                self.token = token
                self.token_expiry = exp
                return token
            else:
                print(f"[token] ❌ Login response missing token. Response: {data}")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"[token] ❌ Login failed with status {e.response.status_code}")
            print(f"[token] Response: {e.response.text[:500]}")
            return None
        except Exception as e:
            print(f"[token] ❌ Login error: {e}")
            return None
    
    def get_valid_token(self, fallback_token: Optional[str] = None) -> Optional[str]:
        """
        Get a valid token, refreshing if needed.
        
        Args:
            fallback_token: Token to use if auto-refresh not configured
            
        Returns:
            Valid bearer token or None
        """
        # If we have credentials, try auto-refresh
        if self.username and self.password:
            # Check if current token is still valid
            if self.token and not self.is_token_expired(self.token):
                return self.token
            
            # Token expired or missing, get new one
            print("[token] Token expired or missing, refreshing...")
            new_token = self.login_and_get_token()
            if new_token:
                return new_token
        
        # Fall back to manual token if provided
        if fallback_token:
            if self.is_token_expired(fallback_token):
                print("[token] ⚠️ WARNING: Fallback token is expired!")
                print("[token] Set EXCH_USERNAME and EXCH_PASSWORD for auto-refresh, or update token manually.")
            return fallback_token
        
        print("[token] ❌ No valid token available!")
        return None
    
    def refresh_token_periodically(self, check_interval_seconds: int = 3600):
        """
        Background task to periodically check and refresh token.
        
        This can run in a separate thread to keep token fresh.
        
        Args:
            check_interval_seconds: How often to check token validity (default 1 hour)
        """
        while True:
            if self.token and self.is_token_expired(self.token, buffer_seconds=600):
                print("[token] Token expiring soon, refreshing...")
                self.login_and_get_token()
            
            time.sleep(check_interval_seconds)


# Singleton instance
_token_manager: Optional[TokenManager] = None


def get_token_manager() -> TokenManager:
    """Get or create singleton TokenManager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager


def get_valid_token(fallback_token: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a valid token.
    
    Usage:
        token = get_valid_token(fallback_token="your_manual_token")
        headers = {"Authorization": f"bearer {token}"}
    
    Args:
        fallback_token: Token to use if auto-refresh not configured
        
    Returns:
        Valid bearer token or None
    """
    manager = get_token_manager()
    return manager.get_valid_token(fallback_token)


# Example usage
if __name__ == "__main__":
    import sys
    
    # Test token decoding
    test_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS5kOTlleGNoLmNvbS9hcGkvYXV0aCIsImlhdCI6MTc2Njc0NTQ2NywiZXhwIjoxNzY2NzYzNDY3LCJuYmYiOjE3NjY3NDU0NjcsImp0aSI6IlRNd1IwTjNwQVRQcFVIWkkiLCJzdWIiOiI5ODcyOTQiLCJwcnYiOiI4N2UwYWYxZWY5ZmQxNTgxMmZkZWM5NzE1M2ExNGUwYjA0NzU0NmFhIn0.XE3AIrm60v-No5wuNmSwDBGHZgNSYUk5S4C4kGJYd7U"
    
    manager = TokenManager()
    
    print("=" * 60)
    print("TOKEN MANAGER TEST")
    print("=" * 60)
    
    # Decode token
    payload = manager.decode_token_payload(test_token)
    print(f"\n1. Token Payload:")
    print(f"   Issuer: {payload.get('iss')}")
    print(f"   Subject (User ID): {payload.get('sub')}")
    print(f"   Issued At: {datetime.fromtimestamp(payload.get('iat', 0), tz=timezone.utc)}")
    print(f"   Expires At: {datetime.fromtimestamp(payload.get('exp', 0), tz=timezone.utc)}")
    
    # Check expiration
    is_expired = manager.is_token_expired(test_token)
    print(f"\n2. Token Expiration:")
    print(f"   Is Expired: {is_expired}")
    
    # Try login if credentials provided
    if os.getenv("EXCH_USERNAME") and os.getenv("EXCH_PASSWORD"):
        print(f"\n3. Auto-Login Test:")
        token = manager.login_and_get_token()
        if token:
            print(f"   ✅ Login successful!")
            print(f"   Token: {token[:50]}...")
        else:
            print(f"   ❌ Login failed")
    else:
        print(f"\n3. Auto-Login Test:")
        print(f"   ⚠️ Skipped - set EXCH_USERNAME and EXCH_PASSWORD env vars to test")
        print(f"   Example:")
        print(f"     export EXCH_USERNAME='your_username'")
        print(f"     export EXCH_PASSWORD='your_password'")
        print(f"     python3 token_manager.py")
    
    print("\n" + "=" * 60)
