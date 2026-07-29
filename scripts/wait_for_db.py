from __future__ import annotations

import os
import time

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import app as flask_app
from app import db


def _positive_float_from_env(name, default):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value

def wait_for_database(timeout_seconds, interval_seconds):
    deadline = time.monotonic() + timeout_seconds
    attempt = 0
    with flask_app.app_context():
        while True:
            attempt += 1
            try:
                with db.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                print(f"[wait-for-db] Database is ready after {attempt} attempt(s).")
                return True
            except SQLAlchemyError as exc:
                db.session.remove()
                remaining_seconds = deadline - time.monotonic()
                if remaining_seconds <= 0:
                    print(
                        "[wait-for-db] ERROR: Database did not become ready "
                        f"within {timeout_seconds:g}s. Last error type: "
                        f"{type(exc).__name__}."
                    )
                    return False
                print(
                    "[wait-for-db] Database is not ready yet "
                    f"(attempt {attempt}, error type {type(exc).__name__})."
                )
                time.sleep(min(interval_seconds, remaining_seconds))

def main():
    try:
        timeout_seconds = _positive_float_from_env("DB_WAIT_TIMEOUT_SECONDS", 180)
        interval_seconds = _positive_float_from_env("DB_WAIT_INTERVAL_SECONDS", 3)
    except ValueError as exc:
        print(f"[wait-for-db] ERROR: {exc}")
        return 2
    print(
        "[wait-for-db] Waiting for database connectivity "
        f"(timeout={timeout_seconds:g}s, interval={interval_seconds:g}s)."
    )
    return 0 if wait_for_database(timeout_seconds, interval_seconds) else 1


if __name__ == "__main__":
    raise SystemExit(main())