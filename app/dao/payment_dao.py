from datetime import datetime

from app import db, momo
from app.dao.enrollment_dao import enroll_course, is_enrolled
from app.models import Course, Payment, PaymentStatus


def create_payment(user_id, course_id):
    course = Course.query.get(course_id)
    if not course:
        return None, "Khóa học không tồn tại."
    if not course.activate:
        return None, "Khóa học chưa được công khai."
    if is_enrolled(user_id, course_id):
        return None, "Bạn đã đăng ký khóa học này rồi."
    if not course.price or course.price <= 0:
        return None, "Khóa học này miễn phí, hãy bấm Đăng ký học."

    order_id = momo.new_order_id(course_id)
    request_id = momo.new_request_id()
    order_info = f"Thanh toán khóa học {course.name}"

    payment = Payment(
        user_id=user_id,
        course_id=course_id,
        order_id=order_id,
        request_id=request_id,
        amount=course.price,
        status=PaymentStatus.PENDING,
    )
    try:
        db.session.add(payment)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return None, "Không thể khởi tạo giao dịch thanh toán."

    pay_url, error = momo.create_payment_request(
        order_id=order_id,
        request_id=request_id,
        amount=course.price,
        order_info=order_info,
    )
    if error:
        payment.status = PaymentStatus.FAILED
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        return None, error

    return pay_url, None


def confirm_payment_success(order_id, momo_trans_id=None, pay_type=None):
    payment = Payment.query.filter_by(order_id=order_id).first()
    if not payment:
        return None

    if payment.status == PaymentStatus.SUCCESS:
        return payment

    payment.status = PaymentStatus.SUCCESS
    payment.momo_trans_id = momo_trans_id
    payment.pay_type = pay_type
    payment.paid_at = datetime.now()

    enroll_course(payment.user_id, payment.course_id, force=True, price=payment.amount)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return payment

    if not payment.invoice_sent and payment.user and payment.course:
        try:
            from app.mailer import send_invoice_email

            sent, _ = send_invoice_email(payment, payment.user, payment.course)
            if sent:
                payment.invoice_sent = True
                db.session.commit()
        except Exception:
            pass

    return payment


def confirm_payment_failed(order_id):
    payment = Payment.query.filter_by(order_id=order_id).first()
    if payment and payment.status == PaymentStatus.PENDING:
        payment.status = PaymentStatus.FAILED
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    return payment


def get_payment_by_order_id(order_id):
    return Payment.query.filter_by(order_id=order_id).first()


def get_my_payments(user_id):
    return Payment.query.filter_by(user_id=user_id).order_by(Payment.created_date.desc()).all()

