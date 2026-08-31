import json

from app import dao
from app.models import Course
from app.services.upload_service import upload_file


def get_all_active_courses():
    courses = Course.query.filter_by(activate=True).order_by(Course.id.desc()).all()
    categories = dao.get_categories()
    return courses, categories


def get_teacher_courses(teacher_id):
    return dao.get_courses_by_teacher_id(teacher_id)


def get_course_detail(course_id, user_id=None):
    course = Course.query.get_or_404(course_id)
    is_enrolled = False
    enrollment = None
    if user_id:
        is_enrolled = dao.is_enrolled(user_id, course_id)
        enrollment = dao.get_latest_enrollment(user_id, course_id)

    chapters = dao.get_chapters(course_id)
    outcomes = dao.get_outcomes(course_id)

    return {
        "course": course,
        "chapters": chapters,
        "outcomes": outcomes,
        "is_enrolled": is_enrolled,
        "enrollment": enrollment,
    }


def create_course(teacher_id, form_data, files):
    name = form_data.get("name", "").strip()
    description = form_data.get("description", "").strip()
    if not name:
        return None, "Vui lòng nhập tên khóa học!"

    image_file = files.get("image")
    image_url, _ = upload_file(image_file, folder="elearning-platform/courses")

    course = dao.create_course(
        name=name,
        description=description,
        image=image_url,
        teacher_id=teacher_id,
        level=form_data.get("level"),
        category_ids=form_data.getlist("category_ids"),
    )
    if course:
        outcomes = form_data.getlist("outcomes")
        for content in outcomes:
            if content.strip():
                dao.create_outcome(course_id=course.id, content=content.strip())
        return course, None
    return None, "Không thể tạo khóa học!"


def update_course(course_id, teacher_id, form_data, files):
    course = dao.get_course_details(course_id, teacher_id=teacher_id)
    if not course:
        return None, "Khóa học không tồn tại hoặc bạn không có quyền!"

    tests_data_raw = form_data.get("tests_data")
    if tests_data_raw:
        try:
            tests_data = json.loads(tests_data_raw)
        except (ValueError, TypeError):
            tests_data = []
        dao.sync_tests(course_id=course_id, teacher_id=teacher_id, tests_data=tests_data)

    image_file = files.get("image")
    image_url, _ = upload_file(image_file, folder="elearning-platform/courses")

    price_raw = form_data.get("price")
    price = None
    if price_raw not in (None, ""):
        try:
            price = max(0, int(price_raw))
        except ValueError:
            price = None
    elif not course.activate:
        price = 0

    was_draft = not course.activate
    action = form_data.get("action", "save")

    dao.update_course(
        course_id=course_id,
        teacher_id=teacher_id,
        name=form_data.get("name"),
        description=form_data.get("description"),
        image=image_url,
        level=form_data.get("level"),
        category_ids=form_data.getlist("category_ids"),
        price=price,
    )

    outcomes = form_data.getlist("outcomes")
    dao.replace_outcomes(course_id, outcomes)

    chapters_data_raw = form_data.get("chapters_data")
    if chapters_data_raw:
        try:
            chapters_data = json.loads(chapters_data_raw)
        except (ValueError, TypeError):
            chapters_data = []
        if chapters_data:
            dao.sync_chapters_and_lessons(
                course_id=course_id,
                teacher_id=teacher_id,
                chapters_data=chapters_data,
                files=files,
            )

    if was_draft and action == "publish":
        dao.activate_course(course_id, teacher_id=teacher_id)

    return course, None


def delete_course(course_id, teacher_id):
    return dao.delete_course(course_id, teacher_id)


def activate_course(course_id, teacher_id):
    return dao.activate_course(course_id, teacher_id)
