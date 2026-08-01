#!/bin/sh

set -eu

echo "[release-start] Waiting for the database..."
python -m scripts.wait_for_db

if [ "${BASELINE_EXISTING_DATABASE:-false}" = "true" ]; then
    echo "[release-start] Checking the one-time migration baseline..."
    python -m scripts.baseline_existing_database
fi

echo "[release-start] Applying database migrations..."
flask --app app.index:app db upgrade

echo "[release-start] Starting Gunicorn..."
exec gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-1}" \
    --threads "${GUNICORN_THREADS:-8}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    app.index:app