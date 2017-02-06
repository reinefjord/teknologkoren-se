from datetime import datetime, timedelta
from flask import abort, Blueprint, redirect, render_template, url_for
from flask_login import current_user
from playhouse.flask_utils import get_object_or_404
from teknologkoren_se import app, images
from teknologkoren_se.models import Event
from teknologkoren_se.util import url_for_other_page


mod = Blueprint('events', __name__, url_prefix='/konserter')


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url


def index(template, events, page):
    """Show published events.

    This code is the same for both coming and old events, minimizing
    code duplication. Only events are shown so we can use peewee's
    built in pagination, unlike in blog.index.
    """
    events = events.filter_by(published=True)

    pagination = events.paginate(page, 5, error_out=False)

    # If there are events in the database, but the pagination is empty
    # (too high page number)
    if not pagination and events:
        # Get the last page that contains events and redirect there
        last_page = (len(events) // 5) + 1
        if len(events) % 5:
            last_page += 1
        return redirect(url_for('.konserter', page=last_page))

    # True if next page has content, else False
    has_next = True if events.paginate(page+1, 5, error_out=False) else False

    return render_template(template,
                           pagination=pagination,
                           page=page,
                           has_next=has_next)


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def coming(page):
    """Show upcoming events.

    An event is still considered 'coming' if it is less than 3 hours
    after start time, allowing people to see that there is an ongoing
    event.
    """
    old = datetime.now() - timedelta(hours=3)
    events = (Event.query.filter(Event.start_time > old)
              .order_by(Event.start_time.desc()))
    return index('events/coming.html', events, page)


@mod.route('/arkiv/', defaults={'page': 1})
@mod.route('/arkiv/page/<int:page>/')
def archive(page):
    """Show old (archived) events.

    And event is considered archived if there has been more than
    3 hours since the start time of the event.
    """
    old = datetime.now() - timedelta(hours=3)
    events = (Event.query.filter(Event.start_time < old)
              .order_by(Event.start_time.desc()))
    return index('events/archive.html', events, page)


@mod.route('/<int:event_id>/')
@mod.route('/<int:event_id>/<slug>/')
def view_event(event_id, slug=None):
    """View a single event."""
    event = Event.query.get_or_404(event_id)

    if not event.published and not current_user.is_authenticated:
        return abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != event.slug:
        return redirect(url_for(
            '.view_event',
            event_id=event.id,
            slug=event.slug))

    return render_template('events/view-event.html', event=event)
