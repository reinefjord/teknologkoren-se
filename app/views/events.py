from datetime import datetime, timedelta
from flask import abort, Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from app import app, images
from app.forms import EditEventForm
from app.models import Event, File, EventFile


mod = Blueprint('events', __name__, url_prefix='/konserter')


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url


def overview(template, events, page):
    if not current_user.is_authenticated:
        events = events.where(Event.published == True)

    pagination = events.paginate(page, 5)

    if not pagination and events:
        last_page = (len(events) // 5) + 1
        if len(events) % 5:
            last_page += 1
        return redirect(url_for('.konserter', page=last_page))

    has_next = True if events.paginate(page+1, 5) else False

    return render_template(template,
                           pagination=pagination,
                           page=page,
                           has_next=has_next)


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def coming(page):
    old = datetime.now() - timedelta(hours=3)
    events = Event.select(
            ).where(Event.start_time > old).order_by(Event.start_time.desc())
    return overview('events/coming.html', events, page)


@mod.route('/arkiv/', defaults={'page': 1})
@mod.route('/arkiv/page/<int:page>/')
def archive(page):
    old = datetime.now() - timedelta(hours=3)
    events = Event.select(
            ).where(Event.start_time < old).order_by(Event.start_time.desc())
    has_next = True if events.paginate(page+1, 5) else False

    return overview('events/archive.html', events, page)


@mod.route('/new-event/', methods=['GET', 'POST'])
@login_required
def new_event():
    form = EditEventForm(CombinedMultiDict((request.form, request.files)))

    if form.validate_on_submit():
        event = Event.create(
                title=form.title.data,
                content=form.content.data,
                published=form.published.data,
                start_time=form.start_time.data,
                location=form.location.data,
                timestamp=datetime.now(),
                author=current_user.id,
                )

        for field in form.upload.entries:
            if field.has_file():
                image_name = images.save(field.data)
                file = File.create(name=image_name)
                EventFile.create(event=event, file=file)

        return redirect(url_for('.view_event',
                                event_id=event.id,
                                slug=event.slug))

    return render_template('events/edit-event.html', form=form)


@mod.route('/<int:event_id>/')
@mod.route('/<int:event_id>/<slug>/')
def view_event(event_id, slug=None):
    event = get_object_or_404(Event, Event.id == event_id)

    if not event.published and not current_user.is_authenticated:
        return abort(404)

    if slug != event.slug:
        return redirect(url_for(
            '.view_event',
            event_id=event.id,
            slug=event.slug))

    return render_template('events/view-event.html', event=event)


@mod.route('/edit/<int:event_id>/', methods=['GET', 'POST'])
@mod.route('/edit/<int:event_id>/<slug>/', methods=['GET', 'POST'])
@login_required
def edit_event(event_id, slug=None):
    event = get_object_or_404(Event, Event.id == event_id)

    if slug != event.slug:
        return redirect(url_for('.edit_event',
                        event_id=event.id,
                        slug=event.slug))

    form = EditEventForm(
            CombinedMultiDict((request.form, request.files)),
            event
            )

    if form.validate_on_submit():
        event.title = form.title.data
        event.content = form.content.data
        event.published = form.published.data
        event.start_time = form.start_time.data
        event.location = form.location.data
        event.save()

        for field in form.upload.entries:
            if field.has_file():
                image_name = images.save(field.data)
                file = File.create(name=image_name)
                EventFile.create(event=event, file=file)

        return redirect(url_for('.view_event',
                                event_id=event.id,
                                slug=event.slug))

    return render_template('events/edit-event.html', form=form)


@mod.route('/remove/<int:event_id>/')
@mod.route('/remove/<int:event_id>/<slug>/')
@login_required
def remove_event(event_id, slug=None):
    event = get_object_or_404(Event, Event.id == event_id)
    event.delete_instance()
    return redirect(url_for('.coming'))
