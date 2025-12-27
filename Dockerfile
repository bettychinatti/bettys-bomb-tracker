# syntax=docker/dockerfile:1
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8501 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy app files
COPY dashboard.py background_tracker.py entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

EXPOSE 8501

# Run both tracker and dashboard
CMD ["/app/entrypoint.sh"]
