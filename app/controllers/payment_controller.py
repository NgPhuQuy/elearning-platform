from flask import jsonify, redirect, render_template, request, url_for
from flask_login import current_user

from app import app
from app.decorators import login_required
from app.services import payment_service


@app.route("/courses/<int:course_id>/checkout", methods=["GET", "POST"])
@login_required
def checkout_course(course_id):
    pay_url, error = payment_service.checkout_course(user_id=current_user.id, course_id=course_id)
    if error:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": error}), 400
        return redirect(url_for("course_detail", course_id=course_id, error=error))
    return redirect(pay_url)


@app.route("/payment/momo/ipn", methods=["POST"])
def momo_ipn():
    data = request.get_json(silent=True) or {}
    ok, message = payment_service.process_ipn(data)
    if not ok:
        return jsonify({"message": message}), 400
    return jsonify({"message": message}), 204


@app.route("/payment/momo/return")
@login_required
def momo_return():
    payment, is_success = payment_service.process_return(request.args)
    return render_template("payment/result.html", payment=payment, is_success=is_success)


@app.route("/payment/history")
@login_required
def payment_history():
    payments = payment_service.get_my_payments(current_user.id)
    return render_template("payment/history.html", payments=payments)
