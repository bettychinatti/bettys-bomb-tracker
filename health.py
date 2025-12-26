"""
Health check and keep-alive endpoint for Render.com free tier
Prevents the app from sleeping by responding to external pings
"""

import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def show_health_status():
    """Display simple health status - called when ?health=true is in URL"""
    query_params = st.query_params
    
    if query_params.get("health") == "true":
        st.write("✅ HEALTHY")
        st.write(f"Timestamp: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        st.write("Status: Running")
        st.stop()
