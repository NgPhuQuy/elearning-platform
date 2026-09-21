from app.models import Certificate


def get_certificate_by_id(cert_id):
    return Certificate.query.get(cert_id)


def get_certificate_by_enrollment(enrollment_id):
    return Certificate.query.filter_by(enrollment_id=enrollment_id).first()


def get_user_certificates(user_id):
    return (
        Certificate.query.join(Certificate.enrollment)
        .filter_by(user_id=user_id)
        .order_by(Certificate.issued_date.desc())
        .all()
    )

