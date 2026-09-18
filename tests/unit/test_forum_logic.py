from unittest.mock import MagicMock

from app.dao import forum_dao
from app.models import VoteType


def test_calculate_post_score_empty():
    post = MagicMock(reactions=[])
    score = sum(1 if r.vote_type == VoteType.UP else -1 for r in post.reactions)
    assert score == 0


def test_calculate_post_score_mixed():
    r1 = MagicMock(vote_type=VoteType.UP)
    r2 = MagicMock(vote_type=VoteType.UP)
    r3 = MagicMock(vote_type=VoteType.DOWN)
    post = MagicMock(reactions=[r1, r2, r3])

    score = sum(1 if r.vote_type == VoteType.UP else -1 for r in post.reactions)
    assert score == 1  # 2 up - 1 down = 1


def test_vote_entity_toggle_same_vote_deletes_reaction():
    # User upvote khi đã upvote trước đó -> hủy vote (delete reaction)
    mock_model_cls = MagicMock()
    existing_reaction = MagicMock(vote_type=VoteType.UP)
    mock_model_cls.query.filter_by.return_value.first.return_value = existing_reaction

    mock_db = MagicMock()
    original_db = forum_dao.db
    try:
        forum_dao.db = mock_db
        forum_dao._vote_entity(mock_model_cls, "post_id", 1, 10, VoteType.UP)

        # Vì cùng loại vote (UP) -> gọi delete
        mock_db.session.delete.assert_called_once_with(existing_reaction)
        mock_db.session.commit.assert_called_once()
    finally:
        forum_dao.db = original_db


def test_vote_entity_change_vote_updates_type():
    # User downvote khi đang upvote -> chuyển thành downvote (không xóa)
    mock_model_cls = MagicMock()
    existing_reaction = MagicMock(vote_type=VoteType.UP)
    mock_model_cls.query.filter_by.return_value.first.return_value = existing_reaction

    mock_db = MagicMock()
    original_db = forum_dao.db
    try:
        forum_dao.db = mock_db
        forum_dao._vote_entity(mock_model_cls, "post_id", 1, 10, VoteType.DOWN)

        # Chuyển vote_type thành DOWN
        assert existing_reaction.vote_type == VoteType.DOWN
        mock_db.session.delete.assert_not_called()
        mock_db.session.commit.assert_called_once()
    finally:
        forum_dao.db = original_db


def test_vote_entity_new_vote_creates_reaction():
    # Chưa từng vote -> tạo reaction mới
    mock_model_cls = MagicMock()
    mock_model_cls.query.filter_by.return_value.first.return_value = None

    mock_db = MagicMock()
    original_db = forum_dao.db
    try:
        forum_dao.db = mock_db
        forum_dao._vote_entity(mock_model_cls, "post_id", 1, 10, VoteType.UP)

        mock_db.session.add.assert_called_once()
        mock_db.session.commit.assert_called_once()
    finally:
        forum_dao.db = original_db
