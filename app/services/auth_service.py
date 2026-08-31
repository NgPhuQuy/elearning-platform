from app import dao, db
from app.models import User
from app.services.upload_service import upload_file


def register_user(form_data, files):
    password = form_data.get("password")
    confirm = form_data.get("confirm")
    username = form_data.get("username")
    email = form_data.get("email")
    phone = form_data.get("phone")
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")

    if not all([password, confirm, username, email, phone, first_name, last_name]):
        return None, "Vui lòng nhập đầy đủ thông tin!"

    if password != confirm:
        return None, "Mật khẩu không khớp!"

    if len(password) < 8:
        return None, "Mật khẩu phải từ 8 ký tự trở lên!"

    if dao.is_username_exist(username=username):
        return None, "Username đã tồn tại!"

    if dao.is_email_used(email=email):
        return None, "Email đã được sử dụng!"

    if dao.is_phone_used(phone=phone):
        return None, "Số điện thoại này đã được đăng ký!"

    avatar_file = files.get("avatar")
    avatar_url, upload_err = upload_file(avatar_file, folder="elearning-platform/avatars")
    if upload_err:
        return None, "Tải file thất bại!"

    try:
        user = dao.register_user(username, password, email, phone, avatar_url, first_name, last_name)
        return user, None
    except Exception:
        db.session.rollback()
        return None, "Hệ thống lỗi, vui lòng quay lại sau!"


def auth_user(username, password):
    if not username or not password:
        return None, "Vui lòng nhập đầy đủ tài khoản và mật khẩu!"

    user = dao.auth_user(username=username, password=password)
    if not user:
        return None, "Tài khoản hoặc mật khẩu không đúng!"
    if not user.is_active:
        return None, "Tài khoản của bạn đã bị khóa!"

    return user, None


def auth_admin(username, password):
    if not username or not password:
        return None, "Vui lòng nhập đầy đủ tài khoản và mật khẩu!"

    user = dao.auth_user(username=username, password=password)
    if not user:
        return None, "Tài khoản hoặc mật khẩu không đúng!"
    if not getattr(user, "admin", None):
        return None, "Bạn không có quyền quản trị viên!"

    return user, None


def handle_google_login(userinfo):
    if not userinfo or not userinfo.get("email_verified"):
        return None, "Xác thực Google thất bại!"

    user = User.query.filter_by(google_sub=userinfo["sub"]).first()
    if not user:
        user = User.query.filter_by(email=userinfo["email"]).first()
        if user:
            user.google_sub = userinfo["sub"]
            if not user.avatar and userinfo.get("picture"):
                user.avatar = userinfo["picture"]
        else:
            base_username = userinfo["email"].split("@")[0]
            candidate_username = base_username
            counter = 1
            while dao.is_username_exist(candidate_username):
                candidate_username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                username=candidate_username,
                email=userinfo["email"],
                first_name=userinfo.get("given_name", ""),
                last_name=userinfo.get("family_name", ""),
                avatar=userinfo.get("picture", ""),
                google_sub=userinfo["sub"],
            )
            db.session.add(user)
        db.session.commit()

    return user, None


def update_profile(form_data, files):
    first_name = form_data.get("first_name")
    last_name = form_data.get("last_name")
    email = form_data.get("email")
    phone = form_data.get("phone")

    avatar_file = files.get("avatar")
    avatar_url, upload_err = upload_file(avatar_file, folder="elearning-platform/avatars")
    if upload_err:
        return False, "Tải file thất bại!"

    return dao.change_info(email, phone, avatar_url, first_name, last_name)


def change_password(user, curr_password, new_password, new_confirm):
    if not dao.auth_user(username=user.username, password=curr_password):
        return False, "Sai mật khẩu!"

    if new_password != new_confirm:
        return False, "Mật khẩu không khớp!"

    if len(new_password) < 8:
        return False, "Mật khẩu phải từ 8 ký tự trở lên!"

    return dao.change_password(new_password)
