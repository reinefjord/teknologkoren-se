from urllib.parse import urlparse, urljoin
from flask import request, url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (StringField, PasswordField, SubmitField, BooleanField,
                     HiddenField, DateTimeField)
from wtforms.validators import Email, InputRequired, Length, Regexp, EqualTo
from peewee import DoesNotExist
from app import images
from .models import User


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


class RedirectForm(FlaskForm):
    next = HiddenField()

    def redirect(self, endpoint='index', **values):
        self.next.data = request.args.get('next')
        if self.next.data and is_safe_url(self.next.data):
            return redirect(self.next.data)

        return redirect(url_for(endpoint, **values))


class LoginForm(RedirectForm):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember me')

    def validate(self):
        if not FlaskForm.validate(self):
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


class EmailForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email()])

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        try:
            self.user = User.get(User.email == self.email.data)
        except User.DoesNotExist:
            self.email.errors.append("Unknown email")
            return False

        return True


class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired()])


class AddUserForm(RedirectForm):
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('First Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    phone = StringField('Phone', validators=[Regexp(r'^\+?[0-9]*$')])
    active = BooleanField('Active')

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        try:
            User.get(email=self.email.data)
        except DoesNotExist:
            return True

        self.email.errors.append("This email is already in use")
        return False


class UploadForm(FlaskForm):
    upload = FileField('image', validators=[
        FileAllowed(images, 'Images only!')
        ])


class EditPostForm(UploadForm):
    content = HiddenField(validators=[InputRequired()])
    title = StringField('Title', validators=[InputRequired()])
    published = BooleanField('Publish')


class EditEventForm(EditPostForm):
    start_time = DateTimeField(format='%Y-%m-%d %H:%M')
    location = StringField('Location')
