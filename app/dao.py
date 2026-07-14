import hashlib

from flask_login import current_user

from app.models import User
from app import db, login

@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def register_user(username, password, email,
                  phone, avatar, first_name, last_name):
    hashed_password = hash_password(password)
    user = User(username=username, password=hashed_password, email=email,phone=phone,
                avatar=avatar, first_name=first_name, last_name=last_name)
    db.session.add(user)
    db.session.commit()
    return user

def is_username_exist(username):
    return User.query.filter(User.username == username).first()


def is_email_used(email):
    return User.query.filter(User.email == email).first()


def is_phone_used(phone):
    return User.query.filter(User.phone == phone).first()

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def change_info(email, phone, file_path, first_name, last_name):
    if email != current_user.email:

        if is_email_used(email):
            return False, "Email đã được sử dụng bởi tài khoản khác."

    current_user.email = email
    current_user.phone = phone
    current_user.avatar = file_path
    current_user.first_name = first_name
    current_user.last_name = last_name
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    return True, None


def change_password(new_password):
    current_user.password = hash_password(new_password)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return False, str(e)
    return True, None