from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from teknologkoren_se import app
from teknologkoren_se.views.public.users import verify_email
from teknologkoren_se.forms import EditUserForm
from teknologkoren_se.models import User, Tag

mod = Blueprint('intranet', __name__, url_prefix='/intranet')

app.jinja_env.add_extension('jinja2.ext.do')


@mod.before_request
@login_required
def before_request():
    """Do nothing, but make sure user is logged in."""
    pass


@mod.route('/')
def index():
    """Show main intra page."""
    return render_template('intranet/intranet.html')


@mod.route('/profile/')
def my_profile():
    """Redirect to profile of logged in user."""
    return redirect(url_for('.profile', id=current_user.id))


@mod.route('/profile/<int:id>/')
def profile(id):
    """Show profile of user with matching id."""
    user = get_object_or_404(User, User.id == id)
    tags = user.tags.order_by(Tag.name)

    if current_user.id == id or 'Webmaster' in current_user.tag_names:
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
    """Edit (own) profile.

    Redirects to admin-edit if user is webmaster, redirects to viewing
    profile if not own profile. Allows editing of email, phone number,
    and password. Edit of email has to be confirmed by clicking a link
    sent to the new email address.
    """
    if 'Webmaster' in current_user.tag_names:
        return full_edit_user(id)

    elif current_user.id != id:
        return redirect(url_for('.profile', id=id))

    form = EditUserForm(current_user, request.form)

    if form.validate_on_submit():
        if form.email.data != current_user.email:
            verify_email(current_user, form.email.data)
            flash("Please check {} for a verification link."
                  .format(form.email.data), 'info')

        current_user.phone = form.phone.data

        if form.password.data:
            current_user.password = form.password.data

        current_user.save()

        return redirect(url_for('.profile', id=id))

    return render_template('intranet/edit_user.html',
                           user=current_user,
                           form=form,
                           full_form=False)


@mod.route('/members/all/')
def all_members():
    """Show all registred members."""
    tag_dict = {'All': User.select().order_by(User.first_name)}
    tag_list = ['All']

    return render_template(
        'intranet/members.html',
        tag_list=tag_list,
        tag_dict=tag_dict)


@mod.route('/members/<list:tag_list>/')
def members_by_tags(tag_list):
    """Show active members sorted by the tags in tag_list."""
    active_users = User.has_tag('Aktiv')

    tag_dict = {}
    for tag in tag_list:
        tag_dict[tag] = (active_users & User.has_tag(tag)
                         ).order_by(User.first_name)

    return render_template(
        'intranet/members.html',
        tag_list=tag_list,
        tag_dict=tag_dict)


@mod.route('/members/<list:columns>/<list:rows>/')
def member_matrix(columns, rows):
    """Show a matrice of members based on their tags."""
    tag_dict = {}
    for column in columns:
        tag_dict[column] = {}
        for row in rows:
            tag_dict[column][row] = (User.has_tag(column) & User.has_tag(row))

    return render_template('intranet/member_matrix.html',
                           columns=columns,
                           rows=rows,
                           tag_dict=tag_dict)


@mod.route('/members/')
def voices():
    """Show members by voice."""
    tag_list = ['Sopran 1', 'Sopran 2', 'Alt 1', 'Alt 2', 'Tenor 1',
                'Tenor 2', 'Bas 1', 'Bas 2']
    return members_by_tags(tag_list)


@mod.route('/members/groups/')
def groups():
    """Show members by group."""
    columns = ['Sånggrupp 1', 'Sånggrupp 2', 'Sånggrupp 3']
    rows = ['Sopran 1', 'Sopran 2', 'Alt 1', 'Alt 2', 'Tenor 1', 'Tenor 2',
            'Bas 1', 'Bas 2']
    return member_matrix(columns, rows)
