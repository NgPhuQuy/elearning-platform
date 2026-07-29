from sqlalchemy import text

from app import db
from app.index import app as flask_app


def test_database_connection():
    with flask_app.app_context():
        try:
            result = db.session.execute(text("SELECT 1")).scalar_one()
            assert result == 1
        finally:
            db.session.remove()


def test_home_page_is_served():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        response = client.get("/")
    assert response.status_code == 200
    assert response.mimetype == "text/html"

def test_health_check_reports_database_ready():
    flask_app.config.update(TESTING=True)
    with flask_app.test_client() as client:
        response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}