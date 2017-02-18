from operator import attrgetter
from flask import abort, Blueprint, redirect, render_template, url_for
from flask_login import current_user
from playhouse.flask_utils import get_object_or_404
from teknologkoren_se import app, images
from teknologkoren_se.models import Post, Event
from teknologkoren_se.util import url_for_other_page


mod = Blueprint('blog', __name__)


def is_event(post):
    """Check whether an object is of Event type.

    Used by templates as posts and events are in the same list.
    """
    if isinstance(post, Event):
        return True
    return False


def image_destination():
    return images.config.base_url


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url
app.jinja_env.globals['image_dest'] = image_destination
app.jinja_env.tests['event'] = is_event


def paginate(content, page, page_size):
    """Return a page of content.

    Calculates which posts to have on a specific page based on which
    page they're on and how many objects there are per page.
    """
    start_index = (page-1) * page_size
    end_index = start_index + page_size
    pagination = content[start_index:end_index]
    return pagination


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def index(page):
    """Show blogposts and events, main page.

    Selects all published posts and events and sorts them outside orm.
    Sorting with database query would require posts and events to be
    joined which would make it difficult for templates to determine
    which objects are posts and which are events.
    """
    blogposts = Post.select().where(Post.published == True)
    events = Event.select().where(Event.published == True)

    posts = list(blogposts) + list(events)
    posts.sort(key=attrgetter('timestamp'), reverse=True)

    pagination = paginate(posts, page, 5)

    # If there are posts in the database, but the pagination is empty
    # (too high page number)
    if not pagination and posts:
        # Get the last page that contains posts and redirect there
        last_page = len(posts) // 5
        if len(posts) % 5:
            last_page += 1
        return redirect(url_for('.index', page=last_page))

    # True if next page has content, else False
    has_next = True if paginate(posts, page+1, 5) else False

    return render_template('blog/overview.html',
                           pagination=pagination,
                           page=page,
                           has_next=has_next)


@mod.route('/<int:post_id>/')
@mod.route('/<int:post_id>/<slug>/')
def view_post(post_id, slug=None):
    """View a single blogpost."""
    post = get_object_or_404(Post, Post.id == post_id)

    if not post.published and not current_user.is_authenticated:
        return abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != post.slug:
        return redirect(url_for('.view_post', post_id=post.id, slug=post.slug))

    return render_template('blog/view-post.html', post=post)
