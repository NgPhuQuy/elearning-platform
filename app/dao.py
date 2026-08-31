import hashlib
import uuid
from datetime import datetime, timedelta

import cloudinary.uploader
from flask_login import current_user

from app import TEACHER_APPLICATION_COOLDOWN_DAYS, db, login, momo
from app.models import (
    Answer,
    ApplicationStatus,
    Category,
    Chapter,
    Comment,
    Conversation,
    ConversationMember,
    Course,
    CourseCategory,
    CourseOutcome,
    DocContent,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonProgress,
    LessonType,
    Message,
    MessageReaction,
    Payment,
    PaymentStatus,
    Post,
    PostCate,
    Question,
    ReactionComment,
    ReactionPost,
    Score,
    Teacher,
    TeacherApplication,
    Test,
    User,
    VideoContent,
)


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()


def register_user(username, password, email, phone, avatar, first_name, last_name):
    hashed_password = hash_password(password)
    user = User(
        username=username,
        password=hashed_password,
        email=email,
        phone=phone,
        avatar=avatar,
        first_name=first_name,
        last_name=last_name,
    )
    db.session.add(user)
    db.session.commit()
    return user


def is_username_exist(username):
    return User.query.filter(User.username == username).first()


def is_email_used(email):
    return User.query.filter(User.email == email).first()


def is_phone_used(phone):
    return User.query.filter(User.phone == phone).first()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def change_info(email, phone, file_path, first_name, last_name):
    if email != current_user.email:
        if is_email_used(email):
            return False, "Email đã được sử dụng bởi tài khoản khác."

    current_user.email = email
    current_user.phone = phone
    current_user.avatar = file_path
    current_user.first_name = first_name
    current_user.last_name = last_name
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    return True, None


def change_password(new_password):
    current_user.password = hash_password(new_password)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    return True, None


def get_latest_teacher_application(user_id):
    return TeacherApplication.query.filter_by(user_id=user_id).order_by(TeacherApplication.created_date.desc()).first()


def can_apply_teacher(user_id):
    latest = get_latest_teacher_application(user_id)
    if not latest:
        return True, None

    if latest.status == ApplicationStatus.PENDING:
        return False, "Đơn của bạn đang chờ duyệt, vui lòng đợi kết quả."

    if latest.status == ApplicationStatus.APPROVED:
        return False, "Bạn đã là giảng viên."

    # REJECTED -> áp dụng cooldown
    next_allowed = latest.created_date + timedelta(days=TEACHER_APPLICATION_COOLDOWN_DAYS)
    if datetime.now() < next_allowed:
        remaining = (next_allowed - datetime.now()).days + 1
        return False, f"Đơn trước đã bị từ chối. Bạn cần đợi thêm {remaining} ngày nữa mới được nộp lại."

    return True, None


def create_teacher_application(user_id, **kwargs):
    ok, message = can_apply_teacher(user_id)
    if not ok:
        return None, message

    application = TeacherApplication(user_id=user_id, status=ApplicationStatus.PENDING, **kwargs)
    try:
        db.session.add(application)
        db.session.commit()
        return application, None
    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng thử lại sau!"


def get_teacher_applications(status=None):
    query = TeacherApplication.query
    if status:
        query = query.filter(TeacherApplication.status == status)
    return query.order_by(TeacherApplication.created_date.desc()).all()


def register_teacher(user_id, note=""):
    teacher = Teacher(user_id=user_id, note=note)
    try:
        db.session.add(teacher)
        db.session.commit()
        return teacher
    except Exception:
        db.session.rollback()
        return None


def get_categories():
    return Category.query.order_by(Category.name).all()


def create_course(
    name,
    description,
    image,
    teacher_id,
    level,
    category_ids,
):
    course = Course(name=name, description=description, image=image, teacher_id=teacher_id, level=level)

    try:
        db.session.add(course)
        db.session.flush()

        if category_ids:
            for cate_id in category_ids:
                db.session.add(CourseCategory(course_id=course.id, category_id=cate_id))

        db.session.commit()
        return course

    except Exception:
        db.session.rollback()
        return None


def get_course_details(course_id, teacher_id=None):
    query = Course.query.filter_by(id=course_id)

    if teacher_id is not None:
        query = query.filter_by(teacher_id=teacher_id)

    return query.first()


def save_video_for_lesson(lesson_id, teacher_id, video_url, duration=0):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )

    if not lesson:
        return None

    video = VideoContent.query.filter_by(lesson_id=lesson_id).first()
    if video:
        video.video_url = video_url
        video.duration = duration
    else:
        video = VideoContent(lesson_id=lesson_id, video_url=video_url, duration=duration)
        db.session.add(video)

    lesson.type = LessonType.VIDEO

    try:
        db.session.commit()
        return video
    except Exception:
        db.session.rollback()
        return None


def save_doc_for_lesson(lesson_id, teacher_id, file_url):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )

    if not lesson:
        return None

    doc = DocContent.query.filter_by(lesson_id=lesson_id).first()
    if doc:
        doc.file_url = file_url
    else:
        doc = DocContent(lesson_id=lesson_id, file_url=file_url)
        db.session.add(doc)

    lesson.type = LessonType.DOCUMENT

    try:
        db.session.commit()
        return doc
    except Exception:
        db.session.rollback()
        return None


def clear_video_content(lesson_id, teacher_id):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )
    if not lesson:
        return False

    video = VideoContent.query.filter_by(lesson_id=lesson_id).first()
    if video:
        db.session.delete(video)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return False
    return True


def clear_doc_content(lesson_id, teacher_id):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )
    if not lesson:
        return False

    doc = DocContent.query.filter_by(lesson_id=lesson_id).first()
    if doc:
        db.session.delete(doc)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return False
    return True


def delete_course(course_id, teacher_id):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()

    if not course:
        return False, "Khóa học không tồn tại."

    has_enrollment = Enrollment.query.filter_by(course_id=course_id).first() is not None
    if has_enrollment:
        return False, "Không thể xóa: đã có học viên đăng ký khóa học này."

    try:
        db.session.delete(course)
        db.session.commit()
        return True, None

    except Exception:
        db.session.rollback()
        return False, "Hệ thống lỗi, vui lòng thử lại sau!"


def update_lesson(lesson_id, teacher_id, name=None, description=None, lesson_type=None):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )

    if not lesson:
        return None

    if name:
        lesson.name = name

    if description:
        lesson.description = description

    if lesson_type:
        lesson.type = lesson_type

    try:
        db.session.commit()
        return lesson

    except Exception:
        db.session.rollback()
        return None


def sync_chapters_and_lessons(course_id, teacher_id, chapters_data, files):
    """
    Đồng bộ chapters + lessons từ JSON (chapters_data) gửi lên khi bấm "Lưu thay đổi".
    - Chapter/Lesson có id -> update
    - Chapter/Lesson id=None -> tạo mới
    - Chapter/Lesson đang có trong DB nhưng KHÔNG có trong chapters_data -> xóa (đồng bộ 2 chiều)
    - files: request.files, dùng để lấy video_file_lesson_<id|temp_id> / doc_file_lesson_<id|temp_id>
    """
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return False

    existing_chapter_ids = {c.id for c in course.chapters}
    kept_chapter_ids = set()

    for order, chapter_data in enumerate(chapters_data, start=1):
        chapter_id = chapter_data.get("id")
        name = (chapter_data.get("name") or "").strip()
        description = (chapter_data.get("description") or "").strip()

        if chapter_id:
            chapter = Chapter.query.filter_by(id=int(chapter_id), course_id=course_id).first()
            if not chapter:
                continue
            chapter.name = name
            chapter.description = description
            chapter.order = order
        else:
            chapter = Chapter(name=name, description=description, course_id=course_id, order=order)
            db.session.add(chapter)
            db.session.flush()  # để có chapter.id ngay

        kept_chapter_ids.add(chapter.id)
        _sync_lessons_for_chapter(chapter, chapter_data.get("lessons", []), files)

    # Xóa các chapter không còn xuất hiện trong dữ liệu gửi lên
    for old_id in existing_chapter_ids - kept_chapter_ids:
        old_chapter = Chapter.query.get(old_id)
        if old_chapter:
            db.session.delete(old_chapter)

    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def _sync_lessons_for_chapter(chapter, lessons_data, files):
    existing_lesson_ids = {lesson.id for lesson in chapter.lessons}
    kept_lesson_ids = set()

    for lesson_data in lessons_data:
        lesson_id = lesson_data.get("id")
        temp_id = lesson_data.get("temp_id")
        name = (lesson_data.get("name") or "").strip() or "Bài học"
        description = (lesson_data.get("description") or "").strip()
        type_str = lesson_data.get("type") or "NONE"

        try:
            lesson_type = LessonType[type_str]
        except KeyError:
            lesson_type = LessonType.NONE

        if lesson_id:
            lesson = Lesson.query.filter_by(id=int(lesson_id), chapter_id=chapter.id).first()
            if not lesson:
                continue
            lesson.name = name
            lesson.description = description
            lesson.type = lesson_type
            file_key_id = lesson.id
        else:
            lesson = Lesson(name=name, description=description, type=lesson_type, chapter_id=chapter.id)
            db.session.add(lesson)
            db.session.flush()
            file_key_id = temp_id

        kept_lesson_ids.add(lesson.id)

        # ---- Ép 1 lesson chỉ có 1 loại media: xóa media không khớp type hiện tại ----
        existing_video = VideoContent.query.filter_by(lesson_id=lesson.id).first()
        existing_doc = DocContent.query.filter_by(lesson_id=lesson.id).first()

        if lesson_type != LessonType.VIDEO and existing_video:
            db.session.delete(existing_video)
            existing_video = None

        if lesson_type != LessonType.DOCUMENT and existing_doc:
            db.session.delete(existing_doc)
            existing_doc = None

        # Gắn video mới nếu type là VIDEO và có file gửi kèm
        video_file = files.get(f"video_file_lesson_{file_key_id}")
        if video_file and video_file.filename and lesson_type == LessonType.VIDEO:
            try:
                res = cloudinary.uploader.upload(video_file, resource_type="video", folder="elearning-platform/courses")
                if existing_video:
                    existing_video.video_url = res["secure_url"]
                else:
                    db.session.add(VideoContent(lesson_id=lesson.id, video_url=res["secure_url"]))
            except Exception:
                pass

        # Gắn tài liệu mới nếu type là DOCUMENT và có file gửi kèm
        doc_file = files.get(f"doc_file_lesson_{file_key_id}")
        if doc_file and doc_file.filename and lesson_type == LessonType.DOCUMENT:
            try:
                file_ext = doc_file.filename.rsplit(".", 1)[-1].lower() if "." in doc_file.filename else ""
                public_id = f"doc_lesson_{lesson.id}_{uuid.uuid4().hex[:8]}.{file_ext}"

                res = cloudinary.uploader.upload(
                    doc_file,
                    folder="elearning-platform/courses",
                    public_id=public_id,
                    access_mode="public",
                )
                if existing_doc:
                    existing_doc.file_url = res["secure_url"]
                    existing_doc.file_ext = file_ext
                else:
                    db.session.add(DocContent(lesson_id=lesson.id, file_url=res["secure_url"], file_ext=file_ext))
            except Exception as e:
                print("LỖI UPLOAD DOC:", repr(e))

    for old_id in existing_lesson_ids - kept_lesson_ids:
        old_lesson = Lesson.query.get(old_id)
        if old_lesson:
            db.session.delete(old_lesson)


def delete_lesson(lesson_id, teacher_id):
    lesson = (
        Lesson.query.join(Chapter).join(Course).filter(Lesson.id == lesson_id, Course.teacher_id == teacher_id).first()
    )

    if not lesson:
        return False

    try:
        db.session.delete(lesson)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def get_chapters(course_id):
    return Chapter.query.filter_by(course_id=course_id).order_by(Chapter.order).all()


def get_lessons(chapter_id):
    return Lesson.query.filter_by(chapter_id=chapter_id).all()


def get_lesson_details(lesson_id):
    return Lesson.query.get(lesson_id)


def get_outcomes(course_id):
    return CourseOutcome.query.filter_by(course_id=course_id).all()


def create_outcome(course_id, content):
    outcome = CourseOutcome(course_id=course_id, content=content)

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
    try:
        db.session.commit()
        return True
    except Exception:
        db.session.rollback()
        return False


def delete_outcome(outcome_id):
    outcome = CourseOutcome.query.get(outcome_id)

    if not outcome:
        return False

    try:
        db.session.delete(outcome)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


# enrollment


def get_latest_enrollment(user_id, course_id):
    """
    Lấy enrollment hiện tại của user trong course.

    Ưu tiên enrollment mới nhất theo created_date + id
    để tránh trường hợp 2 enrollment có cùng thời gian tạo.
    """
    return (
        Enrollment.query.filter_by(user_id=user_id, course_id=course_id)
        .order_by(Enrollment.created_date.desc(), Enrollment.id.desc())
        .first()
    )


def is_enrolled(user_id, course_id):
    """
    User được xem là đang có enrollment nếu enrollment mới nhất
    tồn tại và chưa FAILED.
    """
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

    # Lấy enrollment mới nhất
    latest_enrollment = get_latest_enrollment(user_id, course_id)

    # Đang học (IN_PROGRESS)
    if latest_enrollment and latest_enrollment.status == EnrollmentStatus.IN_PROGRESS and not force:
        return None, "Bạn đang trong quá trình học khóa học này."

    # Nếu đã hoàn thành và không phải mua/học lại ép buộc
    if latest_enrollment and latest_enrollment.status == EnrollmentStatus.COMPLETED and not force:
        return None, "Bạn đã hoàn thành khóa học này rồi."

    # Khóa học có phí (nếu không phải thanh toán kích hoạt qua force)
    if not force and course.price and course.price > 0:
        return None, "Khóa học có phí, vui lòng thanh toán trước khi đăng ký."

    # Tạo đợt học mới sạch sẽ (Bảo tồn lịch sử đợt học cũ)
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


def _lesson_has_content(lesson):
    return (lesson.type == LessonType.VIDEO and lesson.video_content) or (
        lesson.type == LessonType.DOCUMENT and lesson.doc_content
    )


def get_test_for_teacher(test_id, teacher_id):
    return Test.query.join(Course).filter(Test.id == test_id, Course.teacher_id == teacher_id).first()


def get_questions(test_id):
    return Question.query.filter_by(test_id=test_id).all()


def sync_questions(test_id, teacher_id, questions_data, pass_score=5):
    test = get_test_for_teacher(test_id, teacher_id)

    if not test:
        return False

    # ==============================
    # LƯU ĐIỂM ĐẠT CỦA BÀI TEST
    # ==============================
    try:
        pass_score = int(pass_score)
    except (TypeError, ValueError):
        pass_score = 5

    # Giới hạn điểm đạt từ 0 -> 10
    pass_score = max(0, min(pass_score, 10))

    test.pass_score = pass_score

    # ==============================
    # ĐỒNG BỘ CÂU HỎI
    # ==============================
    existing_question_ids = {q.id for q in test.questions}
    kept_question_ids = set()

    for question_data in questions_data:
        question_id = question_data.get("id")

        content = (question_data.get("content") or "").strip()

        # Câu hỏi trống thì bỏ qua
        if not content:
            continue

        # --------------------------
        # CÂU HỎI CŨ
        # --------------------------
        if question_id:
            question = Question.query.filter_by(id=int(question_id), test_id=test_id).first()

            if not question:
                continue

            question.content = content

        # --------------------------
        # CÂU HỎI MỚI
        # --------------------------
        else:
            question = Question(test_id=test_id, content=content)

            db.session.add(question)
            db.session.flush()

        kept_question_ids.add(question.id)

        # ==========================
        # ĐỒNG BỘ ĐÁP ÁN
        # ==========================
        existing_answer_ids = {answer.id for answer in question.answers}

        kept_answer_ids = set()

        answers_data = question_data.get("answers", [])

        # Backend cũng giới hạn tối đa 4 đáp án
        answers_data = answers_data[:4]

        for answer_data in answers_data:
            answer_id = answer_data.get("id")

            answer_content = (answer_data.get("content") or "").strip()

            # Đáp án trống thì bỏ qua
            if not answer_content:
                continue

            is_correct = bool(answer_data.get("is_correct"))

            # ----------------------
            # ĐÁP ÁN CŨ
            # ----------------------
            if answer_id:
                answer = Answer.query.filter_by(id=int(answer_id), question_id=question.id).first()

                if not answer:
                    continue

                answer.content = answer_content
                answer.is_correct = is_correct

            # ----------------------
            # ĐÁP ÁN MỚI
            # ----------------------
            else:
                answer = Answer(question_id=question.id, content=answer_content, is_correct=is_correct)

                db.session.add(answer)
                db.session.flush()

            kept_answer_ids.add(answer.id)

        # Xóa đáp án đã bị xóa trên giao diện
        for old_id in existing_answer_ids - kept_answer_ids:
            old_answer = Answer.query.get(old_id)

            if old_answer:
                db.session.delete(old_answer)

    # ==============================
    # XÓA CÂU HỎI ĐÃ BỊ XÓA
    # ==============================
    for old_id in existing_question_ids - kept_question_ids:
        old_question = Question.query.get(old_id)

        if old_question:
            db.session.delete(old_question)

    # ==============================
    # COMMIT
    # ==============================
    try:
        db.session.commit()

        return True

    except Exception:
        db.session.rollback()

        return False


def _get_best_scores_map(enrollment_id):
    """Trả về {test_id: điểm cao nhất} trong enrollment hiện tại."""

    rows = Score.query.filter_by(enrollment_id=enrollment_id).all()

    best = {}

    for row in rows:
        if row.test_id not in best or row.score_value > best[row.test_id]:
            best[row.test_id] = row.score_value

    return best


def recalc_enrollment_progress(enrollment):
    course = enrollment.course
    tests = course.tests

    total_lessons = sum(1 for ch in course.chapters for lesson in ch.lessons if _lesson_has_content(lesson))

    done_lessons = LessonProgress.query.filter_by(
        enrollment_id=enrollment.id,
        is_completed=True,
    ).count()

    # Lấy điểm cao nhất VÀ số lần đã làm của từng test trong enrollment hiện tại
    scores = Score.query.filter_by(enrollment_id=enrollment.id).all()

    best_scores = {}
    attempts_count = {}

    for row in scores:
        attempts_count[row.test_id] = attempts_count.get(row.test_id, 0) + 1

        if row.test_id not in best_scores or row.score_value > best_scores[row.test_id]:
            best_scores[row.test_id] = row.score_value

    def is_test_resolved(t):
        """
        Một test được coi là "đã xong" (tính vào tiến độ) khi:
        - Đã đạt điểm pass_score, HOẶC
        - Đã dùng hết số lần làm cho phép (không còn cơ hội thi lại).
        Nếu vẫn còn lượt làm mà chưa đạt -> CHƯA xong, không được
        tính vào tiến độ / không được kéo enrollment sang FAILED.
        """
        best = best_scores.get(t.id)

        if best is None:
            return False

        if best >= t.pass_score:
            return True

        if t.max_attempts and t.max_attempts > 0:
            return attempts_count.get(t.id, 0) >= t.max_attempts

        # Không giới hạn số lần làm -> luôn còn cơ hội, chưa thể coi là xong
        return False

    tests_taken = sum(1 for t in tests if is_test_resolved(t))

    total_items = total_lessons + len(tests)
    done_items = done_lessons + tests_taken

    enrollment.progress = int(done_items / total_items * 100) if total_items else 0

    if enrollment.progress >= 100:
        if tests:
            all_passed = all(best_scores.get(t.id, 0) >= t.pass_score for t in tests)

            if all_passed:
                enrollment.status = EnrollmentStatus.COMPLETED
                enrollment.completed_date = datetime.now()
            else:
                enrollment.status = EnrollmentStatus.FAILED
                enrollment.completed_date = None
        else:
            enrollment.status = EnrollmentStatus.COMPLETED
            enrollment.completed_date = datetime.now()

    elif enrollment.status in (
        EnrollmentStatus.COMPLETED,
        EnrollmentStatus.FAILED,
    ):
        enrollment.status = EnrollmentStatus.IN_PROGRESS
        enrollment.completed_date = None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    return enrollment.progress


def _ensure_lesson_completable(lesson):

    if not _lesson_has_content(lesson):
        return False, "Bài học này chưa có nội dung, không thể đánh dấu hoàn thành."
    return True, None


def mark_lesson_completed(user_id, course_id, lesson_id):

    enrollment = get_latest_enrollment(user_id, course_id)

    if not enrollment or enrollment.status == EnrollmentStatus.FAILED:
        return False, "Bạn chưa đăng ký khóa học này."

    lesson = Lesson.query.get(lesson_id)

    if not lesson or lesson.chapter.course_id != course_id:
        return False, "Bài học không hợp lệ."

    ok, error = _ensure_lesson_completable(lesson)

    if not ok:
        return False, error

    # LessonProgress liên kết với Enrollment thông qua enrollment_id
    lp = LessonProgress.query.filter_by(
        enrollment_id=enrollment.id,
        lesson_id=lesson_id,
    ).first()

    if not lp:
        lp = LessonProgress(
            enrollment_id=enrollment.id,
            lesson_id=lesson_id,
        )
        db.session.add(lp)

    lp.is_completed = True
    lp.completed_at = datetime.now()
    lp.last_watched_at = datetime.now()

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return False, "Hệ thống lỗi, vui lòng thử lại sau!"

    recalc_enrollment_progress(enrollment)

    return True, None


def get_lesson_progress_map(user_id, course_id):

    enrollment = get_latest_enrollment(user_id, course_id)

    if not enrollment:
        return {}

    rows = LessonProgress.query.filter_by(
        enrollment_id=enrollment.id,
        is_completed=True,
    ).all()

    return {row.lesson_id: True for row in rows}


def is_chapter_completed(user_id, course_id, chapter_id):

    enrollment = get_latest_enrollment(user_id, course_id)

    if not enrollment or enrollment.status == EnrollmentStatus.FAILED:
        return False

    chapter = Chapter.query.get(chapter_id)

    if not chapter or chapter.course_id != course_id:
        return False

    lessons_with_content = [lesson for lesson in chapter.lessons if _lesson_has_content(lesson)]

    if not lessons_with_content:
        return True

    completed_ids = {
        row.lesson_id
        for row in LessonProgress.query.filter_by(
            enrollment_id=enrollment.id,
            is_completed=True,
        ).all()
    }

    return all(lesson.id in completed_ids for lesson in lessons_with_content)


def get_test_details(test_id):
    return Test.query.get(test_id)


def get_course_tests(course_id):
    return Test.query.filter_by(course_id=course_id).all()


def get_test_attempts(user_id, course_id, test_id):
    """
    Lấy toàn bộ lịch sử làm test của enrollment hiện tại.
    """

    enrollment = get_latest_enrollment(user_id, course_id)

    if not enrollment:
        return []

    return (
        Score.query.filter_by(
            enrollment_id=enrollment.id,
            test_id=test_id,
        )
        .order_by(Score.attempt_number.desc(), Score.completed_at.desc())
        .all()
    )


def can_take_test(user_id, test):

    enrollment = get_latest_enrollment(user_id, test.course_id)

    if not enrollment:
        return False, "Bạn cần đăng ký khóa học này trước khi làm bài kiểm tra."

    # Chỉ chặn nếu enrollment vẫn FAILED.
    # Sau khi bấm "Làm lại", enroll_course() đã chuyển nó về IN_PROGRESS.
    if enrollment.status == EnrollmentStatus.FAILED:
        return False, "Bạn cần bấm Làm lại khóa học trước khi làm bài kiểm tra."

    # ==========================================================
    # KIỂM TRA CHƯƠNG
    # ==========================================================

    if test.chapter_id:
        if not is_chapter_completed(user_id, test.course_id, test.chapter_id):
            return False, "Bạn cần học xong chương này trước khi làm bài kiểm tra."

    # ==========================================================
    # KIỂM TRA SỐ LẦN LÀM
    # ==========================================================

    if test.max_attempts and test.max_attempts > 0:
        attempts_used = Score.query.filter_by(
            enrollment_id=enrollment.id,
            test_id=test.id,
        ).count()

        if attempts_used >= test.max_attempts:
            return (False, f"Bạn đã hết số lần làm bài cho phép ({test.max_attempts} lần).")

    return True, None


def submit_test_score(user_id, course_id, test_id, answers):

    test = Test.query.filter_by(id=test_id, course_id=course_id).first()

    if not test:
        return None, "Bài kiểm tra không tồn tại."

    ok, error = can_take_test(user_id, test)

    if not ok:
        return None, error

    enrollment = get_latest_enrollment(user_id, course_id)

    questions = test.questions
    total = len(questions)

    if total == 0:
        return None, "Bài kiểm tra chưa có câu hỏi nào."

    correct = 0

    for question in questions:
        selected_answer_id = answers.get(question.id) or answers.get(str(question.id))

        if not selected_answer_id:
            continue

        selected_answer = Answer.query.filter_by(id=int(selected_answer_id), question_id=question.id).first()

        if selected_answer and selected_answer.is_correct:
            correct += 1

    score_value = round(correct / total * 10, 2)

    is_passed = score_value >= test.pass_score

    attempt_number = (
        Score.query.filter_by(
            enrollment_id=enrollment.id,
            test_id=test_id,
        ).count()
        + 1
    )

    score = Score(
        enrollment_id=enrollment.id,
        test_id=test_id,
        attempt_number=attempt_number,
        score_value=score_value,
        is_passed=is_passed,
        completed_at=datetime.now(),
    )

    try:
        db.session.add(score)
        db.session.commit()

    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng thử lại sau!"

    recalc_enrollment_progress(enrollment)

    return score, None


def activate_course(course_id, teacher_id):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return None, "Khóa học không tồn tại."

    if course.activate:
        return course, None

    course.activate = True
    try:
        db.session.commit()
        return course, None
    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng thử lại sau!"


def get_my_enrollments(user_id):
    """
    Lấy enrollment mới nhất của mỗi khóa học của user.

    Nếu user đã học lại khóa học sau khi FAILED,
    profile chỉ hiển thị lần enrollment mới nhất.
    """

    enrollments = Enrollment.query.filter_by(user_id=user_id).order_by(Enrollment.created_date.desc()).all()

    latest_by_course = {}

    for enrollment in enrollments:
        if enrollment.course_id not in latest_by_course:
            latest_by_course[enrollment.course_id] = enrollment

    return list(latest_by_course.values())


# forum
def get_posts(keyword=None, solved=None, category_id=None):
    query = Post.query

    if keyword:
        query = query.filter(Post.title.contains(keyword))

    if solved is not None:
        query = query.filter(Post.is_solved == solved)

    if category_id:
        query = query.join(Post.categories).filter(PostCate.id == category_id)

    return query.order_by(Post.created_date.desc()).all()


def get_post_by_id(post_id):
    post = Post.query.get(post_id)

    if post:
        post.view_count += 1
        db.session.commit()

    return post


def create_post(title, content, category_ids, user_id, image=None):
    post = Post(title=title, content=content, image=image, user_id=user_id)

    db.session.add(post)

    for cid in category_ids:
        category = PostCate.query.get(int(cid))
        if category:
            post.categories.append(category)

    db.session.commit()

    return post


def add_comment(post_id, user_id, content, parent_comment_id=None):
    c = Comment(content=content, post_id=post_id, user_id=user_id, parent_comment_id=parent_comment_id)

    db.session.add(c)
    db.session.commit()


# chat
def get_conversation(conversation_id):
    return Conversation.query.get(conversation_id)


def get_conversations(user_id):
    return (
        Conversation.query.join(ConversationMember)
        .filter(ConversationMember.user_id == user_id)
        .order_by(Conversation.updated_date.desc())
        .all()
    )


def get_private_conversation(user1_id, user2_id):
    conversations = (
        Conversation.query.filter_by(is_group=False)
        .join(ConversationMember)
        .filter(ConversationMember.user_id.in_([user1_id, user2_id]))
        .all()
    )

    for conversation in conversations:
        ids = {m.user_id for m in conversation.members}
        if ids == {user1_id, user2_id}:
            return conversation

    return None


def create_private_conversation(user1_id, user2_id):

    if user1_id == user2_id:
        return None
    existed = get_private_conversation(user1_id, user2_id)

    if existed:
        return existed

    conversation = Conversation(is_group=False)

    try:
        db.session.add(conversation)
        db.session.flush()

        db.session.add(
            ConversationMember(
                conversation_id=conversation.id,
                user_id=user1_id,
            )
        )

        db.session.add(ConversationMember(conversation_id=conversation.id, user_id=user2_id))

        db.session.commit()

        return conversation

    except Exception:
        db.session.rollback()
        return None


def get_message(message_id):
    return Message.query.get(message_id)


def get_messages(conversation_id):
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_date.asc()).all()


def get_latest_message(conversation_id):
    return Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_date.desc()).first()


def get_other_member(conversation_id, current_user_id):
    member = ConversationMember.query.filter(
        ConversationMember.conversation_id == conversation_id,
        ConversationMember.user_id != current_user_id,
    ).first()

    if not member:
        return None

    return User.query.get(member.user_id)


def is_member(conversation_id, user_id):
    return ConversationMember.query.filter_by(conversation_id=conversation_id, user_id=user_id).first() is not None


def get_message_reactions(message_id):
    return MessageReaction.query.filter_by(message_id=message_id).all()


def send_message(conversation_id, sender_id, content, attachment=None):
    conversation = Conversation.query.get(conversation_id)

    if not conversation:
        return None

    message = Message(conversation_id=conversation_id, sender_id=sender_id, content=content, attachment=attachment)

    try:
        db.session.add(message)

        conversation.updated_date = datetime.now()

        db.session.commit()

        return message

    except Exception:
        db.session.rollback()
        return None


def delete_message(message_id):
    message = Message.query.get(message_id)

    if not message:
        return False

    try:
        db.session.delete(message)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def edit_message(
    message_id,
    content,
):
    message = Message.query.get(message_id)

    if not message:
        return None

    message.content = content
    message.is_edited = True

    try:
        db.session.commit()
        return message

    except Exception:
        db.session.rollback()
        return None


def react_message(
    message_id,
    user_id,
    emoji,
):
    reaction = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=user_id,
    ).first()

    try:
        if reaction:
            reaction.emoji = emoji
        else:
            reaction = MessageReaction(
                message_id=message_id,
                user_id=user_id,
                emoji=emoji,
            )
            db.session.add(reaction)

        db.session.commit()

        return reaction

    except Exception:
        db.session.rollback()
        return None


def remove_reaction(
    message_id,
    user_id,
):
    reaction = MessageReaction.query.filter_by(
        message_id=message_id,
        user_id=user_id,
    ).first()

    if not reaction:
        return False

    try:
        db.session.delete(reaction)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def update_last_read(
    conversation_id,
    user_id,
):
    member = ConversationMember.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
    ).first()

    if not member:
        return False

    member.last_read = datetime.now()

    try:
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def count_unread(user_id):
    total = 0

    members = ConversationMember.query.filter_by(user_id=user_id).all()

    for member in members:
        query = Message.query.filter(
            Message.conversation_id == member.conversation_id,
            Message.sender_id != user_id,
        )

        if member.last_read:
            query = query.filter(Message.created_date > member.last_read)

        total += query.count()

    return total


def search_messages(
    conversation_id,
    keyword,
):
    return (
        Message.query.filter(
            Message.conversation_id == conversation_id,
            Message.content.contains(keyword),
        )
        .order_by(Message.created_date.desc())
        .all()
    )


def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def search_users(keyword, current_user_id):
    keyword = keyword.strip()

    if not keyword:
        return []

    pattern = f"%{keyword}%"

    return (
        User.query.filter(
            User.id != current_user_id,
            db.or_(
                User.username.ilike(pattern),
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                db.func.concat(User.first_name, " ", User.last_name).ilike(pattern),
            ),
        )
        .limit(10)
        .all()
    )


def get_courses_by_teacher_id(teacher_id):
    return Course.query.filter_by(teacher_id=teacher_id).order_by(Course.created_date.desc()).all()


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


def accept_answer(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post = comment.post

    if post.user_id != current_user.id:
        return False

    Comment.query.filter_by(post_id=post.id, is_accepted=True).update({"is_accepted": False})

    comment.is_accepted = True

    post.is_solved = True

    db.session.commit()

    return True


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


def sync_tests(course_id, teacher_id, tests_data):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()

    if not course:
        return False

    existing_test_ids = {t.id for t in course.tests}
    kept_test_ids = set()

    for test_data in tests_data:
        test_id = test_data.get("id")
        name = (test_data.get("name") or "").strip()
        chapter_id = test_data.get("chapter_id") or None

        if chapter_id:
            try:
                chapter = Chapter.query.filter_by(id=int(chapter_id), course_id=course_id).first()

                if not chapter:
                    chapter_id = None
            except (TypeError, ValueError):
                chapter_id = None

        try:
            duration = int(test_data.get("duration") or 0)
        except (TypeError, ValueError):
            duration = 0

        try:
            max_attempts = int(test_data.get("max_attempts") or 0)
        except (TypeError, ValueError):
            max_attempts = 0

        if test_id:
            test = Test.query.filter_by(id=int(test_id), course_id=course_id).first()

            if not test:
                continue

            test.name = name
            test.chapter_id = chapter_id
            test.duration = duration
            test.max_attempts = max_attempts

        else:
            test = Test(
                course_id=course_id, chapter_id=chapter_id, name=name, duration=duration, max_attempts=max_attempts
            )

            db.session.add(test)

        db.session.flush()
        kept_test_ids.add(test.id)

    # Xóa các test cũ không còn tồn tại trong dữ liệu gửi lên
    for old_id in existing_test_ids - kept_test_ids:
        old_test = Test.query.get(old_id)

        if old_test:
            db.session.delete(old_test)

    try:
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def update_chapter(chapter_id, teacher_id, name=None, description=None):
    chapter = Chapter.query.join(Course).filter(Chapter.id == chapter_id, Course.teacher_id == teacher_id).first()

    if not chapter:
        return None

    if name:
        chapter.name = name

    if description:
        chapter.description = description

    try:
        db.session.commit()
        return chapter

    except Exception:
        db.session.rollback()
        return None


def delete_chapter(chapter_id, teacher_id):
    chapter = Chapter.query.join(Course).filter(Chapter.id == chapter_id, Course.teacher_id == teacher_id).first()

    if not chapter:
        return False

    try:
        db.session.delete(chapter)
        db.session.commit()
        return True

    except Exception:
        db.session.rollback()
        return False


def create_lesson(teacher_id, chapter_id, name, description, lesson_type):
    chapter = Chapter.query.join(Course).filter(Chapter.id == chapter_id, Course.teacher_id == teacher_id).first()

    if not chapter:
        return None
    lesson = Lesson(name=name, description=description, type=LessonType[lesson_type], chapter_id=chapter.id)
    try:
        db.session.add(lesson)
        db.session.commit()
        return lesson
    except Exception:
        db.session.rollback()
        return None


def _vote_entity(model_cls, fk_field, target_id, user_id, vote_type):
    filter_kwargs = {fk_field: target_id, "user_id": user_id}
    reaction = model_cls.query.filter_by(**filter_kwargs).first()

    if reaction:
        if reaction.vote_type == vote_type:
            db.session.delete(reaction)
        else:
            reaction.vote_type = vote_type
    else:
        filter_kwargs["vote_type"] = vote_type
        db.session.add(model_cls(**filter_kwargs))

    db.session.commit()


def vote_post(post_id, user_id, vote_type):
    return _vote_entity(ReactionPost, "post_id", post_id, user_id, vote_type)


def vote_comment(comment_id, user_id, vote_type):
    return _vote_entity(ReactionComment, "comment_id", comment_id, user_id, vote_type)


def _calculate_score(reactions):
    return sum(r.vote_type.value for r in reactions)


def get_post_score(post):
    return _calculate_score(post.reactions)


def get_comment_score(comment):
    return _calculate_score(comment.reactions)


def get_post_categories():
    return PostCate.query.order_by(PostCate.name).all()


def get_related_posts(post_id, limit=5):
    post = Post.query.get(post_id)
    if not post:
        return []

    cate_ids = [c.id for c in post.categories]

    return (
        Post.query.join(Post.categories)
        .filter(Post.id != post.id)
        .filter(PostCate.id.in_(cate_ids))
        .distinct()
        .limit(limit)
        .all()
    )


def get_user_post_vote(post_id, user_id):
    return ReactionPost.query.filter_by(post_id=post_id, user_id=user_id).first()


def get_course_sale():
    return Course.query.filter_by(is_sale=True).all()


def get_question_today():
    return Post.query.filter(db.func.date(Post.created_date) == datetime.now().date()).all()


# =========================================================================
# PAYMENT DAO FUNCTIONS
# =========================================================================


def create_payment(user_id, course_id):
    course = Course.query.get(course_id)
    if not course:
        return None, "Khóa học không tồn tại."
    if not course.activate:
        return None, "Khóa học chưa được công khai."
    if is_enrolled(user_id, course_id):
        return None, "Bạn đã đăng ký khóa học này rồi."
    if not course.price or course.price <= 0:
        return None, "Khóa học này miễn phí, hãy bấm Đăng ký học."

    order_id = momo.new_order_id(course_id)
    request_id = momo.new_request_id()
    order_info = f"Thanh toán khóa học {course.name}"

    payment = Payment(
        user_id=user_id,
        course_id=course_id,
        order_id=order_id,
        request_id=request_id,
        amount=course.price,
        status=PaymentStatus.PENDING,
    )
    try:
        db.session.add(payment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return None, "Không thể khởi tạo giao dịch thanh toán."

    pay_url, error = momo.create_payment_request(
        order_id=order_id,
        request_id=request_id,
        amount=course.price,
        order_info=order_info,
    )
    if error:
        payment.status = PaymentStatus.FAILED
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return None, error

    return pay_url, None


def confirm_payment_success(order_id, momo_trans_id=None, pay_type=None):
    payment = Payment.query.filter_by(order_id=order_id).first()
    if not payment:
        return None

    if payment.status == PaymentStatus.SUCCESS:
        return payment

    payment.status = PaymentStatus.SUCCESS
    payment.momo_trans_id = momo_trans_id
    payment.pay_type = pay_type
    payment.paid_at = datetime.now()

    # Kích hoạt Enrollment mới cho học viên
    enroll_course(payment.user_id, payment.course_id, force=True, price=payment.amount)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return payment

    # Gửi hóa đơn qua email nếu chưa gửi
    if not payment.invoice_sent and payment.user and payment.course:
        try:
            from app.mailer import send_invoice_email

            sent, _ = send_invoice_email(payment, payment.user, payment.course)
            if sent:
                payment.invoice_sent = True
                db.session.commit()
        except Exception:
            pass

    return payment


def confirm_payment_failed(order_id):
    payment = Payment.query.filter_by(order_id=order_id).first()
    if payment and payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.FAILED
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    return payment


def get_payment_by_order_id(order_id):
    return Payment.query.filter_by(order_id=order_id).first()


def get_my_payments(user_id):
    return Payment.query.filter_by(user_id=user_id).order_by(Payment.created_date.desc()).all()
