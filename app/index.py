import cloudinary.uploader
from flask import redirect, render_template, request
from flask_login import login_user, current_user, logout_user, login_required
from app import app, dao, login, db
from datetime import datetime
from app.dao import register_user


@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            error = "Mật khẩu không khớp!"
            return render_template("auth/register.html", error=error)

        username = request.form.get('username')
        if dao.is_username_exist(username=username):
            error = "Username đã tồn tại!"
            return render_template("auth/register.html", error=error)

        email = request.form.get("email")
        if dao.is_email_used(email=email):
            error = "Email đã được sử dụng!"
            return render_template("auth/register.html", error=error)

        phone = request.form.get("phone")
        if dao.is_phone_used(phone=phone):
            error = "Số điện thoại này đã được đăng ký!"
            return render_template("auth/register.html", error=error)

        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        avatar = request.files.get("avatar")

        file_path = None
        if avatar:
            try:
                res = cloudinary.uploader.upload(avatar)
                file_path = res["secure_url"]
            except Exception:
                error = "Tải file thất bại!"
                return render_template("auth/register.html", error=error)
        try:
            user = register_user(username, password, email, phone, file_path, first_name, last_name)
            login_user(user)
            return redirect("/")

        except Exception:
            error = "Hệ thống lỗi, vui lòng quay lại sau!"
            db.session.rollback()
            return render_template("auth/register.html", error=error)

    return render_template("auth/register.html", error=error)

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)

        if user:
            login_user(user)
            if user.teach:
                return redirect("/courses")
            return redirect("/")
        else:
            error = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("auth/login.html", error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

@app.route('/profile')
def profile():
    return render_template("profile/profile.html")


@app.route('/profile/change-info', methods=['GET', 'POST'])
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


@app.route('/profile/change-password', methods=['GET', 'POST'])
def change_password():
    error = None
    if request.method == "POST":
        curr_password = request.form.get('curr_password')
        user = dao.auth_user(username=current_user.username, password=curr_password)
        if not user:
            error = "Sai mật khẩu!"
            return render_template("profile/change-password.html", error=error)

        new_password = request.form.get('new_password')
        new_confirm = request.form.get('new_confirm')
        if new_password != new_confirm:
            error = "Mật khẩu không khớp!"
            return render_template("profile/change-password.html", error=error)

        dao.change_password(new_password)
        return redirect("/")

    return render_template("profile/change-password.html", error=error)



@app.route('/create-course', methods=['GET', 'POST'])
@login_required
def create_course():
    error = None

    if current_user.teach:
        teacher = current_user.teach[0]
    else:
        teacher = None

    if not teacher:
        return redirect('/')


    categories = dao.get_categories()

    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')
        image = request.files.get('image')
        category_ids = request.form.getlist('category_ids')

        if not name or not description or not image:
            error = "Vui lòng nhập đầy đủ tên và mô tả khóa học và cả hình ảnh khóa học!"
            return render_template(
                "course/create_course.html",
                error=error,
                categories=categories
            )

        file_path = None
        try:
            res = cloudinary.uploader.upload(image)
            file_path = res["secure_url"]
        except Exception:
            error = "Tải ảnh thất bại!"
            return render_template(
                "course/create_course.html",
                error=error,
                categories=categories
            )

        try:
            course = dao.create_course(
                name=name,
                description=description,
                image=file_path,
                teacher_id=teacher.id,
                category_ids=category_ids
            )

            if not course:
                error = "Hệ thống lỗi, vui lòng thử lại!"
                return render_template(
                    "course/create_course.html",
                    error=error,
                    categories=categories
                )

            return redirect('/courses')

        except Exception:
            db.session.rollback()
            error = "Hệ thống lỗi, vui lòng thử lại!"
            return render_template(
                "course/create_course.html",
                error=error,
                categories=categories
            )

    return render_template(
        "course/create_course.html",
        error=error,
        categories=categories
    )

@app.route("/courses/<int:course_id>")
@login_required
def course_detail(course_id):
    if not current_user.teach:
        return redirect("/")

    teacher = current_user.teach[0]

    course = dao.get_course_details(course_id, teacher.id)

    if not course:
        return redirect("/courses")

    return render_template(
        "course/detail.html",
        course=course
    )
@app.route("/courses")
@login_required
def course_index():
    if not current_user.teach:
        return redirect("/")

    teacher = current_user.teach[0]

    courses = dao.get_courses_by_teacher_id(teacher.id)

    return render_template(
        "course/index.html",
        courses=courses
    )
@app.route("/update_course/<int:course_id>", methods=["GET", "POST"])
@login_required
def update_course(course_id):

    if not current_user.teach:
        return redirect("/")

    teacher = current_user.teach[0]

    course = dao.get_course_details(course_id, teacher.id)

    if not course:
        return redirect("/courses")


    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')
        image = request.files.get('image')
        category_ids = request.form.getlist('category_ids')
        dao.update_course(
            course_id=course_id,
            teacher_id=teacher.id,
            name=name,
            description=description,
            image=image ,
            category_ids = category_ids
        )

        return redirect(f"/courses/{course_id}")


    return render_template(
        "course/update_course.html",
        course=course,
        categories = dao.get_categories()
    )
@app.route("/delete_course/<int:course_id>", methods=["POST"])
@login_required
def delete_course(course_id):
    if not current_user.teach:
        return redirect("/")
    teacher = current_user.teach[0]
    if dao.delete_course(course_id, teacher.id):
        return redirect("/courses")
    return redirect("/courses")

if __name__ == '__main__':
    app.run(debug=True)