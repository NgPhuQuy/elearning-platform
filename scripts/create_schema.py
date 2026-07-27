from app import app as flask_app
from app import db
from app import models as _models  # noqa: F401


def main() -> None:
    with flask_app.app_context():
        db.create_all()
        print("Database schema created successfully.")


if __name__ == "__main__":
    main()
