from flask import jsonify, render_template
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import app, dao, db


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

