import cloudinary.uploader
from flask import jsonify, redirect, render_template, request, url_for,session
from flask_login import current_user, login_user, logout_user

from app import admin, app, dao, db, oauth  # noqa: F401  # Register admin routes.
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
            return jsonify({"success": False, "error": "Mật khẩu phải từ 8 ký tự trở lên!"}), 400

        if dao.is_username_exist(username=username):
            return jsonify({"success": False, "error": "Username đã tồn tại!"}), 400

        if dao.is_email_used(email=email):
            return jsonify({"success": False, "error": "Email đã được sử dụng!"}), 400

        if dao.is_phone_used(phone=phone):
            return jsonify({"success": False, "error": "Số điện thoại này đã được đăng ký!"}), 400

        avatar = request.files.get("avatar")
        file_path = None
        if avatar:
            try:
                res = cloudinary.uploader.upload(avatar)
                file_path = res["secure_url"]
            except Exception:
                return jsonify({"success": False, "error": "Tải file thất bại!"}), 500

        try:
            user = register_user(username, password, email, phone, file_path, first_name, last_name)
            login_user(user)
            return jsonify({"success": True, "redirect": "/"})
        except Exception:
            db.session.rollback()
            return jsonify({"success": False, "error": "Hệ thống lỗi, vui lòng quay lại sau!"}), 500

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
            return jsonify({"success": False, "error": "Tài khoản hoặc mật khẩu không đúng!"}), 401

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
                    res = cloudinary.uploader.upload(f, resource_type="auto")
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
    return render_template("profile/profile.html")


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
                res = cloudinary.uploader.upload(avatar)
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
    courses = Course.query.order_by(Course.id.desc()).all()
    return render_template("course/manage.html", courses=courses)


@app.route("/courses/manage")
@login_required
@teacher_required
def my_courses():
    courses = dao.get_courses_by_teacher_id(current_user.teacher_profile.id)
    return render_template("course/manage.html", courses=courses)


@app.route("/courses/create", methods=["GET", "POST"])
@login_required
@teacher_required
def create_course():
    if request.method == "POST":
        image = request.files.get("image")
        image_url = None
        if image and image.filename:
            res = cloudinary.uploader.upload(image)
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
        image = request.files.get("image")
        image_url = None
        if image and image.filename:
            res = cloudinary.uploader.upload(image)
            image_url = res["secure_url"]

        dao.update_course(
            course_id=course_id,
            teacher_id=current_user.teacher_profile.id,
            name=request.form.get("name"),
            description=request.form.get("description"),
            image=image_url,
            level=request.form.get("level"),
            category_ids=request.form.getlist("category_ids"),
        )

        outcomes = request.form.getlist("outcomes")
        dao.replace_outcomes(course_id, outcomes)

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
    dao.delete_course(course_id, teacher_id=current_user.teacher_profile.id)
    return redirect(url_for("my_courses"))


@app.route("/courses/<int:course_id>/content", methods=["GET", "POST"])
@login_required
@teacher_required
def manage_content(course_id):
    course = dao.get_course_details(course_id, teacher_id=current_user.teacher_profile.id)
    if not course:
        return redirect(url_for("my_courses"))

    action = request.form.get("action")

    if action == "add_chapter":
        dao.create_chapter(
            course_id=course_id,
            teacher_id=current_user.teacher_profile.id,
            name=request.form.get("chapter_name"),
            description=request.form.get("chapter_description", ""),
        )
    elif action == "add_lesson":
        dao.create_lesson(
            teacher_id=current_user.teacher_profile.id,
            chapter_id=request.form.get("chapter_id"),
            name=request.form.get("lesson_name"),
            description=request.form.get("lesson_description", ""),
            lesson_type=request.form.get("lesson_type"),
        )

    return redirect(url_for("update_course", course_id=course_id) + "#cc-content")


@app.route("/chapters/<int:chapter_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_chapter(chapter_id):
    course_id = request.form.get("course_id")
    dao.delete_chapter(chapter_id, teacher_id=current_user.teacher_profile.id)
    return redirect(url_for("manage_content", course_id=course_id))


@app.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    course_id = request.form.get("course_id")
    dao.delete_lesson(lesson_id, teacher_id=current_user.teacher_profile.id)
    return redirect(url_for("manage_content", course_id=course_id))


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
            res = cloudinary.uploader.upload(image)
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


if __name__ == "__main__":
    app.run(debug=True)
