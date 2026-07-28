#!/bin/sh

set -eu

URL="${1:-${APP_URL:-http://127.0.0.1:8000/}}"
TIMEOUT_SECONDS="${2:-120}"
INTERVAL_SECONDS="${3:-3}"

case "$URL" in
  http://*|https://*)
    ;;
  *)
    echo "[wait-for-http] ERROR: URL must begin with http:// or https://"
    exit 2
    ;;
esac

echo "[wait-for-http] Waiting for: $URL"
echo "[wait-for-http] Timeout: ${TIMEOUT_SECONDS}s"
echo "[wait-for-http] Interval: ${INTERVAL_SECONDS}s"

START_TIME="$(date +%s)"

while true; do
  if python - "$URL" <<'PY'
import sys
import urllib.error
import urllib.request

url = sys.argv[1]

try:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "elearning-infrastructure-check/1.0"},
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        status = response.getcode()

    if 200 <= status < 400:
        print(f"[wait-for-http] HTTP {status}")
        raise SystemExit(0)

    print(f"[wait-for-http] HTTP {status}")
    raise SystemExit(1)

except urllib.error.HTTPError as exc:
    # HTTPError vẫn có status code, ví dụ 404 hoặc 500.
    print(f"[wait-for-http] HTTP {exc.code}")
    raise SystemExit(1)

except Exception as exc:
    print(f"[wait-for-http] Not ready: {exc}")
    raise SystemExit(1)
PY
  then
    echo "[wait-for-http] Service is ready."
    exit 0
  fi

  CURRENT_TIME="$(date +%s)"
  ELAPSED_SECONDS=$((CURRENT_TIME - START_TIME))

  if [ "$ELAPSED_SECONDS" -ge "$TIMEOUT_SECONDS" ]; then
    echo "[wait-for-http] ERROR: Service did not become ready within ${TIMEOUT_SECONDS}s."
    exit 1
  fi

  sleep "$INTERVAL_SECONDS"
done