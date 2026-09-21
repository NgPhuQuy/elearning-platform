from flask import abort, render_template
from flask_login import current_user

from app import app, dao
from app.decorators import login_required


@app.route("/certificates/<int:cert_id>")
def view_certificate(cert_id):
    cert = dao.get_certificate_by_id(cert_id)
    if not cert:
        abort(404)

    user = cert.enrollment.user if cert.enrollment else None
    course = cert.course
    recipient_name = f"{user.first_name or ''} {user.last_name or ''}".strip() if user else "Học viên"

    return render_template(
        "certificate/view.html",
        certificate=cert,
        course=course,
        user=user,
        recipient_name=recipient_name,
    )


@app.route("/my-certificates", endpoint="my_certificates")
@app.route("/my-certificate", endpoint="my_certificate")
@login_required
def my_certificates():
    certificates = dao.get_user_certificates(current_user.id)
    return render_template("certificate/my_certificates.html", certificates=certificates)
