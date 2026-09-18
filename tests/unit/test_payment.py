import hashlib
import hmac

from app import momo


def test_new_order_id_format():
    order_id = momo.new_order_id(15)
    assert order_id.startswith("COURSE15-")
    hex_part = order_id.replace("COURSE15-", "")
    assert len(hex_part) == 12
    assert hex_part.isalnum()


def test_new_order_id_uniqueness():
    ids = {momo.new_order_id(1) for _ in range(50)}
    assert len(ids) == 50


def test_sign_hmac(monkeypatch):
    monkeypatch.setattr(momo, "MOMO_SECRET_KEY", "test-secret-key")
    raw = "accessKey=test&amount=100000&orderId=COURSE1-abc"
    expected = hmac.new(b"test-secret-key", raw.encode("utf-8"), hashlib.sha256).hexdigest()
    assert momo._sign(raw) == expected


def test_verify_ipn_signature_valid(monkeypatch):
    secret_key = "test-secret-key"
    access_key = "test-access-key"
    monkeypatch.setattr(momo, "MOMO_SECRET_KEY", secret_key)
    monkeypatch.setattr(momo, "MOMO_ACCESS_KEY", access_key)

    data = {
        "amount": "200000",
        "extraData": "",
        "message": "Successful.",
        "orderId": "COURSE5-abcdef123456",
        "orderInfo": "Thanh toan khoa hoc",
        "orderType": "momo_wallet",
        "partnerCode": "MOMO",
        "payType": "qr",
        "requestId": "req-1234",
        "responseTime": "1700000000000",
        "resultCode": "0",
        "transId": "999999",
    }

    raw = (
        f"accessKey={access_key}"
        f"&amount={data['amount']}"
        f"&extraData={data['extraData']}"
        f"&message={data['message']}"
        f"&orderId={data['orderId']}"
        f"&orderInfo={data['orderInfo']}"
        f"&orderType={data['orderType']}"
        f"&partnerCode={data['partnerCode']}"
        f"&payType={data['payType']}"
        f"&requestId={data['requestId']}"
        f"&responseTime={data['responseTime']}"
        f"&resultCode={data['resultCode']}"
        f"&transId={data['transId']}"
    )
    valid_signature = hmac.new(secret_key.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    data["signature"] = valid_signature

    assert momo.verify_ipn_signature(data) is True


def test_verify_ipn_signature_tampered_amount(monkeypatch):
    secret_key = "test-secret-key"
    access_key = "test-access-key"
    monkeypatch.setattr(momo, "MOMO_SECRET_KEY", secret_key)
    monkeypatch.setattr(momo, "MOMO_ACCESS_KEY", access_key)

    data = {
        "amount": "500000",
        "extraData": "",
        "message": "Successful.",
        "orderId": "COURSE5-abcdef123456",
        "orderInfo": "Thanh toan khoa hoc",
        "orderType": "momo_wallet",
        "partnerCode": "MOMO",
        "payType": "qr",
        "requestId": "req-1234",
        "responseTime": "1700000000000",
        "resultCode": "0",
        "transId": "999999",
    }
    raw = (
        f"accessKey={access_key}"
        f"&amount={data['amount']}"
        f"&extraData={data['extraData']}"
        f"&message={data['message']}"
        f"&orderId={data['orderId']}"
        f"&orderInfo={data['orderInfo']}"
        f"&orderType={data['orderType']}"
        f"&partnerCode={data['partnerCode']}"
        f"&payType={data['payType']}"
        f"&requestId={data['requestId']}"
        f"&responseTime={data['responseTime']}"
        f"&resultCode={data['resultCode']}"
        f"&transId={data['transId']}"
    )
    valid_signature = hmac.new(secret_key.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    data["signature"] = valid_signature

    # Hacker thay đổi số tiền thành 1000 nhưng không có secret key để ký lại
    data["amount"] = "1000"
    assert momo.verify_ipn_signature(data) is False


def test_verify_ipn_signature_missing_signature(monkeypatch):
    monkeypatch.setattr(momo, "MOMO_SECRET_KEY", "secret")
    monkeypatch.setattr(momo, "MOMO_ACCESS_KEY", "access")
    data = {"amount": "100000"}
    assert momo.verify_ipn_signature(data) is False
