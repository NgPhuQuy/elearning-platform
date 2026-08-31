from flask import jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from app import app, oauth
from app.decorators import anonymous_required, login_required
from app.services import auth_service


@app.route("/register", methods=["GET", "POST"])
@anonymous_required
def register():
    if request.method == "POST":
        user, error = auth_service.register_user(request.form, request.files)
        if error:
            return jsonify({"success": False, "error": error}), 400
        login_user(user)
        return jsonify({"success": True, "redirect": "/"})
    return render_template("index.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    return render_template("index.html")


@app.route("/login-admin", methods=["GET", "POST"])
def login_admin_process():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user, error = auth_service.auth_admin(username, password)
        if error:
            status_code = 403 if "quyền" in error else (400 if "đầy đủ" in error else 401)
            return jsonify({"success": False, "error": error}), status_code

        login_user(user)
        return jsonify({"success": True, "redirect": "/admin"})

    if current_user.is_authenticated and getattr(current_user, "admin", None):
        return redirect("/admin")
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
@anonymous_required
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user, error = auth_service.auth_user(username, password)
        if error:
            status_code = 403 if "khóa" in error else (400 if "đầy đủ" in error else 401)
            return jsonify({"success": False, "error": error}), status_code

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
    return oauth.google.authorize_redirect(redirect_uri)


@app.route("/authorize/google")
def google_authorize():
    token = oauth.google.authorize_access_token()
    userinfo = token.get("userinfo") if token else None
    user, error = auth_service.handle_google_login(userinfo)
    if error or not user:
        return redirect(url_for("login"))

    login_user(user)
    return redirect("/")


@app.route("/terms")
def terms():
    return render_template("index.html")


@app.route("/privacy")
def privacy():
    return render_template("index.html")
