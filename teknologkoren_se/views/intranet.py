import datetime
import random
import string
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from teknologkoren_se import app, images, forms
from teknologkoren_se.views.auth import verify_email
from teknologkoren_se.models import User, Tag, Post, Event
from teknologkoren_se.util import tag_required

mod = Blueprint('intranet', __name__, subdomain='intranet')

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

    return render_template('intranet/profile.html',
                           user=user,
                           tags=tags,
                           edit=edit)


@mod.route('/profile/edit/', methods=['GET', 'POST'])
def edit_user():
    """Edit (own) profile.

    Redirects to admin-edit if user is webmaster, redirects to viewing
    profile if not own profile. Allows editing of email, phone number,
    and password. Edit of email has to be confirmed by clicking a link
    sent to the new email address.
    """
    form = forms.EditUserForm(current_user, request.form)

    if form.validate_on_submit():
        if form.email.data != current_user.email:
            verify_email(current_user, form.email.data)
            flash("Please check {} for a verification link."
                  .format(form.email.data), 'info')

        current_user.phone = form.phone.data

        current_user.save()

        return redirect(url_for('.profile', id=current_user.id))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit_user.html',
                           user=current_user,
                           form=form,
                           full_form=False)


@mod.route('/profile/edit/<int:id>/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def full_edit_user(id):
    """Edit all user attributes.

    Allows for editing of all user attributes, including name and tags.
    Tags are in an encapsulated form generated dynamically in this view.
    """
    user = get_object_or_404(User, User.id == id)

    tags = Tag.select().order_by(Tag.name)
    form = forms.TagForm.extend_form(forms.FullEditUserForm, tags, user)

    form = form(user)

    if form.validate_on_submit():
        if form.email.data != user.email:
            verify_email(user, form.email.data)
            flash("A verification link has been sent to {}"
                  .format(form.email.data), 'info')

        user.phone = form.phone.data

        user.first_name = form.first_name.data
        user.last_name = form.last_name.data

        form.set_user_tags()

        user.save()

        return redirect(url_for('.profile', id=id))
    else:
        forms.flash_errors(form)

    return render_template('intranet/full_edit_user.html',
                           user=user,
                           form=form,
                           full_form=True)


@mod.route('/profile/edit/password/', methods=['GET', 'POST'])
def change_password():
    """Change current users password."""
    form = forms.ChangePasswordForm(current_user)
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        current_user.save()
        flash('Your password has been changed!', 'success')
        return redirect(url_for('.my_profile'))
    else:
        forms.flash_errors(form)

    return render_template('intranet/change_password.html', form=form)


@mod.route('/adduser/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def adduser():
    """Add a user."""
    form = forms.AddUserForm()
    if form.validate_on_submit():
        password = ''.join(random.choice(string.ascii_letters + string.digits)
                           for _ in range(30))

        user = User.create(email=form.email.data,
                           first_name=form.first_name.data,
                           last_name=form.last_name.data,
                           phone=form.phone.data,
                           password=password)

        form = forms.AddUserForm()

        flash("User {} added!".format(user.email), 'success')

        return redirect(url_for('.adduser'))

    else:
        if form.errors:
            flash(form.errors, 'error')

    return render_template('intranet/adduser.html', form=form)


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


@mod.route('/admin/')
@tag_required('Webmaster')
def admin():
    """Show administration page."""
    return render_template('intranet/admin.html')


@mod.route('/view-posts/')
@tag_required('Webmaster')
def view_posts():
    """Show links to all post's edit mode."""
    posts = Post.select().order_by(Post.timestamp.desc())

    return render_template('intranet/view-posts.html', posts=posts)


@mod.route('/view-events/')
@tag_required('Webmaster')
def view_events():
    """Show links to all event's edit mode."""
    events = Event.select().order_by(Event.timestamp.desc())

    return render_template('intranet/view-events.html', events=events)


@mod.route('/new-post/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def new_post():
    """Create a new post."""
    form = forms.EditPostForm(CombinedMultiDict((request.form, request.files)))
    if form.validate_on_submit():
        if form.upload.data:
            image = images.save(form.upload.data)
        else:
            image = None

        post = Post.create(
            title=form.title.data,
            path=url_for('.index'),
            content=form.content.data,
            published=form.published.data,
            timestamp=datetime.datetime.now(),
            author=current_user.id,
            image=image
            )
        return redirect(url_for('blog.view_post',
                                post_id=post.id,
                                slug=post.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-post.html', form=form, post=None)


@mod.route('/edit-post/<int:post_id>/', methods=['GET', 'POST'])
@mod.route('/edit-post/<int:post_id>/<slug>/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def edit_post(post_id, slug=None):
    """Edit an existing post."""
    post = get_object_or_404(Post, Post.id == post_id)

    if slug != post.slug:
        return redirect(url_for('.edit_post', post_id=post.id, slug=post.slug))

    form = forms.EditPostForm(CombinedMultiDict((request.form, request.files)),
                              obj=post)

    if form.validate_on_submit():
        if form.upload.data:
            post.image = images.save(form.upload.data)
        post.title = form.title.data
        post.content = form.content.data
        post.published = form.published.data
        post.save()
        return redirect(url_for('blog.view_post',
                                post_id=post.id,
                                slug=post.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-post.html', form=form, post=post)


@mod.route('/remove-post/<int:post_id>/')
@mod.route('/remove-post/<int:post_id>/<slug>/')
@tag_required('Webmaster')
def remove_post(post_id, slug=None):
    """Remove a post."""
    post = get_object_or_404(Post, Post.id == post_id)
    post.delete_instance()
    return redirect(url_for('.view_posts'))


@mod.route('/new-event/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def new_event():
    """Create a new event."""
    form = forms.EditEventForm(
        CombinedMultiDict((request.form, request.files))
        )
    if form.validate_on_submit():
        if form.upload.data:
            image = images.save(form.upload.data)
        else:
            image = None

        event = Event.create(
            title=form.title.data,
            path='/konserter/',
            content=form.content.data,
            published=form.published.data,
            start_time=form.start_time.data,
            location=form.location.data,
            timestamp=datetime.now(),
            author=current_user.id,
            image=image
            )
        return redirect(url_for('events.view_event',
                                event_id=event.id,
                                slug=event.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-event.html', form=form)


@mod.route('/edit-event/<int:event_id>/', methods=['GET', 'POST'])
@mod.route('/edit-event/<int:event_id>/<slug>/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def edit_event(event_id, slug=None):
    """Edit an existing event."""
    event = get_object_or_404(Event, Event.id == event_id)

    if slug != event.slug:
        return redirect(url_for('.edit_event',
                                event_id=event.id,
                                slug=event.slug))

    form = forms.EditEventForm(
        CombinedMultiDict((request.form, request.files)),
        obj=event
        )

    if form.validate_on_submit():
        event.title = form.title.data
        event.content = form.content.data
        event.published = form.published.data
        event.start_time = form.start_time.data
        event.location = form.location.data
        if form.upload.data:
            event.image = images.save(form.upload.data)
        event.save()
        return redirect(url_for('events.view_event',
                                event_id=event.id,
                                slug=event.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-event.html', form=form)


@mod.route('/remove-event/<int:event_id>/')
@mod.route('/remove-event/<int:event_id>/<slug>/')
@tag_required('Webmaster')
def remove_event(event_id, slug=None):
    """Remove an event."""
    event = get_object_or_404(Event, Event.id == event_id)
    event.delete_instance()
    return redirect(url_for('.view-events'))
