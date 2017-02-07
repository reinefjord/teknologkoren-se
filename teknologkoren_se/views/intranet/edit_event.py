import datetime
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from teknologkoren_se import images
from teknologkoren_se.forms import EditEventForm
from teknologkoren_se.models import Event
from teknologkoren_se.util import tag_required


mod = Blueprint('edit_event', __name__, url_prefix='/intranet/admin/event')


@mod.route('/')
@tag_required('Webmaster')
def view_events():
    """Show links to all event's edit mode."""
    events = Event.select().order_by(Event.timestamp.desc())

    return render_template('intranet/view-events.html', events=events)


@mod.route('/new/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def new_event():
    """Create a new event."""
    form = EditEventForm(CombinedMultiDict((request.form, request.files)))
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

    return render_template('intranet/edit-event.html', form=form)


@mod.route('/edit/<int:event_id>/', methods=['GET', 'POST'])
@mod.route('/edit/<int:event_id>/<slug>/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def edit_event(event_id, slug=None):
    """Edit an existing event."""
    event = get_object_or_404(Event, Event.id == event_id)

    if slug != event.slug:
        return redirect(url_for('.edit_event',
                        event_id=event.id,
                        slug=event.slug))

    form = EditEventForm(CombinedMultiDict((request.form, request.files)),
                         obj=event)

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

    return render_template('intranet/edit-event.html', form=form)


@mod.route('/remove/<int:event_id>/')
@mod.route('/remove/<int:event_id>/<slug>/')
@tag_required('Webmaster')
def remove_event(event_id, slug=None):
    """Remove an event."""
    event = get_object_or_404(Event, Event.id == event_id)
    event.delete_instance()
    return redirect(url_for('.view-events'))
