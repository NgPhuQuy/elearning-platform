from functools import wraps

from flask_login import current_user


def socket_auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "is_authenticated", False):
            return None
        return func(*args, **kwargs)

    return wrapper
