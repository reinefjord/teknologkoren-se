from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
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

    return render_template('intranet/profile.html', user=user, tags=tags)


@mod.route('/profile/<int:id>/edit/', methods=['GET', 'POST'])
def edit_profile(id):
    if current_user.id != id:
        return redirect(url_for('.profile', id=id))

    return render_template('intranet/edit_profile.html')


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
