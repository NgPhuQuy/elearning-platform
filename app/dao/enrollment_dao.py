from datetime import datetime

from flask_login import current_user

from app import db
from app.models import Course, Enrollment, EnrollmentStatus, Lesson, LessonProgress, LessonType, Score


def get_latest_enrollment(user_id, course_id):
    return (
        Enrollment.query.filter_by(user_id=user_id, course_id=course_id)
        .order_by(Enrollment.created_date.desc(), Enrollment.id.desc())
        .first()
    )


def is_enrolled(user_id, course_id):
    latest = get_latest_enrollment(user_id, course_id)
    return latest is not None and latest.status != EnrollmentStatus.FAILED


def enroll_course(user_id, course_id, force=False, price=0):
    course = Course.query.get(course_id)
    if not course:
        return None, "Khóa học không tồn tại."
    if not course.activate and not force:
        return None, "Khóa học chưa được công khai."

    if course.teacher_id and current_user.is_authenticated and current_user.teacher_profile:
        if course.teacher_id == current_user.teacher_profile.id:
            return None, "Bạn không thể tự đăng ký khóa học do chính mình tạo."

    latest_enrollment = get_latest_enrollment(user_id, course_id)
    if latest_enrollment and latest_enrollment.status == EnrollmentStatus.IN_PROGRESS and not force:
        return None, "Bạn đang trong quá trình học khóa học này."
    if latest_enrollment and latest_enrollment.status == EnrollmentStatus.COMPLETED and not force:
        return None, "Bạn đã hoàn thành khóa học này rồi."
    if not force and course.price and course.price > 0:
        return None, "Khóa học có phí, vui lòng thanh toán trước khi đăng ký."

    enrollment = Enrollment(
        user_id=user_id,
        course_id=course_id,
        price=price if force else (course.price or 0),
        status=EnrollmentStatus.IN_PROGRESS,
        progress=0,
    )
    try:
        db.session.add(enrollment)
        db.session.commit()
        return enrollment, None
    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng thử lại sau!"


def get_my_enrollments(user_id):
    return (
        Enrollment.query.filter_by(user_id=user_id)
        .order_by(Enrollment.created_date.desc())
        .all()
    )


def _lesson_has_content(lesson):
    return (lesson.type == LessonType.VIDEO and lesson.video_content) or (
        lesson.type == LessonType.DOCUMENT and lesson.doc_content
    )


def mark_lesson_completed(user_id, course_id, lesson_id):
    enrollment = get_latest_enrollment(user_id, course_id)
    if not enrollment:
        return False, "Chưa đăng ký khóa học"

    lesson = Lesson.query.get(lesson_id)
    if not lesson or not _lesson_has_content(lesson):
        return False, "Bài học chưa có nội dung"

    progress = LessonProgress.query.filter_by(enrollment_id=enrollment.id, lesson_id=lesson_id).first()
    if not progress:
        progress = LessonProgress(enrollment_id=enrollment.id, lesson_id=lesson_id)
        db.session.add(progress)

    now = datetime.now()
    progress.last_watched_at = now
    if not progress.is_completed:
        progress.is_completed = True
        progress.completed_at = now

    try:
        db.session.commit()
        recalc_enrollment_progress(enrollment)
        return True, None
    except Exception:
        db.session.rollback()
        return False, "Hệ thống lỗi"


def get_lesson_progress_map(user_id, course_id):
    enrollment = get_latest_enrollment(user_id, course_id)
    if not enrollment:
        return {}

    progresses = LessonProgress.query.filter_by(enrollment_id=enrollment.id).all()
    return {p.lesson_id: p.is_completed for p in progresses}


def recalc_enrollment_progress(enrollment):
    course = Course.query.get(enrollment.course_id)
    if not course:
        return

    all_lessons = [
        les
        for chap in course.chapters
        for les in chap.lessons
        if _lesson_has_content(les)
    ]
    all_tests = list(course.tests)
    total_items = len(all_lessons) + len(all_tests)

    if total_items == 0:
        enrollment.progress = 0
        db.session.commit()
        return

    valid_lesson_ids = [les.id for les in all_lessons]
    completed_lessons = (
        LessonProgress.query.filter(
            LessonProgress.enrollment_id == enrollment.id,
            LessonProgress.lesson_id.in_(valid_lesson_ids),
            LessonProgress.is_completed.is_(True),
        ).count()
        if valid_lesson_ids
        else 0
    )

    passed_tests = (
        Score.query.filter_by(enrollment_id=enrollment.id, is_passed=True)
        .distinct(Score.test_id)
        .count()
    )

    done_items = completed_lessons + passed_tests
    enrollment.progress = min(100, int((done_items / total_items) * 100))

    if enrollment.progress >= 100 and enrollment.status == EnrollmentStatus.IN_PROGRESS:
        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completed_date = datetime.now()

    db.session.commit()

