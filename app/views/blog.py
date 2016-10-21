import datetime
from operator import attrgetter
from flask import abort, Blueprint, redirect, request, render_template, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from app import app, images
from app.forms import EditPostForm
from app.models import Post, Event


mod = Blueprint('blog', __name__)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


def is_event(post):
    if isinstance(post, Event):
        return True
    return False


app.jinja_env.globals['url_for_other_page'] = url_for_other_page
app.jinja_env.globals['image_url'] = images.url
app.jinja_env.tests['event'] = is_event


def paginate(content, page, page_size):
    start_index = (page-1) * page_size
    end_index = start_index + page_size
    pagination = content[start_index:end_index]
    return pagination


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def overview(page):
    blogposts = Post.select()
    events = Event.select()

    if not current_user.is_authenticated:
        blogposts = blogposts.where(Post.published == True)
        events = events.where(Event.published == True)

    posts = list(blogposts) + list(events)
    posts.sort(key=attrgetter('timestamp'), reverse=True)

    pagination = paginate(posts, page, 5)

    if not pagination and posts:
        last_page = len(posts) // 5
        if len(posts) % 5:
            last_page += 1
        return redirect(url_for('.overview', page=last_page))

    has_next = True if paginate(posts, page+1, 5) else False

    return render_template('blog/overview.html',
                           pagination=pagination,
                           page=page,
                           has_next=has_next)


@mod.route('/new-post/', methods=['GET', 'POST'])
@login_required
def new_post():
    form = EditPostForm(CombinedMultiDict((request.form, request.files)))
    if form.validate_on_submit():
        if form.upload.has_file():
            image = images.save(form.upload.data)
        else:
            image = None

        post = Post.create(
                title=form.title.data,
                path=url_for('.overview'),
                content=form.content.data,
                published=form.published.data,
                timestamp=datetime.datetime.now(),
                author=current_user.id,
                image=image
                )
        return redirect(post.slug)

    return render_template('blog/edit-post.html', form=form)


@mod.route('/<slug>/')
def view_post(slug):
    post = get_object_or_404(Post, Post.slug == slug)

    if not post.published and not current_user.is_authenticated:
        return abort(404)

    return render_template('blog/view-post.html', post=post)


@mod.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = get_object_or_404(Post, Post.slug == slug)
    form = EditPostForm(CombinedMultiDict((request.form, request.files)), post)

    if form.validate_on_submit():
        if form.upload.has_file():
            post.image = images.save(form.upload.data)
        post.title = form.title.data
        post.content = form.content.data
        post.published = form.published.data
        post.save()
        return redirect(post.slug)

    return render_template('blog/edit-post.html', form=form)


@mod.route('/<slug>/remove/', methods=['GET'])
@login_required
def remove_post(slug):
    post = get_object_or_404(Post, Post.slug == slug)
    post.delete_instance()
    return redirect(url_for('blog.overview'))
