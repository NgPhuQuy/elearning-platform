from app.models import Certificate, Enrollment


def get_certificate_by_id(cert_id):
    return Certificate.query.get(cert_id)


def get_certificate_by_enrollment(enrollment_id):
    return Certificate.query.filter_by(enrollment_id=enrollment_id).first()


def get_user_certificates(user_id):
    return (
        Certificate.query.join(Enrollment, Certificate.enrollment_id == Enrollment.id)
        .filter(Enrollment.user_id == user_id)
        .order_by(Certificate.issued_date.desc())
        .all()
    )
