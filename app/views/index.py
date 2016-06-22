from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user
from app.models import Post


mod = Blueprint('index', __name__)


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>/')
def index(page):
    if current_user.is_authenticated:
        posts = Post.select().where(Post.is_page == False).order_by(Post.timestamp.desc())
    else:
        posts = Post.select().where((Post.is_page == False) &
                                    (Post.published == True)
                                    ).order_by(Post.timestamp.desc())

    pagination = posts.paginate(page, 5)

    if not pagination:
        if posts:
            last_page = (len(posts) // 5) + 1
            return redirect(url_for('.index', page=last_page))

    has_next = True if posts.paginate(page+1, 5) else False

    return render_template('index.html',
                           pagination=pagination,
                           page=page,
                           has_next=has_next)
