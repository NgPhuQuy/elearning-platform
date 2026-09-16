from datetime import datetime

from app import db
from app.dao.enrollment_dao import get_latest_enrollment, recalc_enrollment_progress
from app.models import Answer, Course, EnrollmentStatus, Question, Score, Test


def get_course_tests(course_id):
    return Test.query.filter_by(course_id=course_id).all()


def get_test_details(test_id):
    return Test.query.get(test_id)


def get_test_for_teacher(test_id, teacher_id):
    return Test.query.join(Course).filter(Test.id == test_id, Course.teacher_id == teacher_id).first()


def get_questions(test_id):
    return Question.query.filter_by(test_id=test_id).all()


def get_test_attempts(user_id, course_id, test_id):
    enrollment = get_latest_enrollment(user_id, course_id)
    if not enrollment:
        return []
    return Score.query.filter_by(enrollment_id=enrollment.id, test_id=test_id).order_by(Score.attempt_number).all()


def can_take_test(user_id, test):
    enrollment = get_latest_enrollment(user_id, test.course_id)
    if not enrollment or enrollment.status == EnrollmentStatus.FAILED:
        return False, "Bạn chưa đăng ký khóa học này."

    if not test.max_attempts or test.max_attempts <= 0:
        return True, None

    used = Score.query.filter_by(enrollment_id=enrollment.id, test_id=test.id).count()
    if used >= test.max_attempts:
        return False, f"Bạn đã hết lượt làm bài (tối đa {test.max_attempts} lần)."

    return True, None


def submit_test_score(user_id, course_id, test_id, answers):
    enrollment = get_latest_enrollment(user_id, course_id)
    if not enrollment or enrollment.status == EnrollmentStatus.FAILED:
        return None, "Bạn chưa đăng ký khóa học này."

    test = Test.query.get(test_id)
    if not test:
        return None, "Bài kiểm tra không tồn tại."

    used = Score.query.filter_by(enrollment_id=enrollment.id, test_id=test.id).count()
    if test.max_attempts and test.max_attempts > 0 and used >= test.max_attempts:
        return None, f"Bạn đã hết lượt làm bài (tối đa {test.max_attempts} lần)."

    attempt_number = used + 1
    questions = test.questions
    total_q = len(questions)

    if total_q == 0:
        score_value = 0.0
    else:
        correct_count = 0
        for q in questions:
            user_ans_id = answers.get(str(q.id))
            if user_ans_id:
                try:
                    ans = Answer.query.get(int(user_ans_id))
                    if ans and ans.question_id == q.id and ans.is_correct:
                        correct_count += 1
                except (ValueError, TypeError):
                    pass
        score_value = round((correct_count / total_q) * 10, 2)

    pass_threshold = float(test.pass_score) if test.pass_score else 5.0
    is_passed = score_value >= pass_threshold

    score = Score(
        enrollment_id=enrollment.id,
        test_id=test.id,
        attempt_number=attempt_number,
        score_value=score_value,
        is_passed=is_passed,
        completed_at=datetime.now(),
    )
    db.session.add(score)

    if test.max_attempts and attempt_number >= test.max_attempts and not is_passed:
        has_passed_any = Score.query.filter_by(enrollment_id=enrollment.id, test_id=test.id, is_passed=True).count() > 0
        if not has_passed_any:
            enrollment.status = EnrollmentStatus.FAILED
            enrollment.completed_date = datetime.now()

    try:
        db.session.commit()
        recalc_enrollment_progress(enrollment)
        return score, None
    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng thử lại sau!"


def sync_tests(course_id, teacher_id, tests_data):
    course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
    if not course:
        return False

    incoming_ids = {t["id"] for t in tests_data if t.get("id")}
    for old_test in course.tests:
        if old_test.id not in incoming_ids:
            db.session.delete(old_test)
    db.session.flush()

    for item in tests_data:
        test_id = item.get("id")
        name = item.get("name", "").strip()
        duration = int(item.get("duration", 0))
        max_attempts = int(item.get("max_attempts", 1))
        pass_score = float(item.get("pass_score", 5))

        if not name:
            continue

        if test_id:
            test = Test.query.filter_by(id=test_id, course_id=course_id).first()
            if test:
                test.name = name
                test.duration = duration
                test.max_attempts = max_attempts
                test.pass_score = pass_score
        else:
            test = Test(
                course_id=course_id,
                name=name,
                duration=duration,
                max_attempts=max_attempts,
                pass_score=pass_score,
            )
            db.session.add(test)

    db.session.commit()
    return True


def sync_questions(test_id, teacher_id, questions_data, pass_score):
    test = Test.query.join(Course).filter(Test.id == test_id, Course.teacher_id == teacher_id).first()
    if not test:
        return False

    test.pass_score = pass_score

    for q in test.questions:
        db.session.delete(q)
    db.session.flush()

    for q_data in questions_data:
        content = q_data.get("content", "").strip()
        if not content:
            continue

        question = Question(test_id=test.id, content=content)
        db.session.add(question)
        db.session.flush()

        for a_data in q_data.get("answers", []):
            a_content = a_data.get("content", "").strip()
            if not a_content:
                continue

            answer = Answer(
                question_id=question.id,
                content=a_content,
                is_correct=bool(a_data.get("is_correct", False)),
            )
            db.session.add(answer)

    db.session.commit()
    return True
