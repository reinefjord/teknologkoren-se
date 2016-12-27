import datetime
from operator import attrgetter
from flask import abort, Blueprint, redirect, request, render_template, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from app import app, images
from app.forms import EditPostForm
from app.models import Post, Event, File, PostFile


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
        post = Post.create(
                title=form.title.data,
                content=form.content.data,
                published=form.published.data,
                timestamp=datetime.datetime.now(),
                author=current_user.id,
                )

        for field in form.upload.entries:
            if field.has_file():
                image_name = images.save(field.data)
                file = File.create(name=image_name)
                PostFile.create(post=post, file=file)

        return redirect(url_for('.view_post', post_id=post.id, slug=post.slug))

    return render_template('blog/edit-post.html', form=form)


@mod.route('/<int:post_id>/')
@mod.route('/<int:post_id>/<slug>/')
def view_post(post_id, slug=None):
    post = get_object_or_404(Post, Post.id == post_id)

    if not post.published and not current_user.is_authenticated:
        return abort(404)

    if slug != post.slug:
        return redirect(url_for('.view_post', post_id=post.id, slug=post.slug))

    return render_template('blog/view-post.html', post=post)


@mod.route('/edit/<int:post_id>/', methods=['GET', 'POST'])
@mod.route('/edit/<int:post_id>/<slug>/', methods=['GET', 'POST'])
@login_required
def edit_post(post_id, slug=None):
    post = get_object_or_404(Post, Post.id == post_id)

    if slug != post.slug:
        return redirect(url_for('.edit_post', post_id=post.id, slug=post.slug))

    form = EditPostForm(CombinedMultiDict((request.form, request.files)), post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.published = form.published.data
        post.save()

        for field in form.upload.entries:
            if field.has_file():
                image_name = images.save(field.data)
                file = File.create(name=image_name)
                PostFile.create(post=post, file=file)

        return redirect(url_for('.view_post', post_id=post.id, slug=post.slug))

    return render_template('blog/edit-post.html', form=form)


@mod.route('/remove/<int:post_id>/')
@mod.route('/remove/<int:post_id>/<slug>/')
@login_required
def remove_post(post_id, slug=None):
    post = get_object_or_404(Post, Post.id == post_id)
    post.delete_instance()
    return redirect(url_for('.overview'))
