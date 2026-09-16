from flask import redirect, render_template, request, url_for
from flask_login import current_user

from app import app, dao
from app.decorators import login_required
from app.services import auth_service, teacher_service


@app.route("/register-teacher", methods=["GET", "POST"])
@login_required
def register_teacher():
    if current_user.teacher_profile:
        return redirect(url_for("profile"))

    if request.method == "POST":
        application, error = teacher_service.submit_teacher_application(
            user_id=current_user.id,
            form_data=request.form,
            files=request.files,
        )
        if error:
            return render_template("teacher/register-teacher.html", error=error)
        return redirect(url_for("profile"))

    latest_application = teacher_service.get_latest_application(current_user.id)
    return render_template("teacher/register-teacher.html", latest_application=latest_application)


@app.route("/profile")
@login_required
def profile():
    enrollments = dao.get_my_enrollments(current_user.id)
    return render_template("profile/profile.html", enrollments=enrollments)


@app.route("/profile/change-info", methods=["GET", "POST"])
@login_required
def change_info():
    error = None
    if request.method == "POST":
        ok, err = auth_service.update_profile(request.form, request.files)
        if not ok:
            return render_template("profile/change-info.html", error=err)
        return redirect(url_for("profile"))

    return render_template("profile/change-info.html", error=error)


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    error = None
    if request.method == "POST":
        curr_password = request.form.get("curr_password")
        new_password = request.form.get("new_password")
        new_confirm = request.form.get("new_confirm")
        ok, err = auth_service.change_password(current_user, curr_password, new_password, new_confirm)
        if not ok:
            return render_template("profile/change-password.html", error=err)
        return redirect(url_for("profile"))

    return render_template("profile/change-password.html", error=error)
