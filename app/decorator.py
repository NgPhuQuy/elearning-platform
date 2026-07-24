from functools import wraps

from flask import redirect
from flask_login import current_user


def anonymous_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect('/')
        return func(*args, **kwargs)
    return wrapper


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            #hien thi trang dang nhap todo
            return None
        return func(*args, **kwargs)
    return wrapper


def teacher_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.teacher_profile:
            #thong bao ban ko co quyen teacher todo
            return redirect('/')
        return func(*args, **kwargs)
    return wrapper
