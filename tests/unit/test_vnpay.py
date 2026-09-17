import urllib.parse

from app import vnpay


def test_vnpay_new_order_id():
    order_id = vnpay.new_order_id(8)
    assert order_id.startswith("VNP8-")
    # Kiểm tra tính duy nhất
    order_ids = {vnpay.new_order_id(8) for _ in range(50)}
    assert len(order_ids) == 50


def test_vnpay_create_payment_url_missing_credentials(monkeypatch):
    monkeypatch.setattr(vnpay, "VNPAY_TMN_CODE", "")
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", "")
    url, err = vnpay.create_payment_url("ORDER-1", 100000, "Thanh toan")
    assert url is None
    assert "VNPAY_TMN_CODE" in err


def test_vnpay_create_payment_url_missing_return_url(monkeypatch):
    monkeypatch.setattr(vnpay, "VNPAY_TMN_CODE", "TEST_TMN")
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", "TEST_SECRET")
    monkeypatch.setattr(vnpay, "VNPAY_RETURN_URL", "")
    url, err = vnpay.create_payment_url("ORDER-1", 100000, "Thanh toan")
    assert url is None
    assert "VNPAY_RETURN_URL" in err


def test_vnpay_create_payment_url_success(monkeypatch):
    tmn_code = "DEMO_TMN"
    secret = "DEMO_SECRET_KEY_123"
    payment_url = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
    return_url = "http://localhost:8000/payment/vnpay/return"

    monkeypatch.setattr(vnpay, "VNPAY_TMN_CODE", tmn_code)
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", secret)
    monkeypatch.setattr(vnpay, "VNPAY_PAYMENT_URL", payment_url)
    monkeypatch.setattr(vnpay, "VNPAY_RETURN_URL", return_url)

    url, err = vnpay.create_payment_url(
        order_id="VNP1-12345",
        amount=150000,  # 150.000 VNĐ -> VNPay phải nhân 100 = 15.000.000
        order_info="Thanh toan khoa hoc 1",
        ip_addr="192.168.1.1",
        bank_code="NCB",
    )

    assert err is None
    assert url is not None
    assert url.startswith(payment_url)

    # Phân tích URL query parameters
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)

    assert qs["vnp_TmnCode"][0] == tmn_code
    assert qs["vnp_Amount"][0] == "15000000"  # Nhân 100
    assert qs["vnp_TxnRef"][0] == "VNP1-12345"
    assert qs["vnp_BankCode"][0] == "NCB"
    assert qs["vnp_ReturnUrl"][0] == return_url
    assert "vnp_SecureHash" in qs
    assert len(qs["vnp_SecureHash"][0]) == 128  # SHA512 ra 128 ký tự hex


def test_vnpay_verify_signature_valid_and_tampered(monkeypatch):
    secret = "MY_HASH_SECRET_KEY"
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", secret)

    # Dữ liệu mẫu từ VNPay trả về
    sample_data = {
        "vnp_Amount": "10000000",
        "vnp_BankCode": "NCB",
        "vnp_CardType": "ATM",
        "vnp_OrderInfo": "Thanh toan don hang",
        "vnp_PayDate": "20260917210000",
        "vnp_ResponseCode": "00",
        "vnp_TmnCode": "TEST_TMN",
        "vnp_TransactionNo": "14000000",
        "vnp_TransactionStatus": "00",
        "vnp_TxnRef": "VNP1-TEST",
    }

    # Tính chữ ký hợp lệ
    sorted_items = sorted(sample_data.items())
    query_str = urllib.parse.urlencode(sorted_items)
    correct_hash = vnpay._sign(query_str, secret)

    # 1. Chữ ký hợp lệ -> Verify True
    data_with_hash = dict(sample_data)
    data_with_hash["vnp_SecureHash"] = correct_hash
    assert vnpay.verify_response_signature(data_with_hash, secret) is True

    # 2. Bị sửa số tiền -> Verify False
    tampered_data = dict(data_with_hash)
    tampered_data["vnp_Amount"] = "1000"
    assert vnpay.verify_response_signature(tampered_data, secret) is False

    # 3. Thiếu SecureHash -> Verify False
    assert vnpay.verify_response_signature(sample_data, secret) is False


def test_vnpay_is_payment_success(monkeypatch):
    secret = "MY_HASH_SECRET_KEY"
    monkeypatch.setattr(vnpay, "VNPAY_HASH_SECRET", secret)

    # Case thành công: code 00 và đúng chữ ký
    success_data = {
        "vnp_Amount": "10000000",
        "vnp_ResponseCode": "00",
        "vnp_TxnRef": "VNP1-SUCCESS",
    }
    query_str = urllib.parse.urlencode(sorted(success_data.items()))
    success_data["vnp_SecureHash"] = vnpay._sign(query_str, secret)

    is_ok, msg = vnpay.is_payment_success(success_data, secret)
    assert is_ok is True
    assert msg == "Giao dịch thành công."

    # Case khách hàng hủy giao dịch: code 24
    cancel_data = {
        "vnp_Amount": "10000000",
        "vnp_ResponseCode": "24",
        "vnp_TxnRef": "VNP1-CANCEL",
    }
    query_str_cancel = urllib.parse.urlencode(sorted(cancel_data.items()))
    cancel_data["vnp_SecureHash"] = vnpay._sign(query_str_cancel, secret)

    is_ok, msg = vnpay.is_payment_success(cancel_data, secret)
    assert is_ok is False
    assert "hủy giao dịch" in msg
