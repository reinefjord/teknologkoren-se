from datetime import datetime, timedelta
from flask import abort, Blueprint, redirect, render_template, url_for
from teknologkoren_se import app, images
from teknologkoren_se.models import Event
from teknologkoren_se.util import url_for_other_page, \
        bp_url_processors


mod = Blueprint('events',
                __name__,
                url_prefix='/<any(sv, en):lang_code>/konserter')

bp_url_processors(mod)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def index(page):
    """Show upcoming events.

    An event is still considered 'coming' if it is less than 3 hours
    after start time, allowing people to see that there is an ongoing
    event.
    """
    old = datetime.utcnow() - timedelta(hours=3)
    events = (Event.query
              .filter(Event.start_time > old, Event.published == True)
              .order_by(Event.start_time.desc()))

    pagination = events.paginate(page, 5)

    return render_template('events/coming.html',
                           pagination=pagination,
                           page=page)


@mod.route('/arkiv/', defaults={'page': 1})
@mod.route('/arkiv/page/<int:page>/')
def archive(page):
    """Show old (archived) events.

    And event is considered archived if there has been more than
    3 hours since the start time of the event.
    """
    old = datetime.utcnow() - timedelta(hours=3)
    events = (Event.query
              .filter(Event.start_time < old, Event.published == True)
              .order_by(Event.start_time.desc()))

    pagination = events.paginate(page, 5)

    return render_template('events/archive.html',
                           pagination=pagination,
                           page=page)


@mod.route('/<int:event_id>/')
@mod.route('/<int:event_id>/<slug>/')
def view_event(event_id, slug=None):
    """View a single event."""
    event = Event.query.get_or_404(event_id)

    if not event.published:
        return abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != event.slug:
        return redirect(url_for(
            '.view_event',
            event_id=event.id,
            slug=event.slug))

    return render_template('events/view-event.html', event=event)
