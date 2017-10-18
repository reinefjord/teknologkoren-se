from flask import abort, Blueprint, redirect, render_template, url_for
from teknologkoren_se import app, images
from teknologkoren_se.models import Post, Event
from teknologkoren_se.util import url_for_other_page


mod = Blueprint('blog', __name__, url_prefix='/<lang_code>')


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


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def index(page):
    """Show blogposts and events, main page.

    Event is a subclass of Post, querying Post returns both events and
    posts.
    """
    posts = (Post.query.filter_by(published=True)
             .order_by(Post.timestamp.desc()))

    pagination = posts.paginate(page, 5)

    return render_template('blog/overview.html',
                           pagination=pagination,
                           page=page)


@mod.route('/blog/<int:post_id>/')
@mod.route('/blog/<int:post_id>/<slug>/')
def view_post(post_id, slug=None):
    """View a single blogpost."""
    post = Post.query.get_or_404(post_id)

    if not post.published:
        return abort(404)

    # Redirect to url with correct slug if missing or incorrect
    if slug != post.slug:
        return redirect(url_for('.view_post', post_id=post.id, slug=post.slug))

    return render_template('blog/view-post.html', post=post)
