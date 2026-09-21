from datetime import datetime
from unittest.mock import MagicMock, patch

from app.dao import enrollment_dao
from app.models import EnrollmentStatus, LessonType


# -------------------------------------------------------------
# 1. Kiểm tra bài học có nội dung hay không: _lesson_has_content
# -------------------------------------------------------------
def test_lesson_has_content_video_with_content():
    lesson = MagicMock(type=LessonType.VIDEO, video_content=MagicMock())
    assert bool(enrollment_dao._lesson_has_content(lesson)) is True


def test_lesson_has_content_video_without_content():
    lesson = MagicMock(type=LessonType.VIDEO, video_content=None)
    assert not enrollment_dao._lesson_has_content(lesson)


def test_lesson_has_content_document_with_content():
    lesson = MagicMock(type=LessonType.DOCUMENT, doc_content=MagicMock())
    assert bool(enrollment_dao._lesson_has_content(lesson)) is True


def test_lesson_has_content_document_without_content():
    lesson = MagicMock(type=LessonType.DOCUMENT, doc_content=None)
    assert not enrollment_dao._lesson_has_content(lesson)


# -------------------------------------------------------------
# 2. Tính toán phần trăm tiến độ khóa học: recalc_enrollment_progress
# -------------------------------------------------------------
@patch("app.dao.enrollment_dao.db")
@patch("app.dao.enrollment_dao.Course")
def test_recalc_progress_zero_items(mock_course_cls, mock_db):
    fake_course = MagicMock(chapters=[], tests=[])
    mock_course_cls.query.get.return_value = fake_course

    fake_enrollment = MagicMock(course_id=1, progress=50)

    enrollment_dao.recalc_enrollment_progress(fake_enrollment)

    assert fake_enrollment.progress == 0
    mock_db.session.commit.assert_called_once()


@patch("app.dao.enrollment_dao.Score")
@patch("app.dao.enrollment_dao.LessonProgress")
@patch("app.dao.enrollment_dao.db")
@patch("app.dao.enrollment_dao.Course")
def test_recalc_progress_partial_completion(mock_course_cls, mock_db, mock_lp_cls, mock_score_cls):
    # Khóa học có 4 bài học và 1 bài test = 5 items
    lesson1 = MagicMock(id=1, type=LessonType.VIDEO, video_content="vid1")
    lesson2 = MagicMock(id=2, type=LessonType.VIDEO, video_content="vid2")
    lesson3 = MagicMock(id=3, type=LessonType.DOCUMENT, doc_content="doc1")
    lesson4 = MagicMock(id=4, type=LessonType.DOCUMENT, doc_content="doc2")
    chapter = MagicMock(lessons=[lesson1, lesson2, lesson3, lesson4])
    fake_test = MagicMock(id=10)

    fake_course = MagicMock(chapters=[chapter], tests=[fake_test])
    mock_course_cls.query.get.return_value = fake_course

    # Học viên hoàn thành 2 bài học và 0 bài test -> 2/5 = 40%
    mock_lp_cls.query.filter.return_value.count.return_value = 2
    mock_score_cls.query.filter_by.return_value.distinct.return_value.count.return_value = 0

    fake_enrollment = MagicMock(id=100, course_id=1, status=EnrollmentStatus.IN_PROGRESS, progress=0)

    enrollment_dao.recalc_enrollment_progress(fake_enrollment)

    assert fake_enrollment.progress == 40
    # Chưa xong 100% thì trạng thái vẫn giữ nguyên
    assert fake_enrollment.status == EnrollmentStatus.IN_PROGRESS


@patch("app.dao.enrollment_dao.Certificate")
@patch("app.dao.enrollment_dao.Score")
@patch("app.dao.enrollment_dao.LessonProgress")
@patch("app.dao.enrollment_dao.db")
@patch("app.dao.enrollment_dao.Course")
def test_recalc_progress_100_percent_triggers_completion(mock_course_cls, mock_db, mock_lp_cls, mock_score_cls, mock_cert_cls):
    # Khóa học có 2 bài học
    lesson1 = MagicMock(id=1, type=LessonType.VIDEO, video_content="vid1")
    lesson2 = MagicMock(id=2, type=LessonType.VIDEO, video_content="vid2")
    chapter = MagicMock(lessons=[lesson1, lesson2])

    fake_course = MagicMock(chapters=[chapter], tests=[], has_certificate=True)
    mock_course_cls.query.get.return_value = fake_course
    mock_cert_cls.query.filter_by.return_value.first.return_value = None

    # Học viên hoàn thành cả 2 bài học -> 2/2 = 100%
    mock_lp_cls.query.filter.return_value.count.return_value = 2
    mock_score_cls.query.filter_by.return_value.distinct.return_value.count.return_value = 0

    fake_enrollment = MagicMock(id=100, course_id=1, status=EnrollmentStatus.IN_PROGRESS, progress=50)

    enrollment_dao.recalc_enrollment_progress(fake_enrollment)

    assert fake_enrollment.progress == 100
    assert fake_enrollment.status == EnrollmentStatus.COMPLETED
    assert isinstance(fake_enrollment.completed_date, datetime)
    mock_db.session.add.assert_called_once()
