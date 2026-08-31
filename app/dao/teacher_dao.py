from datetime import datetime, timedelta

from app import TEACHER_APPLICATION_COOLDOWN_DAYS, db
from app.models import ApplicationStatus, TeacherApplication


def can_apply_teacher(user_id):
    latest = (
        TeacherApplication.query.filter_by(user_id=user_id).order_by(TeacherApplication.created_date.desc()).first()
    )
    if not latest:
        return True, ""

    if latest.status == ApplicationStatus.PENDING:
        return False, "Bạn đã có đơn đăng ký đang chờ xét duyệt."

    if latest.status == ApplicationStatus.APPROVED:
        return False, "Tài khoản của bạn đã là giảng viên."

    if latest.status == ApplicationStatus.REJECTED:
        cooldown = timedelta(days=TEACHER_APPLICATION_COOLDOWN_DAYS)
        ref_time = latest.reviewed_at or latest.created_date
        unlock_date = ref_time + cooldown
        if datetime.now() < unlock_date:
            days_left = (unlock_date - datetime.now()).days + 1
            return False, f"Đơn của bạn bị từ chối. Vui lòng thử lại sau {days_left} ngày."

    return True, ""


def create_teacher_application(
    user_id,
    workplace,
    degree,
    major,
    bio,
    expertise,
    experience,
    teach_style,
    linkedin,
    website,
    id_card_file=None,
    degree_file=None,
    cv_file=None,
    extra_cert_file=None,
    video_file=None,
):
    ok, message = can_apply_teacher(user_id)
    if not ok:
        return None, message

    application = TeacherApplication(
        user_id=user_id,
        workplace=workplace,
        degree=degree,
        major=major,
        bio=bio,
        expertise=expertise,
        experience=experience,
        teach_style=teach_style,
        linkedin=linkedin,
        website=website,
        id_card_file=id_card_file,
        degree_file=degree_file,
        cv_file=cv_file,
        extra_cert_file=extra_cert_file,
        video_file=video_file,
        status=ApplicationStatus.PENDING,
    )
    try:
        db.session.add(application)
        db.session.commit()
        return application, None
    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng thử lại sau!"


def get_latest_teacher_application(user_id):
    return TeacherApplication.query.filter_by(user_id=user_id).order_by(TeacherApplication.created_date.desc()).first()
