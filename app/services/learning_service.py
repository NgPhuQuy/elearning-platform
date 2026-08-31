from app import dao


def get_doc_kind(ext):
    ext = (ext or "").lower()
    if ext == "pdf":
        return "pdf"
    if ext in ("doc", "docx", "ppt", "pptx", "xls", "xlsx"):
        return "office"
    if ext in ("png", "jpg", "jpeg", "gif", "webp"):
        return "image"
    return "other"


def get_my_learning(user_id):
    return dao.get_my_enrollments(user_id)


def enroll_course(user_id, course_id):
    return dao.enroll_course(user_id=user_id, course_id=course_id)


def get_learn_context(course_id, user_id, lesson_id=None):
    if not dao.is_enrolled(user_id, course_id):
        return None

    course = dao.get_course_details(course_id)
    chapters = dao.get_chapters(course_id)

    current_lesson = None
    if lesson_id:
        current_lesson = dao.get_lesson_details(lesson_id)

    if not current_lesson:
        for chapter in chapters:
            if chapter.lessons:
                current_lesson = chapter.lessons[0]
                break

    doc_kind = None
    if current_lesson and current_lesson.doc_content:
        doc_kind = get_doc_kind(current_lesson.doc_content.file_ext or "")
        dao.mark_lesson_completed(user_id, course_id, current_lesson.id)

    enrollment = dao.get_latest_enrollment(user_id, course_id)
    progress_map = dao.get_lesson_progress_map(user_id, course_id)
    tests = dao.get_course_tests(course_id)

    return {
        "course": course,
        "chapters": chapters,
        "current_lesson": current_lesson,
        "doc_kind": doc_kind,
        "enrollment": enrollment,
        "progress_map": progress_map,
        "tests": tests,
    }


def mark_lesson_completed(user_id, course_id, lesson_id):
    return dao.mark_lesson_completed(user_id, course_id, lesson_id)
