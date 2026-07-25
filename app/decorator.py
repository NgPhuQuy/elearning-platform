from functools import wraps

from flask import redirect
from flask_login import current_user


def teacher_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect('/login')

        if not current_user.teacher_profile:
            return redirect('/')

        return func(*args, **kwargs)

    return wrapper
