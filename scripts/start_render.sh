#!/bin/sh

set -eu

echo "[render-start] Waiting for the staging database..."
python -m scripts.wait_for_db

echo "[render-start] Creating missing database tables..."
python -m scripts.create_schema

echo "[render-start] Starting Gunicorn..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-1}" \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    app.index:app