#!/bin/sh

set -eu

BASE_URL="${1:-${APP_URL:-http://127.0.0.1:8000}}"
TIMEOUT_SECONDS="${SMOKE_TIMEOUT_SECONDS:-120}"

# Loại bỏ dấu "/" cuối để tránh URL dạng "//".
BASE_URL="${BASE_URL%/}"

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

echo "[smoke-test] Target: $BASE_URL"

sh "$SCRIPT_DIR/wait_for_http.sh" \
  "$BASE_URL/" \
  "$TIMEOUT_SECONDS" \
  3

python - "$BASE_URL" <<'PY'
import sys
import urllib.error
import urllib.request

base_url = sys.argv[1].rstrip("/")

checks = [
    {
        "name": "Health check",
        "path": "/healthz",
        "accepted_statuses": range(200, 201),
    },
    {
        "name": "Home page",
        "path": "/",
        "accepted_statuses": range(200, 400),
    },
]

def check_endpoint(name, path, accepted_statuses):
    url = f"{base_url}{path}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "elearning-smoke-test/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            status = response.getcode()
            body = response.read(512)

    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(512)

    except Exception as exc:
        raise RuntimeError(
            f"{name} failed: cannot connect to {url}: {exc}"
        ) from exc

    if status not in accepted_statuses:
        preview = body.decode("utf-8", errors="replace")
        raise RuntimeError(
            f"{name} failed: {url} returned HTTP {status}. "
            f"Response preview: {preview!r}"
        )
    print(f"[smoke-test] PASS: {name} -> HTTP {status}")

failures: list[str] = []

for check in checks:
    try:
        check_endpoint(**check)
    except Exception as exc:
        failures.append(str(exc))
        print(f"[smoke-test] FAIL: {exc}")

if failures:
    print(f"[smoke-test] {len(failures)} check(s) failed.")
    raise SystemExit(1)

print(f"[smoke-test] All {len(checks)} check(s) passed.")
PY