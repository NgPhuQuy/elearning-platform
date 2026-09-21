from flask import abort, render_template

from app import app, dao


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

