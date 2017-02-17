from functools import partialmethod
from flask import url_for, redirect
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (StringField, PasswordField, BooleanField, HiddenField,
                     DateTimeField, FileField, TextAreaField, FormField)
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import (Email, InputRequired, Regexp, Optional,
                                ValidationError, Length)
from teknologkoren_se import images
from teknologkoren_se.models import User, UserTag
from teknologkoren_se.util import is_safe_url, get_redirect_target


class TagForm:
    """Namespace for tag forms.

    Do not use this as an object, it is only the methods that are
    interesting.

    WTForms does not allow adding fields after initialization, so we
    use a method to extend a form with a FormField that contains the
    tag fields, checked and ready to go.

    We make sure not to setattr the base as this will modify it
    process wide, instead we let a new class inherit from the base.
    """
    @classmethod
    def extend_form(cls, base, tags, user=None):
        """Return an extended form with tag fields and user modifying method.

        Arguments:
            base: the form to extend
            tags: the tags to extend the form with
            user: a user to check tags against (optional)

        If a user is passed, check the fields of the tags that the user
        has, and set set_user_tags as a method with arguments attached.
        Also set user as an attribute of the extended form.
        """
        class ExtendedBase(base):
            pass

        class Tags(FlaskForm):
            pass

        for tag in tags:
            # If user has this tag, set its value to checked
            if user and tag in user.tags:
                field = BooleanField(tag.name, default=True)
            else:
                field = BooleanField(tag.name)

            # Add the field to this class with the name of the tag
            setattr(Tags, tag.name, field)

        Tags.tags = tags
        ExtendedBase.tags = FormField(Tags)

        if user:
            ExtendedBase.user = user
            # Add TagForm.set_user_tags to Tags together with arguments.
            ExtendedBase.set_user_tags = partialmethod(cls.set_user_tags, user)

        return ExtendedBase

    @staticmethod
    def set_user_tags(form, user):
        """Update user with new and removed tags."""
        tag_form = form.tags
        for tag in tag_form.tags:
            tag_field = getattr(tag_form, tag.name)

            # If tag field is checked and the user did not already
            # have that tag, give user tag
            if tag_field.data and tag not in user.tags:
                UserTag.create(user=user, tag=tag)

            # If tag field isn't checked but the user has that tag,
            # remove it.
            elif not tag_field.data and tag in user.tags:
                user_tag = UserTag.get(UserTag.user == user,
                                       UserTag.tag == tag)
                user_tag.delete_instance()


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
        if self.next.data and is_safe_url(self.next.data):
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


class NewPasswordForm(FlaskForm):
    new_password = PasswordField('New password',
                                 validators=[InputRequired(), Length(min=8)])


class ChangePasswordForm(PasswordForm, NewPasswordForm):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def validate(self):
        if not FlaskForm.validate(self):
            return False

        if not self.user.verify_password(self.password.data):
            return False

        return True


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
    content = TextAreaField(validators=[InputRequired()])
    title = StringField('Title', validators=[InputRequired()])
    published = BooleanField('Publish')


class EditEventForm(EditPostForm):
    start_time = DateTimeField(format='%Y-%m-%d %H:%M')
    location = StringField('Location')
