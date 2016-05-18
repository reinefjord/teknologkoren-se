from flask import Blueprint, render_template
from app.models import Page, Post

mod = Blueprint('index', __name__)


@mod.route('/', defaults={'page': 1})
@mod.route('/page/<int:page>')
def index(page):
    index = Page.get(Page.name == 'index')
    posts = Post.select().where(
            Post.page == index).order_by(Post.timestamp.desc())
    pagination = posts.paginate(page, 5)
    has_next = True if posts.paginate(page+1, 5) else False

    return render_template('index.html',
                           pagination=pagination,
                           page=page,
                           has_next=has_next)
