import random
from string import ascii_letters, digits
from flask import Blueprint, render_template, redirect, url_for, request, flash
from playhouse.flask_utils import get_object_or_404
from wtforms import BooleanField, FormField
from teknologkoren_se.views.public.users import verify_email
from teknologkoren_se.forms import FullEditUserForm, FlaskForm, AddUserForm
from teknologkoren_se.models import User, Tag, UserTag
from teknologkoren_se.util import tag_required


mod = Blueprint('administration', __name__, url_prefix='/intranet/admin')


@mod.route('/')
@tag_required('Webmaster')
def admin():
    """Show administration page."""
    return render_template('intranet/admin.html')


@mod.route('/adduser/', methods=['GET', 'POST'])
def adduser():
    """Add a user."""
    form = AddUserForm(request.form)
    if form.validate_on_submit():
        password = ''.join(
                random.choice(ascii_letters + digits) for _ in range(30))

        User.create(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone=form.phone.data,
                password=password,
                )

        return redirect('intranet.index')

    return render_template('users/adduser.html', form=form)


def full_edit_user(id):
    """Edit all user attributes.

    Allows for editing of all user attributes, including name and tags.
    Tags are in an encapsulated form generated dynamically in this view.
    """
    user = get_object_or_404(User, User.id == id)

    # Class to become tag form
    class F(FlaskForm):
        pass

    for tag in Tag.select().order_by(Tag.name):
        # If a user has this tag, set its value to checked
        if tag.name in user.tag_names:
            field = BooleanField(tag.name, default=True)
        else:
            field = BooleanField(tag.name)

        # Add the field to class F with the name of the tag
        setattr(F, tag.name, field)

    # Add the tag form to the main form
    setattr(FullEditUserForm, 'tags', FormField(F))

    form = FullEditUserForm(user, request.form)

    if form.validate_on_submit():
        if form.email.data != user.email:
            verify_email(user, form.email.data)
            flash("A verification link has been sent to {}"
                  .format(form.email.data), 'info')

        user.phone = form.phone.data

        if form.password.data:
            user.password = form.password.data

        user.first_name = form.first_name.data
        user.last_name = form.last_name.data

        tag_form = form.tags
        for tag in Tag.select():
            tag_field = getattr(tag_form, tag.name)

            # If tag field is checked and the user did not already
            # have that tag, give user tag
            if tag_field.data and tag.name not in user.tag_names:
                UserTag.create(user=user, tag=tag)

            # If tag field isn't checked but the user has that tag,
            # remove it.
            elif not tag_field.data and tag.name in user.tag_names:
                user_tag = UserTag.get((UserTag.user == user) &
                                       (UserTag.tag == tag))
                user_tag.delete_instance()

        user.save()

        return redirect(url_for('.profile', id=id))

    return render_template('intranet/full_edit_user.html',
                           user=user,
                           form=form,
                           full_form=True)
