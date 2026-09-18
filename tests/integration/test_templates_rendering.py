import uuid

import pytest

from app import dao, db
from app.index import app as flask_app
from app.models import (
    ROLE,
    Chapter,
    Course,
    CourseLevel,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonType,
    Payment,
    PaymentStatus,
    User,
)
from app.models.test import Test as CourseTest


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


def test_public_pages_render_without_crash(app_ctx):
    with flask_app.test_client() as client:
        # Index page anonymous
        res = client.get("/")
        assert res.status_code == 200
        assert "Chào mừng" in res.get_data(as_text=True) or "EduForge" in res.get_data(as_text=True)

        # Courses list
        res = client.get("/courses")
        assert res.status_code == 200

        # Forum list
        res = client.get("/forum")
        assert res.status_code == 200


def test_authenticated_profile_and_learning_templates(app_ctx):
    suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"tpl_user_{suffix}",
        email=f"tpl_{suffix}@example.com",
        first_name="Học",
        last_name="Viên",
        password=dao.hash_password("12345678"),
        role=ROLE.USER,
    )
    teacher = User(
        username=f"tpl_teacher_{suffix}",
        email=f"teacher_{suffix}@example.com",
        first_name="Thầy",
        last_name="Giáo",
        password=dao.hash_password("12345678"),
        role=ROLE.TEACHER,
    )
    db.session.add_all([user, teacher])
    db.session.commit()

    course = Course(
        name=f"Khóa học UI {suffix}",
        price=100000,
        level=CourseLevel.BASIC,
        teacher_id=teacher.id,
        activate=True,
    )
    db.session.add(course)
    db.session.commit()

    chapter = Chapter(name="Chương 1", course_id=course.id, order=1)
    db.session.add(chapter)
    db.session.commit()

    lesson = Lesson(name="Bài 1", chapter_id=chapter.id, type=LessonType.VIDEO, content="https://example.com")
    db.session.add(lesson)
    db.session.commit()

    enrollment = Enrollment(user_id=user.id, course_id=course.id, status=EnrollmentStatus.IN_PROGRESS, progress=10)
    payment = Payment(
        user_id=user.id,
        course_id=course.id,
        order_id=f"ORD-{suffix}",
        amount=100000,
        pay_type="vnpay",
        status=PaymentStatus.SUCCESS,
    )
    db.session.add_all([enrollment, payment])
    db.session.commit()

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # Index page authenticated
        res = client.get("/")
        assert res.status_code == 200
        assert "Chào buổi sáng" in res.get_data(as_text=True)

        # Profile
        res = client.get("/profile")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "Học Viên" in html
        assert "Thầy Giáo" in html

        # Change Info
        res = client.get("/profile/change-info")
        assert res.status_code == 200
        assert "Chỉnh sửa thông tin" in res.get_data(as_text=True)

        # Change Password
        res = client.get("/profile/change-password")
        assert res.status_code == 200
        assert "Đổi mật khẩu" in res.get_data(as_text=True)

        # My Learning
        res = client.get("/my-learning")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert course.name in html
        assert "Thầy Giáo" in html

        # Payment History
        res = client.get("/payment/history")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert f"ORD-{suffix}" in html
        assert "100,000" in html

        # Course Detail
        res = client.get(f"/courses/{course.id}")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "Thầy Giáo" in html

        # Learn page
        res = client.get(f"/learn/{course.id}")
        assert res.status_code == 200

    # Cleanup
    db.session.delete(payment)
    db.session.delete(enrollment)
    db.session.delete(course)
    db.session.delete(user)
    db.session.delete(teacher)
    db.session.commit()


def test_teacher_course_form_and_tests_rendering(app_ctx):
    suffix = uuid.uuid4().hex[:6]
    teacher = User(
        username=f"prof_{suffix}",
        email=f"prof_{suffix}@example.com",
        first_name="Giảng",
        last_name="Viên",
        password=dao.hash_password("12345678"),
        role=ROLE.TEACHER,
    )
    db.session.add(teacher)
    db.session.commit()

    course = Course(
        name=f"Course Edit {suffix}",
        price=50000,
        level=CourseLevel.INTERMEDIATE,
        teacher_id=teacher.id,
        activate=True,
    )
    db.session.add(course)
    db.session.commit()

    chapter = Chapter(name=f"Chương Test {suffix}", course_id=course.id, order=1)
    db.session.add(chapter)
    db.session.commit()

    test = CourseTest(
        name=f"Kiểm tra {suffix}", course_id=course.id, chapter_id=chapter.id, duration=15, max_attempts=3
    )
    db.session.add(test)
    db.session.commit()

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher.id)
            sess["_fresh"] = True

        # Course Form Update
        res = client.get(f"/courses/{course.id}/update")
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert f"Chương Test {suffix}" in html
        assert f"Kiểm tra {suffix}" in html

        # Manage Questions page
        res = client.get(f"/courses/{course.id}/tests/{test.id}/questions")
        assert res.status_code == 200

        # Test Info
        res = client.get(f"/courses/{course.id}/tests/{test.id}")
        assert res.status_code == 200

        # Test Result (no attempts yet)
        res = client.get(f"/courses/{course.id}/tests/{test.id}/result")
        assert res.status_code == 200

    # Cleanup
    db.session.delete(course)
    db.session.delete(teacher)
    db.session.commit()
