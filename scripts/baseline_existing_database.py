from __future__ import annotations

from flask_migrate import stamp
from sqlalchemy import inspect, text

from app import app as flask_app
from app import db
from scripts.verify_schema_matches_models import get_schema_differences

BASELINE_REVISION = "b7f4d9a31c01"


def _recorded_revisions():
    inspector = inspect(db.engine)
    if not inspector.has_table("alembic_version"):
        return []
    with db.engine.connect() as connection:
        rows = connection.execute(text("SELECT version_num FROM alembic_version"))
        return [str(row[0]) for row in rows]


def main():
    with flask_app.app_context():
        revisions = _recorded_revisions()
        if revisions:
            print(
                f"[migration-baseline] Database is already managed by Alembic at revision(s): {', '.join(revisions)}."
            )
            return 0
        differences = get_schema_differences()
        if differences:
            print("[migration-baseline] ERROR: The existing schema does not match the PR5 model baseline.")
            for difference in differences:
                print(f"[migration-baseline] - {difference!r}")
            print("[migration-baseline] The database was not stamped.")
            return 1

        stamp(revision=BASELINE_REVISION)
        print(f"[migration-baseline] Existing database stamped at revision {BASELINE_REVISION}.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
