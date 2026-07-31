import hashlib
import hmac
import json
import os
import uuid

import requests

MOMO_PARTNER_CODE = os.environ.get("MOMO_PARTNER_CODE")
MOMO_ACCESS_KEY = os.environ.get("MOMO_ACCESS_KEY")
MOMO_SECRET_KEY = os.environ.get("MOMO_SECRET_KEY")
MOMO_ENDPOINT = os.environ.get("MOMO_ENDPOINT")
MOMO_REDIRECT_URL = os.environ.get("MOMO_REDIRECT_URL")
MOMO_IPN_URL = os.environ.get("MOMO_IPN_URL")


def _sign(raw_signature: str) -> str:
    return hmac.new(
        MOMO_SECRET_KEY.encode("utf-8"),
        raw_signature.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def new_order_id(course_id: int) -> str:
    return f"COURSE{course_id}-{uuid.uuid4().hex[:12]}"


def new_request_id() -> str:
    return str(uuid.uuid4())


def create_payment_request(order_id: str, request_id: str, amount: int, order_info: str, extra_data: str = ""):
    raw_signature = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={amount}"
        f"&extraData={extra_data}"
        f"&ipnUrl={MOMO_IPN_URL}"
        f"&orderId={order_id}"
        f"&orderInfo={order_info}"
        f"&partnerCode={MOMO_PARTNER_CODE}"
        f"&redirectUrl={MOMO_REDIRECT_URL}"
        f"&requestId={request_id}"
        f"&requestType=captureWallet"
    )
    signature = _sign(raw_signature)

    payload = {
        "partnerCode": MOMO_PARTNER_CODE,
        "partnerName": "E-Learning Platform",
        "storeId": "ElearningStore",
        "requestId": request_id,
        "amount": amount,
        "orderId": order_id,
        "orderInfo": order_info,
        "redirectUrl": MOMO_REDIRECT_URL,
        "ipnUrl": MOMO_IPN_URL,
        "lang": "vi",
        "extraData": extra_data,
        "requestType": "captureWallet",
        "signature": signature,
    }

    try:
        resp = requests.post(
            MOMO_ENDPOINT,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        data = resp.json()
    except requests.RequestException:
        return None, "Không thể kết nối tới MoMo, vui lòng thử lại sau."

    if data.get("resultCode") == 0:
        return data.get("payUrl"), None
    return None, data.get("message", "Tạo giao dịch MoMo thất bại.")


def verify_ipn_signature(data: dict) -> bool:
    raw_signature = (
        f"accessKey={MOMO_ACCESS_KEY}"
        f"&amount={data.get('amount')}"
        f"&extraData={data.get('extraData', '')}"
        f"&message={data.get('message')}"
        f"&orderId={data.get('orderId')}"
        f"&orderInfo={data.get('orderInfo')}"
        f"&orderType={data.get('orderType')}"
        f"&partnerCode={data.get('partnerCode')}"
        f"&payType={data.get('payType')}"
        f"&requestId={data.get('requestId')}"
        f"&responseTime={data.get('responseTime')}"
        f"&resultCode={data.get('resultCode')}"
        f"&transId={data.get('transId')}"
    )
    expected = _sign(raw_signature)
    return hmac.compare_digest(expected, data.get("signature", ""))