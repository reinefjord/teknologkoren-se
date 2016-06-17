import datetime
from flask import Blueprint, request, render_template, url_for
from flask_login import current_user, login_required
from app import app
from app.forms import CreatePostForm
from app.models import Page, Post

mod = Blueprint('general', __name__)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


@mod.route('/<page>/new-post/', methods=['GET', 'POST'])
@login_required
def new_post(page):
    page_obj = Page.get(Page.name == page)
    form = CreatePostForm(request.form)
    if form.validate_on_submit():
        Post.create(title=form.title.data,
                    content=form.trix.data,
                    published=form.published.data,
                    timestamp=datetime.datetime.now(),
                    author=current_user.id,
                    page=page_obj.id)

    return render_template('new-post.html', page=page_obj, form=form)


@mod.route('/edit-post/<slug>/', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = Post.get(Post.slug == slug)
    form = CreatePostForm(request.form, post)
    return render_template('new-post.html',
                           page=None,
                           form=form)
