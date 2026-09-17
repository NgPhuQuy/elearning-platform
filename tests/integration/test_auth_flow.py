import uuid

import pytest

from app import db
from app.index import app as flask_app
from app.models import User


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


def test_auth_full_flow_register_login_logout(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"flow_user_{unique_suffix}"
    email = f"flow_{unique_suffix}@example.com"
    password = "FlowPassword123"

    with flask_app.test_client() as client:
        # 1. Đăng ký tài khoản mới qua endpoint /register
        register_data = {
            "username": username,
            "email": email,
            "phone": f"09{uuid.uuid4().int % 100000000:08d}",
            "first_name": "Flow",
            "last_name": "Test",
            "password": password,
            "confirm": password,
        }
        res_register = client.post("/register", data=register_data)
        assert res_register.status_code == 200
        json_reg = res_register.get_json()
        assert json_reg["success"] is True

        # 2. Đăng xuất
        res_logout = client.get("/logout")
        assert res_logout.status_code == 302

        # 3. Đăng nhập sai mật khẩu -> Báo lỗi 401
        res_wrong_login = client.post("/login", data={"username": username, "password": "WrongPassword"})
        assert res_wrong_login.status_code == 401
        assert res_wrong_login.get_json()["success"] is False

        # 4. Đăng nhập đúng mật khẩu -> Thành công 200
        res_correct_login = client.post("/login", data={"username": username, "password": password})
        assert res_correct_login.status_code == 200
        assert res_correct_login.get_json()["success"] is True

    # Dọn dẹp user tạo trong test
    user = User.query.filter_by(username=username).first()
    if user:
        db.session.delete(user)
        db.session.commit()


def test_unauthenticated_user_redirected_on_protected_routes(app_ctx):
    with flask_app.test_client() as client:
        # Gọi route cần auth khi chưa login
        res = client.get("/my-learning")
        assert res.status_code == 302
        assert "/?login=1" in res.location or "login=1" in res.location
