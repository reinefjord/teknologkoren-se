from flask import Blueprint, render_template
from app.models import Page, Post


mod = Blueprint('about', __name__, url_prefix='/om-oss/')


@mod.route('/')
def index():
    page = Page.get(Page.name == 'about')
    post = Post.get(Post.page == page)
    return render_template('about.html', post=post)
