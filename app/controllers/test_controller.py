from datetime import datetime

from flask import redirect, render_template, request, session, url_for
from flask_login import current_user

from app import app, dao
from app.decorators import login_required, teacher_required
from app.services import test_service


@app.route("/courses/<int:course_id>/tests/<int:test_id>")
@login_required
def take_test(course_id, test_id):
    ctx, error = test_service.get_test_context(course_id, test_id, current_user.id)
    if error:
        return redirect(url_for("learn_course", course_id=course_id))

    return render_template(
        "course/test_info.html",
        course_id=course_id,
        test=ctx["test"],
        can_take=ctx["can_take"],
        block_reason=ctx["block_reason"],
        attempts=ctx["attempts"],
        attempts_count=ctx["attempts_count"],
        attempts_left=ctx["attempts_left"],
        best_score=ctx["best_score"],
    )


@app.route("/courses/<int:course_id>/tests/<int:test_id>/start", methods=["POST"])
@login_required
def start_test(course_id, test_id):
    test = dao.get_test_details(test_id)
    if not test:
        return redirect(url_for("learn_course", course_id=course_id))

    can_take, block_reason = dao.can_take_test(current_user.id, test)
    if not can_take:
        return render_template("course/test_blocked.html", course_id=course_id, test=test, reason=block_reason)

    session[f"test_start_{test_id}"] = datetime.now().isoformat()
    return redirect(url_for("do_test", course_id=course_id, test_id=test_id))


@app.route("/courses/<int:course_id>/tests/<int:test_id>/submit", methods=["POST"])
@login_required
def submit_test(course_id, test_id):
    test = dao.get_test_details(test_id)
    if not test:
        return redirect(url_for("learn_course", course_id=course_id))

    session_key = f"test_start_{test_id}"
    session.pop(session_key, None)

    answers = {k: v for k, v in request.form.items() if k != "csrf_token"}
    score, error = test_service.submit_test(current_user.id, course_id, test_id, answers)
    if error:
        return render_template("course/test_blocked.html", course_id=course_id, test=test, reason=error)

    return redirect(url_for("test_result", course_id=course_id, test_id=test_id, score_id=score.id))


@app.route("/courses/<int:course_id>/tests/<int:test_id>/result")
@login_required
def test_result(course_id, test_id):
    test = dao.get_test_details(test_id)
    if not test:
        return redirect(url_for("learn_course", course_id=course_id))

    ctx, _ = test_service.get_test_context(course_id, test_id, current_user.id)
    score_id = request.args.get("score_id", type=int)
    current_score = None
    if score_id:
        current_score = next((a for a in ctx["attempts"] if a.id == score_id), None)
    if not current_score and ctx["attempts"]:
        current_score = ctx["attempts"][-1]

    return render_template(
        "course/test_result.html",
        course_id=course_id,
        test=test,
        score=current_score,
        attempts=ctx["attempts"],
        attempts_left=ctx["attempts_left"],
        best_score=ctx["best_score"],
    )


@app.route("/courses/<int:course_id>/tests/<int:test_id>/do")
@login_required
def do_test(course_id, test_id):
    ctx, error = test_service.get_test_context(course_id, test_id, current_user.id)
    if error:
        return redirect(url_for("learn_course", course_id=course_id))

    test = ctx["test"]
    if not ctx["can_take"]:
        return render_template("course/test_blocked.html", course_id=course_id, test=test, reason=ctx["block_reason"])

    session_key = f"test_start_{test_id}"
    remaining_seconds, time_expired = test_service.calculate_remaining_time(test, session_key, session)
    questions = dao.get_questions(test_id)

    return render_template(
        "course/test.html",
        course_id=course_id,
        test=test,
        questions=questions,
        remaining_seconds=remaining_seconds,
        time_expired=time_expired,
        attempts=ctx["attempts"],
        attempts_left=ctx["attempts_left"],
        best_score=ctx["best_score"],
    )


@app.route("/courses/<int:course_id>/tests/<int:test_id>/questions", methods=["GET", "POST"])
@login_required
@teacher_required
def manage_questions(course_id, test_id):
    course = test_service.get_course_by_teacher(course_id, current_user.teacher_profile.id)
    if not course:
        return redirect(url_for("my_courses"))

    test = test_service.get_test_for_teacher(test_id, current_user.teacher_profile.id)
    if not test:
        return redirect(url_for("update_course", course_id=course_id))

    if request.method == "POST":
        test_service.sync_questions(test_id, current_user.teacher_profile.id, request.form)
        return redirect(url_for("update_course", course_id=course_id))

    questions = dao.get_questions(test_id)
    return render_template("course/test_questions.html", course_id=course_id, test=test, questions=questions)
