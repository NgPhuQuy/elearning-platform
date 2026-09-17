import uuid

import pytest

from app import dao, db
from app.index import app as flask_app
from app.models import User


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


def test_student_cannot_call_teacher_course_manage(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    # Tạo user là học viên bình thường (không có teacher_profile)
    student = User(
        username=f"stud_{unique_suffix}",
        email=f"stud_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    db.session.add(student)
    db.session.commit()

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(student.id)
            sess["_fresh"] = True

        # Cố gắng truy cập trang quản lý khóa học của giảng viên
        res = client.get("/courses/manage")
        # Decorator teacher_required phải chặn lại và redirect về "/"
        assert res.status_code == 302
        assert res.location == "/"

    db.session.delete(student)
    db.session.commit()


def test_student_cannot_delete_teacher_course(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    student = User(
        username=f"stud2_{unique_suffix}",
        email=f"stud2_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    db.session.add(student)
    db.session.commit()

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(student.id)
            sess["_fresh"] = True

        # Thử gửi lệnh xóa khóa học
        res = client.post("/courses/999/delete")
        assert res.status_code == 302
        assert res.location == "/"

    db.session.delete(student)
    db.session.commit()
