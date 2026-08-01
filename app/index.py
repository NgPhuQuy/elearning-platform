import json
import uuid

import cloudinary.uploader
from flask import jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import admin, app, dao, db, momo, oauth  # noqa: F401  # Register admin routes.
from app.dao import register_user
from app.decorator import anonymous_required, login_required, teacher_required
from app.models import Comment, Course, Post, PostCate, User, VoteType


@app.context_processor
def inject_common():
    new_question_today = dao.get_question_today()
    course_on_sale = dao.get_course_sale()
    return {
        "new_question_today": len(new_question_today),
        "course_on_sale": len(course_on_sale),
        "posts": dao.get_posts(),
        "dao": dao,
    }


@app.get("/healthz")
def healthz():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok"})
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"status": "unavailable"}), 503
    finally:
        db.session.remove()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
@anonymous_required
def register():
    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        username = request.form.get("username")
        email = request.form.get("email")
        phone = request.form.get("phone")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")

        if not all([password, confirm, username, email, phone, first_name, last_name]):
            return jsonify({"success": False, "error": "Vui lòng nhập đầy đủ thông tin!"}), 400

        if password != confirm:
            return jsonify({"success": False, "error": "Mật khẩu không khớp!"}), 400

        if len(password) < 8:
            return (
                jsonify({"success": False, "error": "Mật khẩu phải từ 8 ký tự trở lên!"}),
                400,
            )

        if dao.is_username_exist(username=username):
            return jsonify({"success": False, "error": "Username đã tồn tại!"}), 400

        if dao.is_email_used(email=email):
            return jsonify({"success": False, "error": "Email đã được sử dụng!"}), 400

        if dao.is_phone_used(phone=phone):
            return (
                jsonify({"success": False, "error": "Số điện thoại này đã được đăng ký!"}),
                400,
            )

        avatar = request.files.get("avatar")
        file_path = None
        if avatar:
            try:
                res = cloudinary.uploader.upload(avatar, folder="elearning-platform/avatars")
                file_path = res["secure_url"]
            except Exception:
                return jsonify({"success": False, "error": "Tải file thất bại!"}), 500

        try:
            user = register_user(username, password, email, phone, file_path, first_name, last_name)
            login_user(user)
            return jsonify({"success": True, "redirect": "/"})
        except Exception:
            db.session.rollback()
            return (
                jsonify({"success": False, "error": "Hệ thống lỗi, vui lòng quay lại sau!"}),
                500,
            )

    return render_template("index.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    # TODO
    pass


@app.route("/login-admin", methods=["POST"])
def login_admin_process():
    username = request.form.get("username")
    password = request.form.get("password")

    user = dao.auth_user(username, password)

    if user:
        login_user(user)
        return redirect("/admin")
    else:
        return redirect("/admin")


@app.route("/login", methods=["GET", "POST"])
@anonymous_required
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not all([username, password]):
            return jsonify({"success": False, "error": "Vui lòng nhập đầy đủ tài khoản và mật khẩu!"}), 400

        user = dao.auth_user(username=username, password=password)

        if not user:
            return (
                jsonify({"success": False, "error": "Tài khoản hoặc mật khẩu không đúng!"}),
                401,
            )

        login_user(user)

        redirect_url = session.pop("next_url", "/")

        return jsonify({"success": True, "redirect": redirect_url}), 200

    return render_template("index.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route("/login/google")
def google_login():
    redirect_uri = url_for("google_authorize", _external=True)
    print(repr(redirect_uri))
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/authorize/google")
def google_authorize():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo")

    if not userinfo or not userinfo.get("email_verified"):
        return redirect(url_for("login"))

    user = User.query.filter_by(google_sub=userinfo["sub"]).first()

    if not user:
        user = User.query.filter_by(email=userinfo["email"]).first()
        if user:
            user.google_sub = userinfo["sub"]
        else:
            user = User(
                email=userinfo["email"],
                first_name=userinfo.get("given_name"),
                last_name=userinfo.get("family_name"),
                google_sub=userinfo["sub"],
            )
            db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect("/")


@app.route("/terms")
def terms():
    pass


@app.route("/privacy")
def privacy():
    pass


@app.route("/register-teacher", methods=["GET", "POST"])
@login_required
def register_teacher():
    if current_user.teacher_profile:
        return redirect(url_for("profile"))

    if request.method == "POST":
        ok, message = dao.can_apply_teacher(current_user.id)
        if not ok:
            return render_template("teacher/register-teacher.html", error=message)

        file_fields = {
            "id_card_file": True,
            "degree_file": True,
            "cv_file": True,
            "extra_cert_file": False,
            "video_file": False,
        }
        uploaded = {}
        for field, required in file_fields.items():
            f = request.files.get(field)
            if f and f.filename:
                try:
                    res = cloudinary.uploader.upload(
                        f,
                        resource_type="auto",
                        folder="elearning-platform/teacher-registrations",
                        public_id=f"{field}_{uuid.uuid4().hex[:8]}",
                    )

                    uploaded[field] = res["secure_url"]
                except Exception:
                    return render_template(
                        "teacher/register-teacher.html", error="Tải file thất bại, vui lòng thử lại!"
                    )
            elif required:
                return render_template("teacher/register-teacher.html", error="Vui lòng tải đầy đủ tài liệu bắt buộc!")

        application, error = dao.create_teacher_application(
            user_id=current_user.id,
            workplace=request.form.get("workplace"),
            degree=request.form.get("degree"),
            major=request.form.get("major"),
            bio=request.form.get("bio"),
            expertise=",".join(request.form.getlist("expertise")),
            experience=request.form.get("experience"),
            teach_style=request.form.get("teach_style"),
            linkedin=request.form.get("linkedin"),
            website=request.form.get("website"),
            **uploaded,
        )

        if error:
            return render_template("teacher/register-teacher.html", error=error)

        return redirect(url_for("profile"))

    latest_application = dao.get_latest_teacher_application(current_user.id)
    return render_template("teacher/register-teacher.html", latest_application=latest_application)


@app.route("/profile")
@login_required
def profile():
    enrollments = dao.get_my_enrollments(current_user.id)
    for e in enrollments:
        dao.recalc_enrollment_progress(e)
    return render_template("profile/profile.html", enrollments=enrollments)


@app.route("/profile/change-info", methods=["GET", "POST"])
@login_required
def change_info():
    error = None
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        avatar = request.files.get("avatar")
        file_path = None

        if avatar:
            try:
                res = cloudinary.uploader.upload(avatar, folder="elearning-platform/avatars")
                file_path = res["secure_url"]
            except Exception:
                error = "Tải file thất bại!"
                return render_template("profile/change-info.html", error=error)

        dao.change_info(email, phone, file_path, first_name, last_name)

        return redirect("/profile")

    return render_template("profile/change-info.html", error=error)


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        curr_password = request.form.get("curr_password")
        user = dao.auth_user(username=current_user.username, password=curr_password)
        if not user:
            error = "Sai mật khẩu!"
            return render_template("profile/change-password.html", error=error)

        new_password = request.form.get("new_password")
        new_confirm = request.form.get("new_confirm")
        if new_password != new_confirm:
            error = "Mật khẩu không khớp!"
            return render_template("profile/change-password.html", error=error)

        dao.change_password(new_password)
        return redirect("/")

    return render_template("profile/change-password.html", error=error)


@app.route("/courses")
def courses():
    courses = Course.query.filter_by(activate=True).order_by(Course.id.desc()).all()
    return render_template("course/courses.html", courses=courses)


@app.route("/courses/manage")
@login_required
@teacher_required
def my_courses():
    courses = dao.get_courses_by_teacher_id(current_user.teacher_profile.id)
    request.args.get("error")
    return render_template("course/manage.html", courses=courses)


@app.route("/courses/<int:course_id>")
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)

    is_enrolled = False
    if current_user.is_authenticated:
        is_enrolled = dao.is_enrolled(current_user.id, course_id)

    chapters = dao.get_chapters(course_id)
    outcomes = dao.get_outcomes(course_id)

    return render_template(
        "course/course_detail.html",
        course=course,
        chapters=chapters,
        outcomes=outcomes,
        is_enrolled=is_enrolled,
    )


@app.route("/courses/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll_course(course_id):
    enrollment, error = dao.enroll_course(user_id=current_user.id, course_id=course_id)

    if error:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True, "redirect": url_for("learn_course", course_id=course_id)})


# learning
@app.route("/my-learning")
@login_required
def my_learning():
    enrollments = dao.get_my_enrollments(current_user.id)
    return render_template("profile/my-learning.html", enrollments=enrollments)


@app.route("/learn/<int:course_id>")
@login_required
def learn_course(course_id):
    if not dao.is_enrolled(current_user.id, course_id):
        return redirect(url_for("course_detail", course_id=course_id))

    course = dao.get_course_details(course_id)
    chapters = dao.get_chapters(course_id)

    lesson_id = request.args.get("lesson_id", type=int)
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
        dao.mark_lesson_completed(current_user.id, course_id, current_lesson.id)

    enrollment = dao.get_latest_enrollment(current_user.id, course_id)
    if enrollment:
        dao.recalc_enrollment_progress(enrollment)
    progress_map = dao.get_lesson_progress_map(current_user.id, course_id)

    return render_template(
        "course/learn.html",
        course=course,
        chapters=chapters,
        current_lesson=current_lesson,
        doc_kind=doc_kind,
        enrollment=enrollment,
        progress_map=progress_map,
    )


@app.route("/learn/<int:course_id>/lessons/<int:lesson_id>/complete", methods=["POST"])
@login_required
def complete_lesson(course_id, lesson_id):
    ok, error = dao.mark_lesson_completed(current_user.id, course_id, lesson_id)
    return jsonify({"success": ok, "error": error})

@app.route("/courses/<int:course_id>/tests/<int:test_id>")
@login_required
def take_test(course_id, test_id):
    test = dao.get_test_details(test_id)
    if not test or test.course_id != course_id:
        return redirect(url_for("course_detail", course_id=course_id))

    ok, error = dao.can_take_test(current_user.id, test)
    if not ok:
        return render_template(
            "course/test_blocked.html",
            course_id=course_id,
            test=test,
            error=error,
        )

    attempts = dao.get_test_attempts(current_user.id, course_id, test_id)
    attempts_left = (
        test.max_attempts - len(attempts) if test.max_attempts and test.max_attempts > 0 else None
    )

    return render_template(
        "course/test.html",
        course_id=course_id,
        test=test,
        attempts=attempts,
        attempts_left=attempts_left,
    )


@app.route("/courses/<int:course_id>/tests/<int:test_id>/submit", methods=["POST"])
@login_required
def submit_test(course_id, test_id):
    # Đáp án gửi lên dạng: answer_<question_id> = <answer_id>
    answers = {}
    for key, value in request.form.items():
        if key.startswith("answer_"):
            question_id = key.replace("answer_", "")
            answers[question_id] = value

    score, error = dao.submit_test_score(current_user.id, course_id, test_id, answers)

    if error:
        return render_template(
            "course/test_blocked.html",
            course_id=course_id,
            test=dao.get_test_details(test_id),
            error=error,
        )

    return render_template(
        "course/test_result.html",
        course_id=course_id,
        test=dao.get_test_details(test_id),
        score=score,
    )

def get_doc_kind(ext):
    ext = ext.lower()
    if ext == "pdf":
        return "pdf"
    if ext in ("doc", "docx", "ppt", "pptx", "xls", "xlsx"):
        return "office"
    if ext in ("png", "jpg", "jpeg", "gif", "webp"):
        return "image"
    return "other"


@app.route("/courses/create", methods=["GET", "POST"])
@login_required
@teacher_required
def create_course():
    if request.method == "POST":
        image = request.files.get("image")
        image_url = None
        if image and image.filename:
            res = cloudinary.uploader.upload(image, folder="elearning-platform/courses")
            image_url = res["secure_url"]

        course = dao.create_course(
            name=request.form["name"],
            description=request.form["description"],
            image=image_url,
            teacher_id=current_user.teacher_profile.id,
            level=request.form.get("level"),
            category_ids=request.form.getlist("category_ids"),
        )

        if course:
            outcomes = request.form.getlist("outcomes")
            for content in outcomes:
                if content.strip():
                    dao.create_outcome(course_id=course.id, content=content.strip())
            return redirect(url_for("courses"))

    categories = dao.get_categories()
    return render_template("course/course_form.html", categories=categories, course=None)


@app.route("/courses/<int:course_id>/update", methods=["GET", "POST"])
@login_required
@teacher_required
def update_course(course_id):
    course = dao.get_course_details(course_id, teacher_id=current_user.teacher_profile.id)
    if not course:
        return redirect(url_for("my_courses"))

    if request.method == "POST":
        tests_data_raw = request.form.get("tests_data")
        if tests_data_raw:
            try:
                tests_data = json.loads(tests_data_raw)
            except (ValueError, TypeError):
                tests_data = []
            dao.sync_tests(
                course_id=course_id,
                teacher_id=current_user.teacher_profile.id,
                tests_data=tests_data,
            )
        image = request.files.get("image")
        image_url = None
        if image and image.filename:
            res = cloudinary.uploader.upload(image, folder="elearning-platform/courses")
            image_url = res["secure_url"]

        # Đọc giá từ form: nếu tick "Miễn phí", ô price bị disable nên sẽ không có trong form -> None
        price_raw = request.form.get("price")
        price = None
        if price_raw not in (None, ""):
            try:
                price = max(0, int(price_raw))
            except ValueError:
                price = None
        elif not course.activate:
            # Chưa activate và không nhập gì (tick Miễn phí) -> set về 0
            price = 0

        was_draft = not course.activate
        action = request.form.get("action", "save")

        dao.update_course(
            course_id=course_id,
            teacher_id=current_user.teacher_profile.id,
            name=request.form.get("name"),
            description=request.form.get("description"),
            image=image_url,
            level=request.form.get("level"),
            category_ids=request.form.getlist("category_ids"),
            price=price,
        )

        outcomes = request.form.getlist("outcomes")
        dao.replace_outcomes(course_id, outcomes)

        chapters_data_raw = request.form.get("chapters_data")
        if chapters_data_raw:
            try:
                chapters_data = json.loads(chapters_data_raw)
            except (ValueError, TypeError):
                chapters_data = []
            if chapters_data:
                dao.sync_chapters_and_lessons(
                    course_id=course_id,
                    teacher_id=current_user.teacher_profile.id,
                    chapters_data=chapters_data,
                    files=request.files,
                )

        # Chỉ công khai khi bấm đúng nút "Công khai khóa học" (tab Cài đặt)
        if was_draft and action == "publish":
            dao.activate_course(course_id, teacher_id=current_user.teacher_profile.id)

        return redirect(url_for("my_courses"))

    categories = dao.get_categories()
    chapters = dao.get_chapters(course_id)
    outcomes = dao.get_outcomes(course_id)

    return render_template(
        "course/course_form.html", categories=categories, course=course, chapters=chapters, outcomes=outcomes
    )


@app.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_course(course_id):
    success, error = dao.delete_course(course_id, teacher_id=current_user.teacher_profile.id)

    if not success:
        return redirect(url_for("my_courses", error=error))

    return redirect(url_for("my_courses"))


@app.route("/courses/<int:course_id>/activate", methods=["POST"])
@login_required
@teacher_required
def activate_course(course_id):
    course, error = dao.activate_course(course_id, teacher_id=current_user.teacher_profile.id)

    if error:
        return redirect(url_for("my_courses", error=error))

    return redirect(url_for("my_courses"))





@app.route("/chapters/<int:chapter_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_chapter(chapter_id):
    course_id = request.form.get("course_id")
    dao.delete_chapter(chapter_id, teacher_id=current_user.teacher_profile.id)
    return jsonify({"success": True})


@app.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    course_id = request.form.get("course_id")
    dao.delete_lesson(lesson_id, teacher_id=current_user.teacher_profile.id)
    return jsonify({"success": True})


@app.route("/courses/<int:course_id>/tests/<int:test_id>/questions", methods=["GET", "POST"])
@login_required
@teacher_required
def manage_test_questions(course_id, test_id):
    test = dao.get_test_for_teacher(test_id, current_user.teacher_profile.id)
    if not test or test.course_id != course_id:
        return redirect(url_for("update_course", course_id=course_id))

    if request.method == "POST":
        questions_data_raw = request.form.get("questions_data")
        if questions_data_raw:
            try:
                questions_data = json.loads(questions_data_raw)
            except (ValueError, TypeError):
                questions_data = []
            dao.sync_questions(
                test_id=test_id,
                teacher_id=current_user.teacher_profile.id,
                questions_data=questions_data,
            )
        return redirect(url_for("update_course", course_id=course_id, test_id=test_id))

    questions = dao.get_questions(test_id)
    return render_template(
        "course/test_questions.html", course_id=course_id, test=test, questions=questions
    )
# forum


@app.route("/forum")
def forum():
    keyword = request.args.get("kw")
    solved = request.args.get("solved")
    category = request.args.get("category", type=int)
    if solved == "true":
        solved = True
    elif solved == "false":
        solved = False
    else:
        solved = None

    posts = dao.get_posts(keyword=keyword, solved=solved, category_id=category)

    return render_template("forum/index.html", posts=posts)


@app.route("/forum/<int:post_id>")
@login_required
def forum_detail(post_id):
    post = Post.query.get_or_404(post_id)

    post.view_count += 1
    db.session.commit()
    related_posts = dao.get_related_posts(post.id)
    user_vote = dao.get_user_post_vote(post.id, current_user.id)
    return render_template("forum/detail.html", post=post, related_posts=related_posts, user_vote=user_vote)


@app.route("/forum/create", methods=["GET", "POST"])
@login_required
def create_question():
    if request.method == "POST":
        image = request.files.get("image")

        image_url = None

        if image and image.filename:
            res = cloudinary.uploader.upload(image, folder="elearning-platform/forum")
            image_url = res["secure_url"]

        dao.create_post(
            title=request.form["title"],
            content=request.form["content"],
            category_ids=request.form.getlist("category_ids"),
            user_id=current_user.id,
            image=image_url,
        )

        return redirect(url_for("forum"))

    categories = PostCate.query.all()

    return render_template("forum/create.html", categories=categories)


@app.route("/forum/<int:post_id>/answer", methods=["POST"])
@login_required
def answer(post_id):
    dao.add_comment(post_id=post_id, user_id=current_user.id, content=request.form["content"])

    return redirect(url_for("forum_detail", post_id=post_id))


@app.route("/forum/<int:post_id>/upvote", methods=["POST"])
@login_required
def upvote_post(post_id):
    dao.vote_post(post_id, current_user.id, VoteType.UP)
    return redirect(url_for("forum_detail", post_id=post_id))


@app.route("/forum/<int:post_id>/downvote", methods=["POST"])
@login_required
def downvote_post(post_id):
    dao.vote_post(post_id, current_user.id, VoteType.DOWN)

    return redirect(url_for("forum_detail", post_id=post_id))


@app.route("/comment/<int:comment_id>/accept", methods=["POST"])
@login_required
def accept_answer(comment_id):
    dao.accept_answer(comment_id)

    return redirect(request.referrer)


@app.route("/comment/<int:comment_id>/upvote", methods=["POST"])
@login_required
def upvote_comment(comment_id):
    dao.vote_comment(comment_id, current_user.id, VoteType.UP)

    return redirect(request.referrer)


@app.route("/comment/<int:comment_id>/downvote", methods=["POST"])
@login_required
def downvote_comment(comment_id):
    dao.vote_comment(comment_id, current_user.id, VoteType.DOWN)

    return redirect(request.referrer)


@app.route("/comment/<int:comment_id>/reply", methods=["POST"])
@login_required
def reply_comment(comment_id):
    parent_comment = Comment.query.get_or_404(comment_id)

    dao.add_comment(
        post_id=parent_comment.post_id,
        user_id=current_user.id,
        content=request.form["content"],
        parent_comment_id=comment_id,
    )

    return redirect(url_for("forum_detail", post_id=parent_comment.post_id))


@app.route("/courses/<int:course_id>/checkout", methods=["GET", "POST"])
@login_required
def checkout_course(course_id):
    pay_url, error = dao.create_payment(user_id=current_user.id, course_id=course_id)
    if error:
        return jsonify({"success": False, "error": error}), 400
    return redirect(pay_url)


@app.route("/payment/momo/ipn", methods=["POST"])
def momo_ipn():
    data = request.get_json(silent=True) or {}

    if not momo.verify_ipn_signature(data):
        return jsonify({"message": "Invalid signature"}), 400

    order_id = data.get("orderId")
    result_code = data.get("resultCode")

    if result_code == 0:
        dao.confirm_payment_success(
            order_id=order_id,
            momo_trans_id=data.get("transId"),
            pay_type=data.get("payType"),
        )
    else:
        dao.confirm_payment_failed(order_id)

    return jsonify({"message": "OK"}), 204


@app.route("/payment/momo/return")
def momo_return():
    order_id = request.args.get("orderId")
    result_code = request.args.get("resultCode", type=int)
    payment = dao.get_payment_by_order_id(order_id) if order_id else None

    return render_template(
        "payment/result.html",
        success=(result_code == 0),
        payment=payment,
    )


@app.route("/payment/history")
@login_required
def payment_history():
    payments = dao.get_my_payments(current_user.id)
    return render_template("profile/payment-history.html", payments=payments)


if __name__ == "__main__":
    app.run(debug=True)
