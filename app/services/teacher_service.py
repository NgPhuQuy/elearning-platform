import uuid

from app import dao
from app.services.upload_service import upload_file


def submit_teacher_application(user_id, form_data, files):
    ok, message = dao.can_apply_teacher(user_id)
    if not ok:
        return None, message

    file_fields = {
        "id_card_file": True,
        "degree_file": True,
        "cv_file": True,
        "extra_cert_file": False,
        "video_file": False,
    }
    uploaded = {}
    for field, required in file_fields.items():
        f = files.get(field)
        if f and getattr(f, "filename", None):
            url, err = upload_file(
                f,
                folder="elearning-platform/teacher-registrations",
                public_id=f"{field}_{uuid.uuid4().hex[:8]}",
            )
            if err or not url:
                return None, "Tải file thất bại, vui lòng thử lại!"
            uploaded[field] = url
        elif required:
            return None, "Vui lòng tải đầy đủ tài liệu bắt buộc!"

    return dao.create_teacher_application(
        user_id=user_id,
        workplace=form_data.get("workplace"),
        degree=form_data.get("degree"),
        major=form_data.get("major"),
        bio=form_data.get("bio"),
        expertise=",".join(form_data.getlist("expertise")),
        experience=form_data.get("experience"),
        teach_style=form_data.get("teach_style"),
        linkedin=form_data.get("linkedin"),
        website=form_data.get("website"),
        **uploaded,
    )


def get_latest_application(user_id):
    return dao.get_latest_teacher_application(user_id)

