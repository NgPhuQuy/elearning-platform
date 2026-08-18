#!/bin/sh

set -eu

echo "[release-start] Waiting for the database..."
python -m scripts.wait_for_db

echo "[release-start] Ensuring database schema exists..."
python -m scripts.create_schema

echo "[release-start] Starting Gunicorn..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-1}" \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    app.index:app