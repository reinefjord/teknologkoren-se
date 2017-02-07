import datetime
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user, login_required
from playhouse.flask_utils import get_object_or_404
from werkzeug.datastructures import CombinedMultiDict
from teknologkoren_se import images
from teknologkoren_se.forms import EditPostForm
from teknologkoren_se.models import Post
from teknologkoren_se.util import tag_required


mod = Blueprint('edit_post', __name__, url_prefix='/intranet/admin/post')


@mod.route('/')
@tag_required('Webmaster')
def view_posts():
    """Show links to all post's edit mode."""
    posts = Post.select().order_by(Post.timestamp.desc())

    return render_template('intranet/view-posts.html', posts=posts)


@mod.route('/new/', methods=['GET', 'POST'])
@login_required
@tag_required('Webmaster')
def new_post():
    """Create a new post."""
    form = EditPostForm(CombinedMultiDict((request.form, request.files)))
    if form.validate_on_submit():
        if form.upload.data:
            image = images.save(form.upload.data)
        else:
            image = None

        post = Post.create(
                title=form.title.data,
                path=url_for('.index'),
                content=form.content.data,
                published=form.published.data,
                timestamp=datetime.datetime.now(),
                author=current_user.id,
                image=image
                )
        return redirect(url_for('blog.view_post', post_id=post.id, slug=post.slug))

    return render_template('intranet/edit-post.html', form=form, post=None)


@mod.route('/edit/<int:post_id>/', methods=['GET', 'POST'])
@mod.route('/edit/<int:post_id>/<slug>/', methods=['GET', 'POST'])
@tag_required('Webmaster')
def edit_post(post_id, slug=None):
    """Edit an existing post."""
    post = get_object_or_404(Post, Post.id == post_id)

    if slug != post.slug:
        return redirect(url_for('.edit_post', post_id=post.id, slug=post.slug))

    form = EditPostForm(CombinedMultiDict((request.form, request.files)),
                        obj=post)

    if form.validate_on_submit():
        if form.upload.data:
            post.image = images.save(form.upload.data)
        post.title = form.title.data
        post.content = form.content.data
        post.published = form.published.data
        post.save()
        return redirect(url_for('blog.view_post', post_id=post.id, slug=post.slug))

    return render_template('intranet/edit-post.html', form=form, post=post)


@mod.route('/remove/<int:post_id>/')
@mod.route('/remove/<int:post_id>/<slug>/')
@tag_required('Webmaster')
def remove_post(post_id, slug=None):
    """Remove a post."""
    post = get_object_or_404(Post, Post.id == post_id)
    post.delete_instance()
    return redirect(url_for('.view_posts'))
