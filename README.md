# Betty's Bomb Tracker# Live Team-wise Money Tracker



Real-time sports betting odds tracker with clean, minimal UI.A Streamlit dashboard and 24/7 background tracker to monitor per-team money flows from the market ladder. The background process persists cumulative stats in SQLite, and the dashboard displays them with 1s updates.



## Features## Features

- Per-team totals, top 3 ladders, best back/lay

- 🏏 Live Cricket, Soccer, Tennis & Horse Racing odds- Session deltas + persisted 24/7 cumulative

- 📊 Real-time Back/Lay prices with stakes- Auto start at in-play or scheduled start

- 🎯 Multi-sport switching- Events API cached (30 min) with manual refresh

- 🔄 Auto-refresh every 5 seconds- Manual mode for Market IDs when feed is down

- 🌙 Dark modern UI

## Local run

## Deployment1. Create venv and install deps

2. Start background tracker

Deployed on Render.com: [bettys-bomb-tracker.onrender.com](https://bettys-bomb-tracker.onrender.com)3. Start dashboard



## Local Development## Docker

Build and run locally:

```bash

pip install -r requirements.txt```sh

streamlit run dashboard.py# Build image

```docker build -t money-tracker .



## Files# Run container (maps port 8501 and a local data volume for persistence)

mkdir -p ./data

- `dashboard.py` - Main Streamlit dashboarddocker run --rm -p 8501:8501 \

- `token_manager.py` - API authentication handler  -v $(pwd)/data:/app/data \

- `Dockerfile` - Container configuration  -e PORT=8501 \

- `render.yaml` - Render deployment config  --name money-tracker money-tracker

```

Open http://localhost:8501

## Deploy options
- Render: Use Dockerfile; create a Web Service, set PORT=8501
- Fly.io: `flyctl launch` with Dockerfile; expose port 8501
- Railway/Dokku/Heroku container registry: push image, set PORT, map volume for `/app/data`

## Watchlist
Put Market IDs one per line in `data/watchlist.txt` to force 24/7 tracking.

## Environment
- Requires outbound HTTPS to odds and events APIs
- Persistence at `/app/data/tracker.db` (WAL enabled)
