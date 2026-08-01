#!/bin/sh

set -eu

COMPOSE_FILE="${COMPOSE_FILE:-compose.production.yaml}"
ENV_FILE="${ENV_FILE:-.env}"

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "[deploy] Missing Compose file: $COMPOSE_FILE" >&2
    exit 1
fi
if [ ! -f "$ENV_FILE" ]; then
    echo "[deploy] Missing environment file: $ENV_FILE" >&2
    exit 1
fi

compose() {
    docker compose \
        --env-file "$ENV_FILE" \
        -f "$COMPOSE_FILE" \
        "$@"
}

echo "[deploy] Validating deployment configuration..."
compose config --quiet

echo "[deploy] Pulling immutable application image and database image..."
compose pull app db

echo "[deploy] Starting database and waiting for health..."
compose up --detach --wait db

echo "[deploy] Applying database migrations..."
compose run --rm app sh -c '
    if [ "${BASELINE_EXISTING_DATABASE:-false}" = "true" ]; then
        python -m scripts.baseline_existing_database
    fi
    flask --app app.index:app db upgrade
'

echo "[deploy] Starting application and waiting for health..."
compose up --detach --wait app

echo "[deploy] Running application smoke test..."
compose exec -T app \
    sh scripts/smoke_test.sh http://127.0.0.1:8000

echo "[deploy] Deployment completed successfully."
compose ps