import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
MAIL_SENDER = os.environ.get("MAIL_SENDER", MAIL_USERNAME)


def _send(to_email: str, subject: str, html_body: str) -> tuple[bool, str | None]:
    server_host = os.environ.get("MAIL_SERVER") or MAIL_SERVER
    server_port = int(os.environ.get("MAIL_PORT") or MAIL_PORT)
    username = os.environ.get("MAIL_USERNAME") or MAIL_USERNAME
    password = os.environ.get("MAIL_PASSWORD") or MAIL_PASSWORD
    sender = os.environ.get("MAIL_SENDER") or username or MAIL_SENDER

    if not username or not password:
        return False, "Chưa cấu hình MAIL_USERNAME/MAIL_PASSWORD."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(server_host, server_port, timeout=10) as server:
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


def send_invoice_email(payment, user, course) -> tuple[bool, str | None]:
    """payment, user, course: các object model tương ứng."""
    subject = f"Hóa đơn thanh toán khóa học: {course.name}"
    gateway_name = (payment.pay_type or "vnpay").upper()
    trans_id = payment.momo_trans_id or payment.order_id or "-"
    paid_time = payment.paid_at.strftime("%H:%M %d/%m/%Y") if payment.paid_at else "-"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #4338ca; margin-top: 0;">Hóa đơn thanh toán khóa học</h2>
        <p>Xin chào <strong>{user.first_name} {user.last_name}</strong>,</p>
        <p>Bạn đã thanh toán thành công và khóa học đã được kích hoạt trên hệ thống:</p>
        <table style="width:100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 16px;">
            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding:8px 0; color: #64748b;">Mã đơn hàng</td><td><strong>{payment.order_id}</strong></td></tr>
            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding:8px 0; color: #64748b;">Khóa học</td><td><strong>{course.name}</strong></td></tr>
            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding:8px 0; color: #64748b;">Số tiền</td><td><strong style="color: #4338ca;">{payment.amount:,} VNĐ</strong></td></tr>
            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding:8px 0; color: #64748b;">Cổng thanh toán</td><td><strong>{gateway_name}</strong></td></tr>
            <tr style="border-bottom: 1px solid #f1f5f9;"><td style="padding:8px 0; color: #64748b;">Mã giao dịch</td><td>{trans_id}</td></tr>
            <tr><td style="padding:8px 0; color: #64748b;">Thời gian thanh toán</td><td>{paid_time}</td></tr>
        </table>
        <p style="margin-top:20px; color: #334155;">Cảm ơn bạn đã đồng hành cùng chúng tôi. Chúc bạn học tập hiệu quả!</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="font-size: 12px; color: #94a3b8; text-align: center;">Đây là email tự động từ hệ thống Elearning Platform, vui lòng không phản hồi thư này.</p>
    </div>
    """
    return _send(user.email, subject, html_body)
