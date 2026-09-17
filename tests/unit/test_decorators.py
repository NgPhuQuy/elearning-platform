from unittest.mock import MagicMock, patch

from app.decorators.auth import _add_login_param, anonymous_required, teacher_required
from app.decorators.socket import socket_auth_required


# -------------------------------------------------------------
# 1. URL Helper: _add_login_param
# -------------------------------------------------------------
def test_add_login_param_clean_url():
    result = _add_login_param("http://localhost:8000/courses")
    assert result == "http://localhost:8000/courses?login=1"


def test_add_login_param_with_existing_query():
    result = _add_login_param("http://localhost:8000/courses?category=1&page=2")
    assert "login=1" in result
    assert "category=1" in result
    assert "page=2" in result


# -------------------------------------------------------------
# 2. Decorator: anonymous_required
# -------------------------------------------------------------
@patch("app.decorators.auth.current_user")
def test_anonymous_required_blocks_authenticated_user(mock_user):
    mock_user.is_authenticated = True

    @anonymous_required
    def protected_view():
        return "view_content"

    resp = protected_view()
    # Phải redirect về "/"
    assert resp.status_code == 302
    assert resp.location == "/"


@patch("app.decorators.auth.current_user")
def test_anonymous_required_allows_guest(mock_user):
    mock_user.is_authenticated = False

    @anonymous_required
    def protected_view():
        return "guest_allowed"

    assert protected_view() == "guest_allowed"


# -------------------------------------------------------------
# 3. Decorator: teacher_required
# -------------------------------------------------------------
@patch("app.decorators.auth.current_user")
def test_teacher_required_blocks_unauthenticated_user(mock_user):
    mock_user.is_authenticated = False

    @teacher_required
    def teacher_view():
        return "teacher_data"

    resp = teacher_view()
    assert resp.status_code == 302
    assert resp.location == "/"


@patch("app.decorators.auth.current_user")
def test_teacher_required_blocks_student(mock_user):
    mock_user.is_authenticated = True
    mock_user.teacher_profile = None  # Học viên thường, không phải giáo viên

    @teacher_required
    def teacher_view():
        return "teacher_data"

    resp = teacher_view()
    assert resp.status_code == 302
    assert resp.location == "/"


@patch("app.decorators.auth.current_user")
def test_teacher_required_allows_teacher(mock_user):
    mock_user.is_authenticated = True
    mock_user.teacher_profile = MagicMock(id=1)

    @teacher_required
    def teacher_view():
        return "teacher_data"

    assert teacher_view() == "teacher_data"


# -------------------------------------------------------------
# 4. Decorator: socket_auth_required
# -------------------------------------------------------------
@patch("app.decorators.socket.current_user")
def test_socket_auth_required_blocks_unauthenticated(mock_user):
    mock_user.is_authenticated = False

    @socket_auth_required
    def socket_handler(data):
        return "handled"

    assert socket_handler({}) is None


@patch("app.decorators.socket.current_user")
def test_socket_auth_required_allows_authenticated(mock_user):
    mock_user.is_authenticated = True

    @socket_auth_required
    def socket_handler(data):
        return f"handled: {data.get('msg')}"

    assert socket_handler({"msg": "hello"}) == "handled: hello"
