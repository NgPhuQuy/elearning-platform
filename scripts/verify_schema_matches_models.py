from __future__ import annotations

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app import app as flask_app
from app import db
from app import models as _models  # noqa: F401  # Register model metadata.


def get_schema_differences():
    with flask_app.app_context():
        with db.engine.connect() as connection:
            context = MigrationContext.configure(
                connection,
                opts={
                    "compare_type": True,
                    "compare_server_default": False,
                },
            )
            return list(compare_metadata(context, db.metadata))


def main():
    differences = get_schema_differences()
    if differences:
        print("[schema-verify] ERROR: Database schema differs from the models.")
        for difference in differences:
            print(f"[schema-verify] - {difference!r}")
        print("[schema-verify] Refusing to baseline migrations. Review the differences before stamping the database.")
        return 1
    print("[schema-verify] Database schema matches the current models.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
