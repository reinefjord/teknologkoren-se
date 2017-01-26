from datetime import datetime, timedelta
from flask import abort, Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from teknologkoren_se import app, images
from teknologkoren_se.forms import EditEventForm
from teknologkoren_se.models import Event


mod = Blueprint('events', __name__, url_prefix='/konserter')


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url


def index(template, events, page):
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
    return index('events/coming.html', events, page)


@mod.route('/arkiv/', defaults={'page': 1})
@mod.route('/arkiv/page/<int:page>/')
def archive(page):
    old = datetime.now() - timedelta(hours=3)
    events = Event.select(
            ).where(Event.start_time < old).order_by(Event.start_time.desc())
    has_next = True if events.paginate(page+1, 5) else False

    return index('events/archive.html', events, page)


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
