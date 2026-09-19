import uuid

import cloudinary.uploader

from app import db
from app.models import (
    Category,
    Chapter,
    Course,
    CourseCategory,
    CourseLevel,
    CourseOutcome,
    Lesson,
)


def _normalize_id(value):
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return None
    return normalized if normalized > 0 else None


def get_categories():
    return Category.query.all()


def get_courses(keyword=None, category_id=None):
    query = Course.query.filter_by(is_active=True)
    if keyword:
        query = query.filter(Course.name.contains(keyword))
    if category_id:
        query = query.join(Course.course_category).filter(CourseCategory.category_id == category_id)
    return query.all()


def get_courses_by_teacher_id(teacher_id):
    return Course.query.filter_by(teacher_id=teacher_id).order_by(Course.created_date.desc()).all()


def get_course_details(course_id, teacher_id=None):
    if teacher_id:
        return Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    return Course.query.get(course_id)


def get_course_sale():
    return Course.query.filter_by(is_sale=True).all()


def create_course(name, description, image, teacher_id, level=None, category_ids=None):
    course = Course(
        name=name,
        description=description,
        image=image,
        teacher_id=teacher_id,
        level=CourseLevel[level] if level else CourseLevel.BASIC,
    )
    db.session.add(course)
    db.session.commit()

    if category_ids:
        for cate_id in category_ids:
            db.session.add(CourseCategory(course_id=course.id, category_id=cate_id))
        db.session.commit()

    return course


def update_course(
    course_id, teacher_id, name=None, description=None, image=None, level=None, category_ids=None, price=None
):
    course = Course.query.filter(Course.id == course_id, Course.teacher_id == teacher_id).first()
    if course:
        if name:
            course.name = name
        if description:
            course.description = description
        if image:
            course.image = image
        if level:
            course.level = level
        if price is not None and not course.activate:
            course.price = price

        if category_ids is not None:
            CourseCategory.query.filter_by(course_id=course.id).delete()
            for cate_id in category_ids:
                db.session.add(CourseCategory(course_id=course.id, category_id=cate_id))
        try:
            db.session.commit()
            return course
        except Exception:
            db.session.rollback()
            return None
    return None


def delete_course(course_id, teacher_id):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return False, "Khóa học không tồn tại hoặc bạn không có quyền."
    if course.activate:
        return False, "Không thể xóa khóa học đã công khai."

    try:
        db.session.delete(course)
        db.session.commit()
        return True, None
    except Exception:
        db.session.rollback()
        return False, "Không thể xóa khóa học này do có dữ liệu liên quan."


def activate_course(course_id, teacher_id):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return None, "Khóa học không tồn tại hoặc bạn không có quyền."

    course.activate = True
    try:
        db.session.commit()
        return course, None
    except Exception:
        db.session.rollback()
        return None, "Không thể công khai khóa học."


def get_outcomes(course_id):
    return CourseOutcome.query.filter_by(course_id=course_id).all()


def create_outcome(course_id, content):
    outcome = CourseOutcome(content=content, course_id=course_id)
    try:
        db.session.add(outcome)
        db.session.commit()
        return outcome
    except Exception:
        db.session.rollback()
        return None


def replace_outcomes(course_id, contents):
    CourseOutcome.query.filter_by(course_id=course_id).delete()
    for content in contents:
        content = content.strip()
        if content:
            db.session.add(CourseOutcome(course_id=course_id, content=content))
    db.session.commit()


def get_chapters(course_id):
    return Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order).all()


def create_chapter(course_id, teacher_id, name, description):
    course = Course.query.filter(Course.id == course_id, Course.teacher_id == teacher_id).first()
    if not course:
        return None

    chapter = Chapter(name=name, description=description, course_id=course.id)
    try:
        db.session.add(chapter)
        db.session.commit()
        return chapter
    except Exception:
        db.session.rollback()
        return None


def delete_chapter(chapter_id, teacher_id):
    chapter = Chapter.query.join(Course).filter(Chapter.id == chapter_id, Course.teacher_id == teacher_id).first()
    if chapter:
        db.session.delete(chapter)
        db.session.commit()
        return True
    return False


def get_lesson_details(lesson_id):
    return Lesson.query.get(lesson_id)


def delete_lesson(lesson_id, teacher_id):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )
    if lesson:
        db.session.delete(lesson)
        db.session.commit()
        return True
    return False


def sync_chapters_and_lessons(course_id, teacher_id, chapters_data, files=None):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return {}

    chapter_ids_by_temp_id = {}
    incoming_chap_ids = {
        chapter_id
        for chapter_id in (_normalize_id(c.get("id")) for c in chapters_data)
        if chapter_id is not None
    }
    for old_chap in course.chapters:
        if old_chap.id not in incoming_chap_ids:
            db.session.delete(old_chap)
    db.session.flush()

    for chap_order, chap_data in enumerate(chapters_data, start=1):
        chap_id = _normalize_id(chap_data.get("id"))
        if chap_id:
            chapter = Chapter.query.filter_by(id=chap_id, course_id=course_id).first()
            if chapter:
                chapter.name = chap_data.get("name", chapter.name)
                chapter.description = chap_data.get("description", chapter.description)
                chapter.order = chap_order
        else:
            chapter = Chapter(
                course_id=course_id,
                name=chap_data.get("name", ""),
                description=chap_data.get("description", ""),
                order=chap_order,
            )
            db.session.add(chapter)
            db.session.flush()
            if chap_data.get("temp_id"):
                chapter_ids_by_temp_id[chap_data["temp_id"]] = chapter.id

        if not chapter:
            continue

        lessons_data = chap_data.get("lessons", [])
        incoming_les_ids = {
            lesson_id
            for lesson_id in (_normalize_id(les.get("id")) for les in lessons_data)
            if lesson_id is not None
        }
        for old_les in chapter.lessons:
            if old_les.id not in incoming_les_ids:
                db.session.delete(old_les)
        db.session.flush()

        for les_data in lessons_data:
            les_id = _normalize_id(les_data.get("id"))
            les_type_str = les_data.get("type", "NONE")
            file_key = les_data.get("file_key")
            if not file_key and les_type_str in {"VIDEO", "DOCUMENT"}:
                lesson_key = les_id or les_data.get("temp_id")
                if lesson_key:
                    prefix = "video" if les_type_str == "VIDEO" else "doc"
                    file_key = f"{prefix}_file_lesson_{lesson_key}"
            uploaded_file = files.get(file_key) if files and file_key else None

            if les_id:
                lesson = Lesson.query.filter_by(id=les_id, chapter_id=chapter.id).first()
                if lesson:
                    lesson.name = les_data.get("name", lesson.name)
                    lesson.description = les_data.get("description", lesson.description)
            else:
                lesson = Lesson(
                    name=les_data.get("name", ""),
                    chapter_id=chapter.id,
                    description=les_data.get("description", ""),
                )
                db.session.add(lesson)
                db.session.flush()

            if not lesson:
                continue

            if les_type_str == "VIDEO":
                if uploaded_file and uploaded_file.filename:
                    res = cloudinary.uploader.upload(
                        uploaded_file,
                        resource_type="video",
                        folder="elearning-platform/lessons/videos",
                        public_id=f"video_{uuid.uuid4().hex[:8]}",
                    )
                    lesson.file_url = res["secure_url"]
                elif les_data.get("video_url"):
                    lesson.file_url = les_data["video_url"]

            elif les_type_str == "DOCUMENT":
                if uploaded_file and uploaded_file.filename:
                    res = cloudinary.uploader.upload(
                        uploaded_file,
                        resource_type="raw",
                        folder="elearning-platform/lessons/docs",
                        public_id=f"doc_{uuid.uuid4().hex[:8]}",
                    )
                    lesson.file_url = res["secure_url"]
                elif les_data.get("content_text") is not None:
                    lesson.content = les_data["content_text"]

    db.session.commit()
    return chapter_ids_by_temp_id
