import uuid
from datetime import datetime

import pytest

from app import dao, db
from app.index import app as flask_app
from app.models import Post, User, VoteType


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


def test_voting_dry_helpers(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"vote_user_{unique_suffix}",
        email=f"vote_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    post = Post(title="Post Test", content="Nội dung", user=user)
    db.session.add_all([user, post])
    db.session.commit()

    # Upvote
    dao.vote_post(post.id, user.id, VoteType.UP)
    assert dao.get_post_score(post) == 1

    # Upvote lần nữa -> Hủy vote (score về 0)
    dao.vote_post(post.id, user.id, VoteType.UP)
    assert dao.get_post_score(post) == 0

    # Downvote -> score = -1
    dao.vote_post(post.id, user.id, VoteType.DOWN)
    assert dao.get_post_score(post) == -1

    # Dọn dẹp
    db.session.delete(post)
    db.session.delete(user)
    db.session.commit()


def test_get_question_today(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"today_user_{unique_suffix}",
        email=f"today_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    post = Post(
        title=f"Question Today {unique_suffix}", content="Hỏi đáp hôm nay", user=user, created_date=datetime.now()
    )
    db.session.add_all([user, post])
    db.session.commit()

    today_posts = dao.get_question_today()
    assert any(p.id == post.id for p in today_posts)

    # Dọn dẹp
    db.session.delete(post)
    db.session.delete(user)
    db.session.commit()


def test_safe_referrer_fallback_in_endpoints(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"ref_user_{unique_suffix}",
        email=f"ref_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    post = Post(title="Post Referrer", content="Content", user=user)
    db.session.add_all([user, post])
    db.session.commit()

    with flask_app.test_client() as client:
        # Giả lập login
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        # Gửi POST không có Referer header
        res = client.post(f"/forum/{post.id}/upvote")
        assert res.status_code == 302

    # Dọn dẹp
    db.session.delete(post)
    db.session.delete(user)
    db.session.commit()


def test_create_question_and_answer_flow(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    author = User(
        username=f"author_{unique_suffix}",
        email=f"author_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    responder = User(
        username=f"resp_{unique_suffix}",
        email=f"resp_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    db.session.add_all([author, responder])
    db.session.commit()

    # 1. Tạo bài viết câu hỏi
    post = dao.create_post(title=f"Question {unique_suffix}", content="Cần giúp đỡ", category_ids=[], user_id=author.id)
    assert post.is_solved is False

    # 2. Người khác vào trả lời
    comment = dao.add_comment(post_id=post.id, user_id=responder.id, content="Đây là câu trả lời")
    assert comment is not None
    assert comment.is_accepted is False

    # Dọn dẹp
    db.session.delete(comment)
    db.session.delete(post)
    db.session.delete(responder)
    db.session.delete(author)
    db.session.commit()
