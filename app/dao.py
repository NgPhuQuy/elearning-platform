import hashlib

from app.models import User
from app import db, login

@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def auth_user(username, password):
    password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()

def register_user(username, password, email,
                  phone, avatar, first_name, last_name):
    user = User(username=username, password=password, email=email,phone=phone,
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