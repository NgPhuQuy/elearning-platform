import uuid

import pytest

from app import dao, db
from app.index import app as flask_app
from app.models import Course, EnrollmentStatus, Payment, PaymentStatus, User


@pytest.fixture
def app_ctx():
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        yield flask_app
        db.session.rollback()


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


def test_momo_ipn_endpoint_rejects_invalid_signature(app_ctx):
    with flask_app.test_client() as client:
        # Gửi dữ liệu IPN với chữ ký rác
        fake_ipn_data = {
            "orderId": "COURSE1-fake",
            "amount": "100000",
            "signature": "invalid_signature_hash",
            "resultCode": "0",
        }
        res = client.post("/payment/momo/ipn", json=fake_ipn_data)
        # Webhook phải từ chối ngay (status code 400)
        assert res.status_code == 400


def test_vnpay_return_successful_redirects_to_learn_course(app_ctx, monkeypatch):
    import urllib.parse

    from app import vnpay

    secret = "TEST_HASH_SECRET"
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", secret)

    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"vnp_user_{unique_suffix}",
        email=f"vnp_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
        first_name="Vnpay",
        last_name="User",
    )
    course = Course(
        name=f"VNPay Course {unique_suffix}",
        activate=True,
        price=200000,
    )
    db.session.add_all([user, course])
    db.session.commit()

    order_id = f"VNP{course.id}-{unique_suffix}"
    payment = Payment(
        user_id=user.id,
        course_id=course.id,
        order_id=order_id,
        amount=course.price,
        pay_type="vnpay",
        status=PaymentStatus.PENDING,
    )
    db.session.add(payment)
    db.session.commit()

    # Chuẩn bị dữ liệu trả về thành công từ VNPay
    vnp_params = {
        "vnp_Amount": str(course.price * 100),
        "vnp_ResponseCode": "00",
        "vnp_TransactionNo": "12345678",
        "vnp_TxnRef": order_id,
    }
    query_str = urllib.parse.urlencode(sorted(vnp_params.items()))
    vnp_params["vnp_SecureHash"] = vnpay._sign(query_str, secret)

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        res = client.get("/payment/vnpay/return", query_string=vnp_params)
        # BẮT BUỘC REDIRECT THẲNG VÀO TRANG HỌC (/learn/<course_id>)
        assert res.status_code == 302
        assert f"/learn/{course.id}" in res.location

    # Kiểm tra database đã kích hoạt enrollment
    enrollment = dao.get_latest_enrollment(user.id, course.id)
    assert enrollment is not None
    assert enrollment.status == EnrollmentStatus.IN_PROGRESS

    # Dọn dẹp
    db.session.delete(payment)
    db.session.delete(enrollment)
    db.session.delete(course)
    db.session.delete(user)
    db.session.commit()


def test_vnpay_return_failed_redirects_to_course_detail(app_ctx, monkeypatch):
    import urllib.parse

    from app import vnpay

    secret = "TEST_HASH_SECRET"
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", secret)

    unique_suffix = uuid.uuid4().hex[:6]
    user = User(
        username=f"vnp_fail_{unique_suffix}",
        email=f"vnp_fail_{unique_suffix}@example.com",
        password=dao.hash_password("12345678"),
    )
    course = Course(
        name=f"Fail Course {unique_suffix}",
        activate=True,
        price=200000,
    )
    db.session.add_all([user, course])
    db.session.commit()

    order_id = f"VNP{course.id}-{unique_suffix}"
    payment = Payment(
        user_id=user.id,
        course_id=course.id,
        order_id=order_id,
        amount=course.price,
        pay_type="vnpay",
        status=PaymentStatus.PENDING,
    )
    db.session.add(payment)
    db.session.commit()

    # Khách hàng hủy giao dịch (code 24)
    vnp_params = {
        "vnp_Amount": str(course.price * 100),
        "vnp_ResponseCode": "24",
        "vnp_TxnRef": order_id,
    }
    query_str = urllib.parse.urlencode(sorted(vnp_params.items()))
    vnp_params["vnp_SecureHash"] = vnpay._sign(query_str, secret)

    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)
            sess["_fresh"] = True

        res = client.get("/payment/vnpay/return", query_string=vnp_params)
        # Redirect về trang chi tiết khóa học kèm thông báo lỗi
        assert res.status_code == 302
        assert f"/courses/{course.id}" in res.location

    # Dọn dẹp
    db.session.delete(payment)
    db.session.delete(course)
    db.session.delete(user)
    db.session.commit()


def test_vnpay_ipn_endpoint_rejects_invalid_checksum(app_ctx):
    with flask_app.test_client() as client:
        fake_ipn = {
            "vnp_Amount": "10000000",
            "vnp_SecureHash": "fake_hash_123",
            "vnp_TxnRef": "VNP1-fake",
        }
        res = client.get("/payment/vnpay/ipn", query_string=fake_ipn)
        assert res.status_code == 400
        assert res.get_json()["RspCode"] == "97"
