import cloudinary.uploader
from flask import redirect, render_template, request
from flask_login import login_user, current_user, logout_user
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
            return render_template("register.html", error=error)

        username = request.form.get('username')
        if dao.is_username_exist(username=username):
            error = "Username đã tồn tại!"
            return render_template("register.html", error=error)

        email = request.form.get("email")
        if dao.is_email_used(email=email):
            error = "Email đã được sử dụng!"
            return render_template("register.html", error=error)

        phone = request.form.get("phone")
        if dao.is_phone_used(phone=phone):
            error = "Số điện thoại này đã được đăng ký!"
            return render_template("register.html", error=error)

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
                return render_template("register.html", error=error)
        try:
            user = register_user(username, password, email, phone, file_path, first_name, last_name)
            login_user(user)
            return redirect("/")

        except Exception:
            error = "Hệ thống lỗi, vui lòng quay lại sau!"
            db.session.rollback()
            return render_template("register.html", error=error)

    return render_template("register.html", error=error)

@app.route('/login', methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')

        user = dao.auth_user(username=username, password=password)

        if user:
            login_user(user)
            return redirect("/")
        else:
            error = "Tài khoản hoặc mật khẩu không đúng!"
    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")

if __name__ == '__main__':
    app.run(debug=True)