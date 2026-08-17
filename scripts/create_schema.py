from flask_migrate import upgrade  # noqa: F401

from app import app as flask_app
from app import db
from app import models as _models  # noqa: F401


def main():
    with flask_app.app_context():
        db.create_all()
    print("Database migrations applied successfully.")


if __name__ == "__main__":
    main()
