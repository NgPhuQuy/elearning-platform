from flask import redirect, render_template, request
from flask_login import login_user, current_user, logout_user
from app import app, dao, login
from datetime import datetime


@app.context_processor
def inject_now():
    return {'current_year': datetime.now().year}

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method.__eq__('POST'):
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