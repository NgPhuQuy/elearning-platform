from functools import wraps
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from flask import redirect, request, session, url_for
from flask_login import current_user


def anonymous_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if getattr(current_user, "is_authenticated", False):
            return redirect("/")
        return func(*args, **kwargs)

    return wrapper


def _add_login_param(url):
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query))
    query["login"] = "1"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "is_authenticated", False):
            same_host_referrer = None
            if request.referrer and urlsplit(request.referrer).netloc == urlsplit(request.url).netloc:
                same_host_referrer = request.referrer

            session["next_url"] = same_host_referrer or url_for("index")

            if same_host_referrer:
                return redirect(_add_login_param(same_host_referrer))
            return redirect(url_for("index", login=1))
        return func(*args, **kwargs)

    return wrapper


def teacher_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "is_authenticated", False) or not getattr(current_user, "teacher_profile", None):
            return redirect("/")
        return func(*args, **kwargs)

    return wrapper

