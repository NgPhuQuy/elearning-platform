from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app import app
from app.decorators import login_required
from app.services import learning_service


@app.route("/courses/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll_course(course_id):
    enrollment, error = learning_service.enroll_course(user_id=current_user.id, course_id=course_id)
    if error:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "redirect": url_for("learn_course", course_id=course_id)})


@app.route("/my-learning")
@login_required
def my_learning():
    enrollments = learning_service.get_my_learning(current_user.id)
    return render_template("profile/my-learning.html", enrollments=enrollments)


@app.route("/learn/<int:course_id>")
@login_required
def learn_course(course_id):
    lesson_id = request.args.get("lesson_id", type=int)
    ctx = learning_service.get_learn_context(course_id, current_user.id, lesson_id=lesson_id)
    if not ctx:
        return redirect(url_for("course_detail", course_id=course_id))

    return render_template(
        "course/learn.html",
        course_id=course_id,
        course=ctx["course"],
        chapters=ctx["chapters"],
        current_lesson=ctx["current_lesson"],
        doc_kind=ctx["doc_kind"],
        enrollment=ctx["enrollment"],
        progress_map=ctx["progress_map"],
        tests=ctx["tests"],
    )


@app.route("/lessons/<int:lesson_id>/complete", methods=["POST"])
@login_required
def complete_lesson(lesson_id):
    course_id = request.form.get("course_id", type=int)
    if not course_id:
        return jsonify({"success": False, "error": "Thiếu course_id"}), 400

    ok, error = learning_service.mark_lesson_completed(current_user.id, course_id, lesson_id)
    if not ok:
        return jsonify({"success": False, "error": error}), 400

    return jsonify({"success": True})

