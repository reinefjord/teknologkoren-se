from operator import attrgetter
from urllib.parse import urljoin
from flask import Blueprint, render_template, request
from werkzeug.contrib.atom import AtomFeed
from teknologkoren_se.models import User, Tag, UserTag, Post, Event


mod = Blueprint('general', __name__)


@mod.route('/om-oss/')
def om_oss():
    return render_template('general/om-oss.html')


@mod.route('/boka/', methods=['GET', 'POST'])
def boka():
    return render_template('general/boka.html')


@mod.route('/sjung/')
def sjung():
    return render_template('general/sjung.html')


@mod.route('/kontakt/')
def kontakt():
    users = User.select()
    board = {}
    tags = ['Ordförande', 'Vice ordförande', 'Kassör', 'Sekreterare',
            'PRoletär', 'Notfisqual', 'Qlubbmästare']

    tags_copy = list(tags)

    for tag in tags_copy:
        try:
            board[tag] = (users
                          .join(UserTag)
                          .join(Tag)
                          .where(Tag.name == tag)
                          .get())

        except User.DoesNotExist:
            tags.remove(tag)

    return render_template('general/kontakt.html', board=board, tags=tags)


@mod.route('/feed/')
def atom_feed():
    feed = AtomFeed("Teknologkören", feed_url=request.url,
                    url=request.url_root)

    blogposts = (Post.select()
                 .where(Post.published == True).order_by(Post.timestamp.desc()))
    events = (Event.select()
              .where(Event.published == True).order_by(Event.timestamp.desc()))

    posts = list(blogposts) + list(events)

    posts.sort(key=attrgetter('timestamp'), reverse=True)
    posts = posts[:15]

    for post in posts:
        feed.add(post.title, post.content, content_type='html',
                 author=post.author, url=urljoin(request.url_root, post.url),
                 updated=post.timestamp)

    return feed.get_response()
