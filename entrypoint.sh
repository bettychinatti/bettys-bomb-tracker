#!/bin/bash
set -e

echo "🚀 Betty's Bomb Tracker - Ultra-Precise Tracking"
echo "=============================================="

# Start background tracker
echo "📊 Starting tracker (100ms polling)..."
python3 /app/background_tracker.py &
TRACKER_PID=$!
echo "✅ Tracker started (PID: $TRACKER_PID)"

# Wait for DB init
sleep 5

# Start dashboard
echo "🎨 Starting dashboard (1.5s refresh)..."
streamlit run /app/dashboard.py --server.port=${PORT:-8501} --server.address=0.0.0.0

# Cleanup
kill $TRACKER_PID 2>/dev/null || true
