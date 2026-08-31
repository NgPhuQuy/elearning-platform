import hashlib

from flask_login import current_user

from app import db, login
from app.models import User


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def is_username_exist(username):
    return User.query.filter_by(username=username).first() is not None


def is_email_used(email):
    return User.query.filter_by(email=email).first() is not None


def is_phone_used(phone):
    return User.query.filter_by(phone=phone).first() is not None


def auth_user(username, password):
    hashed_pwd = hash_password(password)
    return User.query.filter(
        User.username == username,
        User.password == hashed_pwd,
    ).first()


def register_user(username, password, email, phone, avatar, first_name, last_name):
    user = User(
        username=username,
        password=hash_password(password),
        email=email,
        phone=phone,
        avatar=avatar,
        first_name=first_name,
        last_name=last_name,
    )
    db.session.add(user)
    db.session.commit()
    return user


def change_info(email, phone, avatar, first_name, last_name):
    try:
        user = current_user
        if email and email != user.email:
            if is_email_used(email):
                return False, "Email đã được sử dụng!"
            user.email = email

        if phone and phone != user.phone:
            if is_phone_used(phone):
                return False, "Số điện thoại đã được sử dụng!"
            user.phone = phone

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if avatar:
            user.avatar = avatar

        db.session.commit()
        return True, None
    except Exception:
        db.session.rollback()
        return False, "Lỗi hệ thống, vui lòng thử lại sau!"


def change_password(new_password):
    try:
        current_user.password = hash_password(new_password)
        db.session.commit()
        return True, None
    except Exception:
        db.session.rollback()
        return False, "Lỗi hệ thống, vui lòng thử lại sau!"


def search_users(keyword, current_user_id):
    return (
        User.query.filter(
            User.id != current_user_id,
            (User.username.ilike(f"%{keyword}%"))
            | (User.first_name.ilike(f"%{keyword}%"))
            | (User.last_name.ilike(f"%{keyword}%")),
        )
        .limit(10)
        .all()
    )

