from flask import redirect, render_template, request, url_for
from flask_login import current_user

from app import app, dao
from app.decorators import login_required, teacher_required
from app.services import course_service


@app.route("/courses")
def courses():
    courses_list, categories = course_service.get_all_active_courses()
    return render_template("course/courses.html", courses=courses_list, categories=categories)


@app.route("/courses/manage")
@login_required
@teacher_required
def my_courses():
    courses_list = course_service.get_teacher_courses(current_user.teacher_profile.id)
    error = request.args.get("error")
    return render_template("course/manage.html", courses=courses_list, error=error)


@app.route("/courses/<int:course_id>")
def course_detail(course_id):
    user_id = current_user.id if current_user.is_authenticated else None
    ctx = course_service.get_course_detail(course_id, user_id=user_id)
    return render_template("course/course_detail.html", **ctx)


@app.route("/courses/create", methods=["GET", "POST"])
@login_required
@teacher_required
def create_course():
    if request.method == "POST":
        course, error = course_service.create_course(
            teacher_id=current_user.teacher_profile.id,
            form_data=request.form,
            files=request.files,
        )
        if error:
            categories = dao.get_categories()
            return render_template("course/course_form.html", categories=categories, course=None, error=error)
        return redirect(url_for("update_course", course_id=course.id))

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
        course_service.update_course(
            course_id=course_id,
            teacher_id=current_user.teacher_profile.id,
            form_data=request.form,
            files=request.files,
        )
        return redirect(url_for("my_courses"))

    categories = dao.get_categories()
    return render_template("course/course_form.html", course=course, categories=categories)


@app.route("/courses/<int:course_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_course(course_id):
    ok, error = course_service.delete_course(course_id, current_user.teacher_profile.id)
    if not ok:
        return redirect(url_for("my_courses", error=error))
    return redirect(url_for("my_courses"))


@app.route("/courses/<int:course_id>/activate", methods=["POST"])
@login_required
@teacher_required
def activate_course(course_id):
    course, error = course_service.activate_course(course_id, current_user.teacher_profile.id)
    if error:
        return redirect(url_for("my_courses", error=error))
    return redirect(url_for("my_courses"))


@app.route("/courses/<int:course_id>/chapters", methods=["POST"])
@login_required
@teacher_required
def create_chapter(course_id):
    name = request.form.get("name")
    description = request.form.get("description")
    dao.create_chapter(
        course_id=course_id,
        teacher_id=current_user.teacher_profile.id,
        name=name,
        description=description,
    )
    return redirect(url_for("update_course", course_id=course_id))


@app.route("/chapters/<int:chapter_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_chapter(chapter_id):
    course_id = request.form.get("course_id", type=int)
    dao.delete_chapter(chapter_id, current_user.teacher_profile.id)
    if course_id:
        return redirect(url_for("update_course", course_id=course_id))
    return redirect(url_for("my_courses"))


@app.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@login_required
@teacher_required
def delete_lesson(lesson_id):
    course_id = request.form.get("course_id", type=int)
    dao.delete_lesson(lesson_id, current_user.teacher_profile.id)
    if course_id:
        return redirect(url_for("update_course", course_id=course_id))
    return redirect(url_for("my_courses"))

