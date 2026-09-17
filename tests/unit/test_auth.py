from unittest.mock import MagicMock, patch

from app.services import auth_service


# -------------------------------------------------------------
# 1. Đăng ký tài khoản (Validation & Business rules)
# -------------------------------------------------------------
def test_register_user_missing_required_fields():
    form_data = {
        "username": "student1",
        "password": "password123",
        "confirm": "password123",
        "email": "student1@example.com",
        "phone": "0912345678",
        "first_name": "Nguyen",
        # Thiếu "last_name"
    }
    user, err = auth_service.register_user(form_data, files={})
    assert user is None
    assert err == "Vui lòng nhập đầy đủ thông tin!"


def test_register_user_password_mismatch():
    form_data = {
        "username": "student1",
        "password": "password123",
        "confirm": "differentpassword",
        "email": "student1@example.com",
        "phone": "0912345678",
        "first_name": "Nguyen",
        "last_name": "An",
    }
    user, err = auth_service.register_user(form_data, files={})
    assert user is None
    assert err == "Mật khẩu không khớp!"


def test_register_user_password_too_short():
    form_data = {
        "username": "student1",
        "password": "short",
        "confirm": "short",
        "email": "student1@example.com",
        "phone": "0912345678",
        "first_name": "Nguyen",
        "last_name": "An",
    }
    user, err = auth_service.register_user(form_data, files={})
    assert user is None
    assert err == "Mật khẩu phải từ 8 ký tự trở lên!"


@patch("app.services.auth_service.dao")
def test_register_user_duplicate_username(mock_dao):
    mock_dao.is_username_exist.return_value = True
    form_data = {
        "username": "existing_user",
        "password": "password123",
        "confirm": "password123",
        "email": "unique@example.com",
        "phone": "0912345678",
        "first_name": "Nguyen",
        "last_name": "An",
    }
    user, err = auth_service.register_user(form_data, files={})
    assert user is None
    assert err == "Username đã tồn tại!"


@patch("app.services.auth_service.dao")
def test_register_user_duplicate_email(mock_dao):
    mock_dao.is_username_exist.return_value = False
    mock_dao.is_email_used.return_value = True
    form_data = {
        "username": "new_user",
        "password": "password123",
        "confirm": "password123",
        "email": "existing@example.com",
        "phone": "0912345678",
        "first_name": "Nguyen",
        "last_name": "An",
    }
    user, err = auth_service.register_user(form_data, files={})
    assert user is None
    assert err == "Email đã được sử dụng!"


@patch("app.services.auth_service.dao")
def test_register_user_duplicate_phone(mock_dao):
    mock_dao.is_username_exist.return_value = False
    mock_dao.is_email_used.return_value = False
    mock_dao.is_phone_used.return_value = True
    form_data = {
        "username": "new_user",
        "password": "password123",
        "confirm": "password123",
        "email": "new@example.com",
        "phone": "0900000000",
        "first_name": "Nguyen",
        "last_name": "An",
    }
    user, err = auth_service.register_user(form_data, files={})
    assert user is None
    assert err == "Số điện thoại này đã được đăng ký!"


# -------------------------------------------------------------
# 2. Đăng nhập & Xác thực (Auth logic)
# -------------------------------------------------------------
def test_auth_user_missing_credentials():
    user, err = auth_service.auth_user("", "")
    assert user is None
    assert "đầy đủ" in err


@patch("app.services.auth_service.dao")
def test_auth_user_wrong_credentials(mock_dao):
    mock_dao.auth_user.return_value = None
    user, err = auth_service.auth_user("student1", "wrong_password")
    assert user is None
    assert err == "Tài khoản hoặc mật khẩu không đúng!"


@patch("app.services.auth_service.dao")
def test_auth_user_locked_account(mock_dao):
    fake_user = MagicMock()
    fake_user.is_active = False
    mock_dao.auth_user.return_value = fake_user

    user, err = auth_service.auth_user("student1", "correct_pwd")
    assert user is None
    assert err == "Tài khoản của bạn đã bị khóa!"


@patch("app.services.auth_service.dao")
def test_auth_user_success(mock_dao):
    fake_user = MagicMock()
    fake_user.is_active = True
    mock_dao.auth_user.return_value = fake_user

    user, err = auth_service.auth_user("student1", "correct_pwd")
    assert user == fake_user
    assert err is None


# -------------------------------------------------------------
# 3. Phân quyền Admin
# -------------------------------------------------------------
@patch("app.services.auth_service.dao")
def test_auth_admin_non_admin_user(mock_dao):
    fake_user = MagicMock()
    fake_user.admin = None  # Không có role admin
    mock_dao.auth_user.return_value = fake_user

    user, err = auth_service.auth_admin("regular_user", "password123")
    assert user is None
    assert err == "Bạn không có quyền quản trị viên!"


@patch("app.services.auth_service.dao")
def test_auth_admin_success(mock_dao):
    fake_user = MagicMock()
    fake_user.admin = MagicMock()  # Có role admin
    mock_dao.auth_user.return_value = fake_user

    user, err = auth_service.auth_admin("admin_user", "password123")
    assert user == fake_user
    assert err is None


# -------------------------------------------------------------
# 4. Đổi mật khẩu (Password change verification)
# -------------------------------------------------------------
@patch("app.services.auth_service.dao")
def test_change_password_wrong_current(mock_dao):
    mock_dao.auth_user.return_value = None
    fake_user = MagicMock(username="student1")

    ok, err = auth_service.change_password(fake_user, "wrong_curr", "newpass123", "newpass123")
    assert ok is False
    assert err == "Sai mật khẩu!"


@patch("app.services.auth_service.dao")
def test_change_password_mismatch(mock_dao):
    mock_dao.auth_user.return_value = MagicMock()
    fake_user = MagicMock(username="student1")

    ok, err = auth_service.change_password(fake_user, "correct_curr", "newpass123", "differentpass")
    assert ok is False
    assert err == "Mật khẩu không khớp!"


@patch("app.services.auth_service.dao")
def test_change_password_too_short(mock_dao):
    mock_dao.auth_user.return_value = MagicMock()
    fake_user = MagicMock(username="student1")

    ok, err = auth_service.change_password(fake_user, "correct_curr", "short", "short")
    assert ok is False
    assert err == "Mật khẩu phải từ 8 ký tự trở lên!"


@patch("app.services.auth_service.dao")
def test_change_password_success(mock_dao):
    mock_dao.auth_user.return_value = MagicMock()
    mock_dao.change_password.return_value = (True, None)
    fake_user = MagicMock(username="student1")

    ok, err = auth_service.change_password(fake_user, "correct_curr", "newpassword123", "newpassword123")
    assert ok is True
    assert err is None
    mock_dao.change_password.assert_called_once_with("newpassword123")
