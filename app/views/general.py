import datetime
from flask import Blueprint, redirect, request, render_template, url_for
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from app import app
from app.forms import CreatePostForm
from app.models import Post


mod = Blueprint('general', __name__)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


@mod.route('/new-post/', methods=['GET', 'POST'])
@login_required
def new_post():
    form = CreatePostForm(request.form)
    if form.validate_on_submit():
        post = Post.create(title=form.title.data,
                           content=form.content.data,
                           published=form.published.data,
                           is_page=form.is_page.data,
                           timestamp=datetime.datetime.now(),
                           author=current_user.id)
        return redirect(post.slug)

    return render_template('edit-post.html', form=form)


@mod.route('/<slug>/')
def view_post(slug):
    post = get_object_or_404(Post, Post.slug == slug)

    if post.is_page:
        return render_template('view-page.html', post=post)

    return render_template('view-post.html', post=post)


@mod.route('/<slug>/edit/', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = get_object_or_404(Post, Post.slug == slug)
    form = CreatePostForm(request.form, post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.is_page = form.is_page.data
        post.published = form.published.data
        post.save()
        return redirect(post.slug)

    return render_template('edit-post.html', form=form)
