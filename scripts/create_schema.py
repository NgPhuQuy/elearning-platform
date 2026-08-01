from flask_migrate import upgrade

from app import app as flask_app
from app import models as _models  # noqa: F401


def main():
    with flask_app.app_context():
        upgrade()
    print("Database migrations applied successfully.")


if __name__ == "__main__":
    main()
