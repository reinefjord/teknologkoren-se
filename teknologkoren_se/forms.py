from flask import url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (StringField, PasswordField, BooleanField,
                     HiddenField, DateTimeField, FileField)
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import (Email, InputRequired, Regexp, Optional,
                                ValidationError)
from teknologkoren_se import images
from .models import User
from .util import is_safe_url, get_redirect_target


class Unique:
    """Validate that field is unique in model."""
    def __init__(self, model, field, message='This element already exists.'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if self.model.select().where(self.field == field.data).exists():
            raise ValidationError(self.message)


class Exists:
    """Validate that field is unique in model."""
    def __init__(self, model, field, message='This element does not exist.'):
        self.model = model
        self.field = field
        self.message = message

    def __call__(self, form, field):
        if not(self.model.select().where(self.field == field.data).exists()):
            raise ValidationError(self.message)


class RedirectForm(FlaskForm):
    next = HiddenField()

    def __init__(self, *args, **kwargs):
        FlaskForm.__init__(self, *args, **kwargs)
        if not self.next.data:
            self.next.data = get_redirect_target() or ''

    def redirect(self, endpoint='index', **values):
        if is_safe_url(self.next.data):
            return redirect(self.next.data)
        target = get_redirect_target()
        return redirect(target or url_for(endpoint, **values))


class EmailForm(FlaskForm):
    email = EmailField('Email', validators=[InputRequired(), Email()])


class ExistingEmailForm(FlaskForm):
    email = EmailField('Email', validators=[
        InputRequired(),
        Email(),
        Exists(
            User,
            User.email,
            message='Unknown email')])


class PasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[InputRequired()])


class LoginForm(RedirectForm, EmailForm, PasswordForm):
    """Get login details."""
    remember = BooleanField('Remember me')

    def __init__(self, *args, **kwargs):
        self.user = None
        super().__init__(*args, **kwargs)

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        user = User.authenticate(self.email.data, self.password.data)
        if not user:
            return False

        self.user = user
        return True


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
