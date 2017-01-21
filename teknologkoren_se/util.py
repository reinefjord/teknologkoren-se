from functools import wraps
from urllib.parse import urlparse, urljoin
from flask import flash, url_for, request, redirect
from flask_login import current_user
from itsdangerous import URLSafeTimedSerializer
from teknologkoren_se import app

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])


def send_email(address, body):
    # TODO: make send_email send emails
    print(body)


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def get_redirect_target(fallback='.index'):
    for target in (request.values.get('next'), request.referrer,
                   url_for(fallback)):
        if not target:
            continue
        if is_safe_url(target):
            return target


def tag_required(tag):
    def decorator(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            if tag not in current_user.tag_names:
                flash("You need to be {} to access that.".format(tag), 'error')
                return redirect(get_redirect_target())
            return func(*args, **kwargs)
        return decorated_function
    return decorator
