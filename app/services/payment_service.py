from app import dao, momo


def checkout_course(user_id, course_id):
    return dao.create_payment(user_id=user_id, course_id=course_id)


def checkout_vnpay(user_id, course_id, ip_addr="127.0.0.1", bank_code=None):
    return dao.create_vnpay_payment(user_id=user_id, course_id=course_id, ip_addr=ip_addr, bank_code=bank_code)


def process_vnpay_return(params):
    from app import vnpay

    is_success, message = vnpay.is_payment_success(params)
    order_id = params.get("vnp_TxnRef")
    trans_id = params.get("vnp_TransactionNo", "")

    if is_success:
        payment = dao.confirm_payment_success(order_id, momo_trans_id=f"VNP_{trans_id}", pay_type="vnpay")
    else:
        payment = dao.confirm_payment_failed(order_id)

    if not payment and order_id:
        payment = dao.get_payment_by_order_id(order_id)

    return payment, is_success, message


def process_vnpay_ipn(params):
    from app import vnpay

    if not vnpay.verify_response_signature(params):
        return False, "Invalid signature"

    order_id = params.get("vnp_TxnRef")
    response_code = params.get("vnp_ResponseCode", "")
    trans_id = params.get("vnp_TransactionNo", "")

    if response_code == "00":
        dao.confirm_payment_success(order_id, momo_trans_id=f"VNP_{trans_id}", pay_type="vnpay")
    else:
        dao.confirm_payment_failed(order_id)

    return True, "IPN processed successfully"


def process_ipn(data):
    if not momo.verify_ipn_signature(data):
        return False, "Invalid signature"

    order_id = data.get("orderId")
    result_code = int(data.get("resultCode", -1))
    trans_id = str(data.get("transId", ""))
    pay_type = str(data.get("payType", ""))

    if result_code == 0:
        dao.confirm_payment_success(order_id, momo_trans_id=trans_id, pay_type=pay_type)
    else:
        dao.confirm_payment_failed(order_id)

    return True, "IPN processed successfully"


def process_return(params):
    order_id = params.get("orderId")
    result_code = int(params.get("resultCode", -1))
    trans_id = str(params.get("transId", ""))
    pay_type = str(params.get("payType", ""))

    if result_code == 0:
        payment = dao.confirm_payment_success(order_id, momo_trans_id=trans_id, pay_type=pay_type)
    else:
        payment = dao.confirm_payment_failed(order_id)

    if not payment:
        payment = dao.get_payment_by_order_id(order_id)

    return payment, result_code == 0


def get_my_payments(user_id):
    return dao.get_my_payments(user_id)
