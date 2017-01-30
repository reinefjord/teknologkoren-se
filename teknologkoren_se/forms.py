from flask import request, url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (StringField, PasswordField, BooleanField,
                     HiddenField, DateTimeField, FileField)
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import (Email, InputRequired, Regexp, Optional,
                                ValidationError)
from teknologkoren_se import images
from .models import User
from .util import is_safe_url


class Unique:
    def __init__(self, model, field, message='This element already exists.'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if self.model.select().where(self.field == field.data).exists():
            raise ValidationError(self.message)


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    remember = BooleanField('Remember me')

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        try:
            self.user = User.get(email=self.email.data)
        except User.DoesNotExist:
            self.email.errors.append("Unknown email")
            return False

        if not self.user.verify_password(self.password.data):
            self.password.errors.append("Invalid password")
            return False

        return True


class EmailForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])

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


class PasswordResetForm(EmailForm, PasswordForm):
    pass


class AddUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('First Name', validators=[InputRequired()])

    email = EmailField('Email', validators=[
        InputRequired(),
        Email(),
        Unique(
            User,
            User.email,
            message="This email is already in use")])

    phone = TelField('Phone', validators=[Regexp(r'^\+?[0-9]*$')])


class EditUserForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])
    phone = TelField('Phone', validators=[
        InputRequired(),
        Regexp(r'^\+?[0-9]*$')])
    password = PasswordField('Password', validators=[Optional()])

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(obj=user, *args, **kwargs)

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        if User.select().where(User.email == self.email.data).exists():
            if self.email.data != self.user.email:
                self.email.errors.append("This email is already in use")
                return False

        return True


class FullEditUserForm(EditUserForm):
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])


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
