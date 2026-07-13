import hashlib

from app.models import User
from app import db, login

@login.user_loader
def load_user(user_id):
    return User.query.get(user_id)

def auth_user(username, password):
    password = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return User.query.filter(User.username.__eq__(username), User.password.__eq__(password)).first()