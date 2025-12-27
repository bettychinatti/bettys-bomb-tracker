#!/bin/bash#!/usr/bin/env sh

set -eset -e



echo "🚀 Starting Betty's Bomb Tracker..."# Start background tracker

python /app/background_tracker.py &

# Start background tracker

echo "📊 Starting background tracker..."# Start streamlit

python3 background_tracker.py &exec streamlit run /app/dashboard.py --server.address=0.0.0.0 --server.port=${PORT:-8501}

TRACKER_PID=$!
echo "✅ Background tracker started (PID: $TRACKER_PID)"

# Wait a bit for tracker to initialize database
sleep 3

# Start Streamlit dashboard
echo "🎨 Starting Streamlit dashboard..."
streamlit run dashboard.py --server.port=8501 --server.address=0.0.0.0

# If Streamlit exits, kill the tracker
kill $TRACKER_PID 2>/dev/null || true
