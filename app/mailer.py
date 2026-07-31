import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_SENDER = os.environ.get("MAIL_SENDER", MAIL_USERNAME)


def _send(to_email: str, subject: str, html_body: str) -> tuple[bool, str | None]:
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        return False, "Chưa cấu hình MAIL_USERNAME/MAIL_PASSWORD."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = MAIL_SENDER
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_SENDER, [to_email], msg.as_string())
        return True, None
    except smtplib.SMTPException as e:
        return False, str(e)


def send_invoice_email(payment, user, course) -> tuple[bool, str | None]:
    """payment, user, course: các object model tương ứng."""
    subject = f"Hóa đơn thanh toán khóa học: {course.name}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: auto;">
        <h2>Hóa đơn thanh toán</h2>
        <p>Xin chào <strong>{user.first_name} {user.last_name}</strong>,</p>
        <p>Bạn đã thanh toán thành công khóa học sau:</p>
        <table style="width:100%; border-collapse: collapse;">
            <tr><td style="padding:6px 0;">Mã đơn hàng</td><td><strong>{payment.order_id}</strong></td></tr>
            <tr><td style="padding:6px 0;">Khóa học</td><td>{course.name}</td></tr>
            <tr><td style="padding:6px 0;">Số tiền</td><td><strong>{payment.amount:,} VNĐ</strong></td></tr>
            <tr><td style="padding:6px 0;">Mã giao dịch MoMo</td><td>{payment.momo_trans_id or "-"}</td></tr>
            <tr><td style="padding:6px 0;">Thời gian</td><td>{payment.paid_at.strftime("%H:%M %d/%m/%Y") if payment.paid_at else "-"}</td></tr>
        </table>
        <p style="margin-top:16px;">Cảm ơn bạn đã sử dụng dịch vụ. Chúc bạn học tốt!</p>
    </div>
    """
    return _send(user.email, subject, html_body)