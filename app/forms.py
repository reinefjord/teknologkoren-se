from urllib.parse import urlparse, urljoin
from flask import request, url_for, redirect
from flask.ext.wtf import Form
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     HiddenField)
from wtforms.validators import Email, InputRequired
from peewee import DoesNotExist
from .models import User


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.args.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


class RedirectForm(Form):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))


class LoginForm(RedirectForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

    def validate(self):
        if not Form.validate(self):
            return False

        try:
            self.user = User.get(email=self.email.data)
        except DoesNotExist:
            self.email.errors.append("Unknown email")
            return False

        if not self.user.verify_password(self.password.data):
            self.password.errors.append("Invalid password")
            return False

        return True


class RegisterForm(RedirectForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Submit')

    def validate(self):
        if not Form.validate(self):
            return False

        try:
            User.get(email=self.email.data)
        except DoesNotExist:
            return True

        self.email.errors.append("This email is already in use")
        return False


class CreatePostForm(Form):
    content = HiddenField(validators=[InputRequired()])
    submit = SubmitField('Submit')
    title = StringField('Title', validators=[InputRequired()])
    published = BooleanField('Publish')


class CreatePageForm(Form):
    name = StringField('Page name', validators=[InputRequired()])
    is_blog = BooleanField('Blog page')
    published = BooleanField('Publish')
    submit = SubmitField('Create')
