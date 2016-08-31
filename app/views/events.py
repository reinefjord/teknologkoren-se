import datetime
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from app import login_manager
from app.forms import EditEventForm
from app.models import Event


mod = Blueprint('events', __name__, url_prefix='/konserter')


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def overview(page):
    if current_user.is_authenticated:
        events = Event.select()
    else:
        events = Event.select().where(Event.published == True)

    events = events.order_by(Event.start_time.desc())

    pagination = events.paginate(page, 5)

    if not pagination and events:
        last_page = (len(events) // 5) + 1
        return redirect(url_for('.konserter', page=last_page))

    has_next = True if events.paginate(page+1, 5) else False

    return render_template('events/overview.html',
                           pagination=pagination,
                           page=page,
                           has_next=has_next)


@mod.route('/new-event/', methods=['GET', 'POST'])
@login_required
def new_event():
    form = EditEventForm(request.form)
    if form.validate_on_submit():
        event = Event.create(title=form.title.data,
                             content=form.content.data,
                             published=form.published.data,
                             start_time=form.start_time.data,
                             location=form.location.data,
                             timestamp=datetime.datetime.now(),
                             author=current_user.id)
        return redirect(url_for('.view_event', slug=event.slug))

    return render_template('events/edit-event.html', form=form)


@mod.route('/<slug>/')
def view_event(slug):
    event = get_object_or_404(Event, Event.slug == slug)

    if not event.published and not current_user.is_authenticated:
        return login_manager.unauthorized()

    return render_template('events/view-event.html', event=event)


@mod.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit_event(slug):
    event = get_object_or_404(Event, Event.slug == slug)
    form = EditEventForm(request.form, event)

    if form.validate_on_submit():
        event.title = form.title.data
        event.content = form.content.data
        event.published = form.published.data
        event.start_time = form.start_time.data
        event.location = form.location.data
        event.save()
        return redirect(url_for('.view_event', slug=event.slug))

    return render_template('events/edit-event.html', form=form)


@mod.route('/<slug>/remove/')
@login_required
def remove_event(slug):
    event = get_object_or_404(Event, Event.slug == slug)
    event.delete_instance()
    return redirect(url_for('.overview'))
