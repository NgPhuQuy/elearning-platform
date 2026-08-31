from app import dao, momo


def checkout_course(user_id, course_id):
    return dao.create_payment(user_id=user_id, course_id=course_id)


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
