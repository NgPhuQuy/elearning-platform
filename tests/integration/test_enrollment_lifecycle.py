import uuid

import pytest

from app import dao, db
from app.index import app as flask_app
from app.models import Course, EnrollmentStatus, Lesson, LessonType, User, VideoContent


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


def test_enrollment_attempt_lifecycle(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"test_user_{unique_suffix}",
        email=f"test_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
        first_name="Test",
        last_name="Student",
    )
    db.session.add(user)
    db.session.flush()

    course = Course(
        name=f"Khóa học Test {unique_suffix}",
        description="Mô tả",
        activate=True,
        price=0,
    )
    db.session.add(course)
    db.session.commit()

    # Lần 1: Đăng ký thành công
    enrollment1, err1 = dao.enroll_course(user.id, course.id)
    assert err1 is None
    assert enrollment1 is not None
    assert enrollment1.status == EnrollmentStatus.IN_PROGRESS

    # Khi đang IN_PROGRESS, không được đăng ký trùng
    enrollment_dup, err_dup = dao.enroll_course(user.id, course.id)
    assert enrollment_dup is None
    assert "quá trình học" in err_dup

    # Giả lập hoàn thành đợt 1
    enrollment1.status = EnrollmentStatus.COMPLETED
    db.session.commit()

    # Lần 2: Học viên đăng ký học lại đợt 2
    enrollment2, err2 = dao.enroll_course(user.id, course.id, force=True)
    assert err2 is None
    assert enrollment2.id != enrollment1.id
    assert enrollment2.status == EnrollmentStatus.IN_PROGRESS

    # Dọn dẹp dữ liệu test
    db.session.delete(enrollment2)
    db.session.delete(enrollment1)
    db.session.delete(course)
    db.session.delete(user)
    db.session.commit()


def test_complete_lesson_increases_progress(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"prog_user_{unique_suffix}",
        email=f"prog_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
        first_name="Prog",
        last_name="User",
    )
    course = Course(
        name=f"Progress Course {unique_suffix}",
        activate=True,
        price=0,
    )
    db.session.add_all([user, course])
    db.session.commit()

    # Tạo chapter và lesson có video content
    chapter = dao.create_chapter(course.id, None, "Chương 1", "Mô tả")
    lesson = Lesson(
        chapter_id=chapter.id,
        name="Bài 1",
        type=LessonType.VIDEO,
        video_content=VideoContent(video_url="http://video.test/1.mp4"),
    )
    db.session.add(lesson)
    db.session.commit()

    enrollment, err = dao.enroll_course(user.id, course.id)
    assert err is None
    assert enrollment.progress == 0

    # Đánh dấu bài học hoàn thành
    ok, mark_err = dao.mark_lesson_completed(user.id, course.id, lesson.id)
    assert ok is True
    assert mark_err is None

    # Vì khóa chỉ có 1 bài học -> progress phải lên 100% và status COMPLETED
    updated_enrollment = dao.get_latest_enrollment(user.id, course.id)
    assert updated_enrollment.progress == 100
    assert updated_enrollment.status == EnrollmentStatus.COMPLETED

    # Dọn dẹp
    db.session.delete(updated_enrollment)
    db.session.delete(course)
    db.session.delete(user)
    db.session.commit()
