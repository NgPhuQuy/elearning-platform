import json
from datetime import datetime

from app import dao
from app.models import Course


def get_test_context(course_id, test_id, user_id):
    test = dao.get_test_details(test_id)
    if not test:
        return None, "Bài kiểm tra không tồn tại."

    can_take, block_reason = dao.can_take_test(user_id, test)
    attempts = dao.get_test_attempts(user_id, course_id, test_id)
    attempts_count = len(attempts)
    attempts_left = max(0, (test.max_attempts or 1) - attempts_count)
    best_score = max((a.score_value for a in attempts), default=None)

    return {
        "test": test,
        "can_take": can_take,
        "block_reason": block_reason,
        "attempts": attempts,
        "attempts_count": attempts_count,
        "attempts_left": attempts_left,
        "best_score": best_score,
    }, None


def calculate_remaining_time(test, session_key, session_store):
    if not test.duration or test.duration <= 0:
        return 0, False

    start_time_str = session_store.get(session_key)
    if not start_time_str:
        return 0, True

    start_time = datetime.fromisoformat(start_time_str)
    elapsed = (datetime.now() - start_time).total_seconds()
    remaining = int(test.duration * 60 - elapsed)
    if remaining <= 0:
        return 0, True
    return remaining, False


def submit_test(user_id, course_id, test_id, form_answers):
    return dao.submit_test_score(user_id, course_id, test_id, form_answers)


def sync_questions(test_id, teacher_id, form_data):
    questions_raw = form_data.get("questions_data")
    if not questions_raw:
        return False
    try:
        questions_data = json.loads(questions_raw)
    except (ValueError, TypeError):
        return False

    pass_score = float(form_data.get("pass_score", 5))
    return dao.sync_questions(
        test_id=test_id,
        teacher_id=teacher_id,
        questions_data=questions_data,
        pass_score=pass_score,
    )


def get_test_for_teacher(test_id, teacher_id):
    return dao.get_test_for_teacher(test_id, teacher_id)


def get_course_by_teacher(course_id, teacher_id):
    return Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()

