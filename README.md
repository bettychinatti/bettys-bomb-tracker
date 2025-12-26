# Live Team-wise Money Tracker

A Streamlit dashboard and 24/7 background tracker to monitor per-team money flows from the market ladder. The background process persists cumulative stats in SQLite, and the dashboard displays them with 1s updates.

## Features
- Per-team totals, top 3 ladders, best back/lay
- Session deltas + persisted 24/7 cumulative
- Auto start at in-play or scheduled start
- Events API cached (30 min) with manual refresh
- Manual mode for Market IDs when feed is down

## Local run
1. Create venv and install deps
2. Start background tracker
3. Start dashboard

## Docker
Build and run locally:

```sh
# Build image
docker build -t money-tracker .

# Run container (maps port 8501 and a local data volume for persistence)
mkdir -p ./data
docker run --rm -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -e PORT=8501 \
  --name money-tracker money-tracker
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
