from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from app.forms import EditUserForm, FullEditUserForm
from app.models import User, Tag, UserTag

mod = Blueprint('intranet', __name__, url_prefix='/intranet')


@mod.before_request
@login_required
def before_request():
    pass


@mod.route('/')
def index():
    return render_template('intranet/intranet.html')


@mod.route('/profile/')
def my_profile():
    return redirect(url_for('.profile', id=current_user.id))


@mod.route('/profile/<int:id>/')
def profile(id):
    user = get_object_or_404(User, User.id == id)
    tags = (Tag
            .select()
            .join(UserTag)
            .where(UserTag.user == user))

    if current_user.id == id or 'Webmaster' in current_user.tags:
        edit = True
    else:
        edit = False

    return render_template(
            'intranet/profile.html',
            user=user,
            tags=tags,
            edit=edit)


@mod.route('/profile/<int:id>/edit/', methods=['GET', 'POST'])
def edit_user(id):
    if 'Webmaster' in current_user.tags:
        user = get_object_or_404(User, User.id == id)
        form = FullEditUserForm(user, request.form, user)
        full_form = True

    elif current_user.id != id:
        return redirect(url_for('.profile', id=id))

    else:
        user = current_user
        form = EditUserForm(user, request.form, user)
        full_form = False

    if form.validate_on_submit():
        user.email = form.email.data
        user.phone = form.phone.data

        if form.password.data:
            user.password = form.password.data

        if full_form:
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.active = form.active.data

        user.save()

        return redirect(url_for('.profile', id=id))

    return render_template('intranet/edit_user.html',
                           user=current_user,
                           form=form,
                           full_form=full_form)


@mod.route('/members/')
def members():
    users = User.select().where(User.active == True)
    voices = {}
    voice_tags = ['Sopran 1', 'Sopran 2', 'Alt 1', 'Alt 2', 'Tenor 1',
                  'Tenor 2', 'Bas 1', 'Bas 2']
    for voice in voice_tags:
        voices[voice] = (users
                         .join(UserTag)
                         .join(Tag)
                         .where(Tag.name == voice))

    return(render_template(
        'intranet/members.html',
        voices=voices,
        voice_tags=voice_tags))
