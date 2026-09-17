from __future__ import annotations

import hashlib
import hmac
import os
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone

VNPAY_TMN_CODE = os.environ.get("VNPAY_TMN_CODE")
VNPAY_HASH_SECRET = os.environ.get("VNPAY_HASH_SECRET")
VNPAY_PAYMENT_URL = os.environ.get("VNPAY_PAYMENT_URL")
VNPAY_RETURN_URL = os.environ.get("VNPAY_RETURN_URL")

# Múi giờ Việt Nam GMT+7
VIETNAM_TZ = timezone(timedelta(hours=7))

# Bảng dịch mã phản hồi VNPay sang thông báo người dùng dễ hiểu
VNPAY_RESPONSE_CODES: dict[str, str] = {
    "00": "Giao dịch thành công.",
    "07": "Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, bất thường).",
    "09": "Giao dịch không thành công do: Thẻ/Tài khoản chưa đăng ký dịch vụ InternetBanking.",
    "10": "Giao dịch không thành công do: Khách hàng xác thực thông tin thẻ/tài khoản không đúng quá 3 lần.",
    "11": "Giao dịch không thành công do: Đã hết hạn chờ thanh toán.",
    "12": "Giao dịch không thành công do: Thẻ/Tài khoản bị khóa.",
    "13": "Giao dịch không thành công do: Nhập sai mật khẩu xác thực OTP.",
    "24": "Giao dịch không thành công do: Khách hàng hủy giao dịch.",
    "51": "Giao dịch không thành công do: Tài khoản không đủ số dư.",
    "65": "Giao dịch không thành công do: Tài khoản đã vượt quá hạn mức giao dịch trong ngày.",
    "75": "Ngân hàng thanh toán đang bảo trì.",
    "79": "Giao dịch không thành công do: Nhập sai mật khẩu thanh toán quá số lần quy định.",
    "99": "Các lỗi khác (lỗi chưa được định danh từ ngân hàng).",
}


def _get_hash_secret() -> str:
    return VNPAY_HASH_SECRET


def _get_tmn_code() -> str:
    return VNPAY_TMN_CODE


def _sign(query_string: str, secret_key: str | None = None) -> str:
    key = (secret_key or _get_hash_secret()).encode("utf-8")
    return hmac.new(
        key,
        query_string.encode("utf-8"),
        hashlib.sha512,
    ).hexdigest()


def new_order_id(course_id: int) -> str:
    """Sinh mã giao dịch duy nhất (vnp_TxnRef), bắt buộc là chuỗi ký tự duy nhất cho mỗi lần bấm thanh toán."""
    time_prefix = datetime.now(VIETNAM_TZ).strftime("%y%m%d%H%M%S")
    unique_hex = uuid.uuid4().hex[:6]
    return f"VNP{course_id}-{time_prefix}{unique_hex}"


def create_payment_url(
    order_id: str,
    amount: int | float,
    order_info: str,
    ip_addr: str = "127.0.0.1",
    bank_code: str | None = None,
    locale: str = "vn",
    order_type: str = "other",
    expire_minutes: int = 15,
) -> tuple[str | None, str | None]:
    """Tạo URL thanh toán chuyển hướng người dùng sang cổng VNPay.

    :param order_id: Mã đơn hàng (vnp_TxnRef)
    :param amount: Số tiền (VNĐ). VNPay yêu cầu nhân 100 khi gửi đi.
    :param order_info: Nội dung thanh toán (vnp_OrderInfo)
    :param ip_addr: IP của client thực hiện request
    :param bank_code: Mã ngân hàng (VNPAYQR, VNBANK, INTCARD...) hoặc None để user tự chọn
    :param locale: Ngôn ngữ ('vn' hoặc 'en')
    :param order_type: Loại hàng hóa/dịch vụ
    :param expire_minutes: Thời hạn chờ thanh toán (phút)
    :return: (payment_url, error_message)
    """
    tmn_code = _get_tmn_code()
    hash_secret = _get_hash_secret()
    payment_url = os.environ.get("VNPAY_PAYMENT_URL") or VNPAY_PAYMENT_URL
    return_url = os.environ.get("VNPAY_RETURN_URL") or VNPAY_RETURN_URL

    if not tmn_code or not hash_secret:
        return None, "Chưa cấu hình VNPAY_TMN_CODE hoặc VNPAY_HASH_SECRET trong biến môi trường."

    if not return_url:
        return None, "Chưa cấu hình VNPAY_RETURN_URL trong biến môi trường."

    now = datetime.now(VIETNAM_TZ)
    create_date = now.strftime("%Y%m%d%H%M%S")
    expire_date = (now + timedelta(minutes=expire_minutes)).strftime("%Y%m%d%H%M%S")

    # VNPay yêu cầu số tiền tính theo đơn vị Đồng * 100 (không có dấu thập phân)
    vnp_amount = str(int(amount) * 100)

    vnp_params: dict[str, str] = {
        "vnp_Version": "2.1.0",
        "vnp_Command": "pay",
        "vnp_TmnCode": tmn_code,
        "vnp_Amount": vnp_amount,
        "vnp_CurrCode": "VND",
        "vnp_TxnRef": str(order_id),
        "vnp_OrderInfo": str(order_info),
        "vnp_OrderType": str(order_type),
        "vnp_Locale": str(locale),
        "vnp_ReturnUrl": return_url,
        "vnp_IpAddr": str(ip_addr),
        "vnp_CreateDate": create_date,
        "vnp_ExpireDate": expire_date,
    }

    if bank_code:
        vnp_params["vnp_BankCode"] = bank_code

    # Sắp xếp các tham số theo thứ tự a-z
    sorted_params = sorted(vnp_params.items())

    # Build query string chuẩn url-encoded
    query_string = urllib.parse.urlencode(sorted_params)

    # Ký HMAC-SHA512 trên chuỗi query_string
    secure_hash = _sign(query_string, hash_secret)

    full_payment_url = f"{payment_url}?{query_string}&vnp_SecureHash={secure_hash}"
    return full_payment_url, None


def verify_response_signature(data: dict[str, str], secret_key: str | None = None) -> bool:
    """Xác thực chữ ký phản hồi từ VNPay (áp dụng cho cả Return URL và IPN Webhook).

    :param data: Dictionary chứa các tham số VNPay trả về (request.args hoặc request.form)
    :param secret_key: Khóa bí mật (nếu None sẽ lấy từ env)
    :return: True nếu chữ ký hợp lệ và dữ liệu không bị can thiệp, False nếu sai.
    """
    received_hash = data.get("vnp_SecureHash", "")
    if not received_hash:
        return False

    hash_secret = secret_key or _get_hash_secret()
    if not hash_secret:
        return False

    # Lọc các tham số bắt đầu bằng "vnp_", loại bỏ vnp_SecureHash và vnp_SecureHashType
    filtered_params = {
        k: v for k, v in data.items() if k.startswith("vnp_") and k not in ("vnp_SecureHash", "vnp_SecureHashType")
    }

    # Sắp xếp theo thứ tự a-z
    sorted_params = sorted(filtered_params.items())

    # Tạo query string
    query_string = urllib.parse.urlencode(sorted_params)

    # Tính chữ ký kỳ vọng
    expected_hash = _sign(query_string, hash_secret)

    # So sánh an toàn chống timing attack
    return hmac.compare_digest(expected_hash.lower(), received_hash.lower())


def is_payment_success(data: dict[str, str], secret_key: str | None = None) -> tuple[bool, str]:
    """Kiểm tra toàn diện giao dịch VNPay trả về: vừa đúng chữ ký vừa có mã kết quả thành công (00).

    :param data: Dữ liệu VNPay gửi về
    :param secret_key: Khóa bí mật
    :return: (is_success, message)
    """
    if not verify_response_signature(data, secret_key):
        return False, "Chữ ký bảo mật VNPay không hợp lệ (nguy cơ can thiệp dữ liệu)."

    response_code = data.get("vnp_ResponseCode", "")
    message = VNPAY_RESPONSE_CODES.get(response_code, f"Mã lỗi VNPay: {response_code}")

    if response_code == "00":
        return True, message

    return False, message
