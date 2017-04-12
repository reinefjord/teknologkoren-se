import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_required
from werkzeug.datastructures import CombinedMultiDict
from wtforms.fields import FormField
from flask_wtf import FlaskForm
from teknologkoren_se import app, db, images, forms
from teknologkoren_se.views.auth import verify_email
from teknologkoren_se.models import User, Tag, Post, Event
from teknologkoren_se.util import tag_required

mod = Blueprint('intranet', __name__)

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


@mod.route('/member/<int:id>/')
def member(id):
    """Show member of user with matching id."""
    user = User.query.get_or_404(id)
    tags = user.active_tags

    return render_template('intranet/member.html',
                           user=user,
                           tags=tags)


@mod.route('/member/edit/', methods=['GET', 'POST'])
def edit_user():
    """Edit (own) member.

    Redirects to admin-edit if user is webmaster, redirects to viewing
    member if not own member. Allows editing of email, phone number,
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

        db.session.commit()

        return redirect(url_for('.member', id=current_user.id))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit_user.html',
                           user=current_user,
                           form=form)


@mod.route('/admin/edit-user/<int:id>/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def full_edit_user(id):
    """Edit all user attributes.

    Allows for editing of all user attributes, including name and tags.
    Tags are in an encapsulated form generated dynamically in this view.
    """
    user = User.query.get_or_404(id)

    tags = Tag.query.order_by(Tag.name).all()
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

        db.session.commit()

        return redirect(url_for('.member', id=id))
    else:
        forms.flash_errors(form)

    return render_template('intranet/full_edit_user.html',
                           user=user,
                           form=form)


@mod.route('/member/edit/password/', methods=['GET', 'POST'])
def change_password():
    """Change current users password."""
    form = forms.ChangePasswordForm(current_user)
    if form.validate_on_submit():
        current_user.password = form.new_password.data
        db.session.commit()
        flash('Your password has been changed!', 'success')
        return redirect(url_for('.member', id=current_user.id))
    else:
        forms.flash_errors(form)

    return render_template('intranet/change_password.html', form=form)


@mod.route('/adduser/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def adduser():
    """Add a user."""
    tags = Tag.query.order_by(Tag.name).all()
    Form = forms.TagForm.extend_form(forms.AddUserForm, tags)

    form = Form()

    if form.validate_on_submit():
        user = User(email=form.email.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    phone=form.phone.data)

        forms.TagForm.set_user_tags(form, user)

        db.session.commit()

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
    tag_dict = {'All': User.query.order_by(User.first_name)}
    tag_list = ['All']

    return render_template(
        'intranet/members.html',
        tag_list=tag_list,
        tag_dict=tag_dict)


@mod.route('/members/<list:tag_list>/')
def members_by_tags(tag_list):
    """Show active members sorted by the tags in tag_list."""
    active_users = User.query.filter(User.has_tag('Aktiv'))

    tag_dict = {}
    for tag in tag_list:
        tag_dict[tag] = active_users.filter(User.has_tag(tag)
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
            tag_dict[column][row] = User.query.filter(
                    User.has_tag(column),
                    User.has_tag(row))

    return render_template('intranet/member_matrix.html',
                           columns=columns,
                           rows=rows,
                           tag_dict=tag_dict)


@mod.route('/members/filter/', methods=['GET', 'POST'])
def filter_members():
    class F(FlaskForm):
        pass

    TagColForm = forms.TagForm.tag_form(Tag.query.all())
    TagRowForm = forms.TagForm.tag_form(Tag.query.all())

    F.col_form = FormField(TagColForm)
    F.row_form = FormField(TagRowForm)

    form = F()

    if form.validate_on_submit():
        if form.row_form.checked_tags():
            return redirect(url_for('.member_matrix',
                                    columns=form.col_form.checked_tags(),
                                    rows=form.row_form.checked_tags()))
        else:
            return redirect(url_for('.members_by_tags',
                                    tag_list=form.col_form.checked_tags()))

    return render_template('intranet/filter_members.html',
                           form=form)


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
@tag_required('Webmaster', 'PRoletär')
def admin():
    """Show administration page."""
    return render_template('intranet/admin.html')


@mod.route('/view-posts/')
@tag_required('Webmaster', 'PRoletär')
def view_posts():
    """Show links to all post's edit mode."""
    posts = Post.query.filter_by(type='post').order_by(Post.timestamp.desc())

    return render_template('intranet/view-posts.html', posts=posts)


@mod.route('/view-events/')
@tag_required('Webmaster', 'PRoletär')
def view_events():
    """Show links to all event's edit mode."""
    events = Event.query.order_by(Event.timestamp.desc())

    return render_template('intranet/view-events.html', events=events)


@mod.route('/new-post/', methods=['GET', 'POST'])
@tag_required('Webmaster', 'PRoletär')
def new_post():
    """Create a new post."""
    form = forms.EditPostForm(CombinedMultiDict((request.form, request.files)))
    if form.validate_on_submit():
        if form.upload.data:
            image = images.save(form.upload.data)
        else:
            image = None

        post = Post(
            title=form.title.data,
            content=form.content.data,
            published=form.published.data,
            timestamp=datetime.datetime.now(),
            author=current_user,
            image=image
            )
        db.session.add(post)
        db.session.commit()

        return redirect(url_for('blog.view_post',
                                post_id=post.id,
                                slug=post.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-post.html', form=form, post=None)


@mod.route('/edit-post/<int:post_id>/', methods=['GET', 'POST'])
@mod.route('/edit-post/<int:post_id>/<slug>/', methods=['GET', 'POST'])
@tag_required('Webmaster', 'PRoletär')
def edit_post(post_id, slug=None):
    """Edit an existing post."""
    post = Post.query.get_or_404(post_id)

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
        db.session.commit()
        return redirect(url_for('blog.view_post', post_id=post.id, slug=post.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-post.html', form=form, post=post)


@mod.route('/remove-post/<int:post_id>/')
@mod.route('/remove-post/<int:post_id>/<slug>/')
@tag_required('Webmaster', 'PRoletär')
def remove_post(post_id, slug=None):
    """Remove a post."""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('.view_posts'))


@mod.route('/new-event/', methods=['GET', 'POST'])
@tag_required('Webmaster', 'PRoletär')
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

        event = Event(
            title=form.title.data,
            content=form.content.data,
            published=form.published.data,
            start_time=form.start_time.data,
            location=form.location.data,
            timestamp=datetime.datetime.now(),
            author=current_user,
            image=image
            )
        db.session.add(event)
        db.session.commit()

        return redirect(url_for('events.view_event',
                                event_id=event.id,
                                slug=event.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-event.html', form=form)


@mod.route('/edit-event/<int:event_id>/', methods=['GET', 'POST'])
@mod.route('/edit-event/<int:event_id>/<slug>/', methods=['GET', 'POST'])
@tag_required('Webmaster', 'PRoletär')
def edit_event(event_id, slug=None):
    """Edit an existing event."""
    event = Event.query.get_or_404(event_id)

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
        db.session.commit()
        return redirect(url_for('events.view_event',
                                event_id=event.id,
                                slug=event.slug))
    else:
        forms.flash_errors(form)

    return render_template('intranet/edit-event.html', form=form, event=event)


@mod.route('/remove-event/<int:event_id>/')
@mod.route('/remove-event/<int:event_id>/<slug>/')
@tag_required('Webmaster', 'PRoletär')
def remove_event(event_id, slug=None):
    """Remove an event."""
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return redirect(url_for('.view-events'))
