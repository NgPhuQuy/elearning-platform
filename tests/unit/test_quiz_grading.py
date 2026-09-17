from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services import test_service


# -------------------------------------------------------------
# 1. Tính toán thời gian làm bài (Countdown & Timeout logic)
# -------------------------------------------------------------
def test_calculate_remaining_time_unlimited_duration():
    fake_test = MagicMock(duration=0)
    remaining, is_timeout = test_service.calculate_remaining_time(fake_test, "key", {})
    assert remaining == 0
    assert is_timeout is False


def test_calculate_remaining_time_no_start_time_in_session():
    fake_test = MagicMock(duration=30)
    remaining, is_timeout = test_service.calculate_remaining_time(fake_test, "key", {})
    assert remaining == 0
    assert is_timeout is True


def test_calculate_remaining_time_still_active():
    fake_test = MagicMock(duration=30)  # 30 phút = 1800 giây
    # Bắt đầu làm bài cách đây 10 phút = 600 giây
    start_time = (datetime.now() - timedelta(minutes=10)).isoformat()
    session_store = {"test_key": start_time}

    remaining, is_timeout = test_service.calculate_remaining_time(fake_test, "test_key", session_store)
    # Thời gian còn lại xấp xỉ 20 phút = 1200 giây
    assert 1195 <= remaining <= 1205
    assert is_timeout is False


def test_calculate_remaining_time_expired():
    fake_test = MagicMock(duration=15)  # 15 phút
    # Bắt đầu làm bài cách đây 20 phút -> đã hết giờ
    start_time = (datetime.now() - timedelta(minutes=20)).isoformat()
    session_store = {"test_key": start_time}

    remaining, is_timeout = test_service.calculate_remaining_time(fake_test, "test_key", session_store)
    assert remaining == 0
    assert is_timeout is True


# -------------------------------------------------------------
# 2. Đồng bộ câu hỏi từ JSON (Validation logic)
# -------------------------------------------------------------
def test_sync_questions_missing_data():
    res = test_service.sync_questions(1, 1, {})
    assert res is False


def test_sync_questions_invalid_json():
    res = test_service.sync_questions(1, 1, {"questions_data": "invalid_json_format{{"})
    assert res is False


@patch("app.services.test_service.dao")
def test_sync_questions_valid_json(mock_dao):
    mock_dao.sync_questions.return_value = True
    valid_data = {"questions_data": '[{"question": "1+1=?", "answers": []}]', "pass_score": "6.0"}
    res = test_service.sync_questions(1, 1, valid_data)
    assert res is True
    mock_dao.sync_questions.assert_called_once_with(
        test_id=1,
        teacher_id=1,
        questions_data=[{"question": "1+1=?", "answers": []}],
        pass_score=6.0,
    )


# -------------------------------------------------------------
# 3. Tính điểm thi & Điểm cao nhất từ nhiều lượt (Grading & Best score)
# -------------------------------------------------------------
@pytest.mark.parametrize(
    "correct_count, total_q, expected_score",
    [
        (0, 10, 0.0),
        (5, 10, 5.0),
        (10, 10, 10.0),
        (7, 10, 7.0),
        (3, 7, 4.29),  # round((3/7)*10, 2) = 4.29
        (1, 3, 3.33),  # round((1/3)*10, 2) = 3.33
        (0, 0, 0.0),
    ],
)
def test_score_calculation_formula(correct_count, total_q, expected_score):
    if total_q == 0:
        score = 0.0
    else:
        score = round((correct_count / total_q) * 10, 2)
    assert score == expected_score


@patch("app.services.test_service.dao")
def test_get_test_context_best_score_and_attempts_left(mock_dao):
    fake_test = MagicMock(id=1, max_attempts=3)
    mock_dao.get_test_details.return_value = fake_test
    mock_dao.can_take_test.return_value = (True, None)

    attempt1 = MagicMock(score_value=4.5)
    attempt2 = MagicMock(score_value=8.0)
    mock_dao.get_test_attempts.return_value = [attempt1, attempt2]

    ctx, err = test_service.get_test_context(course_id=1, test_id=1, user_id=10)

    assert err is None
    assert ctx["attempts_count"] == 2
    assert ctx["attempts_left"] == 1  # 3 - 2 = 1
    assert ctx["best_score"] == 8.0  # max(4.5, 8.0) = 8.0
    assert ctx["can_take"] is True


@patch("app.services.test_service.dao")
def test_get_test_context_test_not_found(mock_dao):
    mock_dao.get_test_details.return_value = None
    ctx, err = test_service.get_test_context(course_id=1, test_id=999, user_id=10)
    assert ctx is None
    assert err == "Bài kiểm tra không tồn tại."
