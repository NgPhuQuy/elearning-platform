import uuid
from datetime import datetime

import pytest

from app import dao, db
from app.index import app as flask_app
from app.models import (
    Course,
    EnrollmentStatus,
    Payment,
    PaymentStatus,
    Post,
    User,
    VoteType,
)


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


def test_password_hashing(app_ctx):
    hashed = dao.hash_password("12345678")
    assert isinstance(hashed, str)
    assert len(hashed) == 64


def test_enrollment_attempt_lifecycle(app_ctx):
    # Tạo user và course giả lập
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"test_user_{unique_suffix}",
        email=f"test_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
        first_name="Test",
        last_name="Student",
    )
    db.session.add(user)
    db.session.flush()

    course = Course(
        name=f"Khóa học Test {unique_suffix}",
        description="Mô tả",
        activate=True,
        price=0,
    )
    db.session.add(course)
    db.session.commit()

    # Lần 1: Đăng ký thành công
    enrollment1, err1 = dao.enroll_course(user.id, course.id)
    assert err1 is None
    assert enrollment1 is not None
    assert enrollment1.status == EnrollmentStatus.IN_PROGRESS

    # Khi đang IN_PROGRESS, không được đăng ký trùng
    enrollment_dup, err_dup = dao.enroll_course(user.id, course.id)
    assert enrollment_dup is None
    assert "quá trình học" in err_dup

    # Giả lập hoàn thành đợt 1
    enrollment1.status = EnrollmentStatus.COMPLETED
    db.session.commit()

    # Lần 2: Học viên đăng ký học lại đợt 2
    enrollment2, err2 = dao.enroll_course(user.id, course.id, force=True)
    assert err2 is None
    assert enrollment2.id != enrollment1.id
    assert enrollment2.status == EnrollmentStatus.IN_PROGRESS

    # Dọn dẹp dữ liệu test
    db.session.delete(enrollment2)
    db.session.delete(enrollment1)
    db.session.delete(course)
    db.session.delete(user)
    db.session.commit()


def test_payment_and_enrollment_link(app_ctx):
    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"pay_user_{unique_suffix}",
        email=f"pay_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
        first_name="Pay",
        last_name="User",
    )
    course = Course(
        name=f"Paid Course {unique_suffix}",
        description="Mô tả",
        activate=True,
        price=100000,
    )
    db.session.add_all([user, course])
    db.session.commit()

    order_id = f"ORDER-{unique_suffix}"
    payment = Payment(
        user_id=user.id,
        course_id=course.id,
        order_id=order_id,
        amount=course.price,
        status=PaymentStatus.PENDING,
    )
    db.session.add(payment)
    db.session.commit()

    # Xác nhận thanh toán thành công
    confirmed = dao.confirm_payment_success(order_id=order_id, momo_trans_id="MOMO123", pay_type="qr")
    assert confirmed.status == PaymentStatus.SUCCESS

    # Kiểm tra enrollment mới được kích hoạt
    enrollment = dao.get_latest_enrollment(user.id, course.id)
    assert enrollment is not None
    assert enrollment.user_id == user.id
    assert enrollment.course_id == course.id
    assert enrollment.status == EnrollmentStatus.IN_PROGRESS

    # Dọn dẹp dữ liệu test
    db.session.delete(payment)
    db.session.delete(enrollment)
    db.session.delete(course)
    db.session.delete(user)
    db.session.commit()


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


def test_upload_helper_handles_empty(app_ctx):
    from app.services.upload_service import upload_file

    url, err = upload_file(None)
    assert url is None
    assert err is None


def test_socket_auth_decorator_blocks_unauthenticated(app_ctx):
    from app.decorators import socket_auth_required

    @socket_auth_required
    def dummy_handler(data):
        return "allowed"

    # Khi chưa authenticate
    res = dummy_handler({})
    assert res is None


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
        # Phải redirect về /forum/post_id an toàn (302) thay vì 500 crash
        assert res.status_code == 302

    # Dọn dẹp
    db.session.delete(post)
    db.session.delete(user)
    db.session.commit()
