#!/bin/sh

set -eu

echo "[release-start] Waiting for the database..."
python -m scripts.wait_for_db

echo "[release-start] Ensuring database schema exists..."
python -m scripts.create_schema

echo "[release-start] Starting Gunicorn with GeventWebSocketWorker..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
    --workers "${GUNICORN_WORKERS:-1}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    app.index:app