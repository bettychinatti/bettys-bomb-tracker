#!/usr/bin/env sh
set -e

# Start background tracker
python /app/background_tracker.py &

# Start streamlit
exec streamlit run /app/dashboard.py --server.address=0.0.0.0 --server.port=${PORT:-8501}
