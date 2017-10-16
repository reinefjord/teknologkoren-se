from urllib.parse import urljoin
from flask import Blueprint, render_template, request
from werkzeug.contrib.atom import AtomFeed
from teknologkoren_se.models import Post, Event, Contact


mod = Blueprint('general', __name__)


@mod.route('/om-oss/')
def om_oss():
    """Show about page."""
    return render_template('general/om-oss.html')


@mod.route('/boka/')
def boka():
    """Show booking page."""
    return render_template('general/boka.html')


@mod.route('/sjung/')
def sjung():
    """Show audition page."""
    return render_template('general/sjung.html')


@mod.route('/kontakt/')
def kontakt():
    """Show contact page.

    Order of board members and their email addresses are hard coded.
    The template iterates over the list of tags and gets the user from
    the generated dict to display them in the same order every time.
    """
    contacts = Contact.query.order_by(Contact.weight.asc()).all()
    ordf = Contact.query.filter_by(title='Ordförande').first()

    return render_template('general/kontakt.html',
                           contacts=contacts,
                           ordf=ordf)


@mod.route('/lucia/')
def lucia():
    ordf = Contact.query.filter_by(title='Ordförande').first()

    return render_template('general/lucia.html',
                           ordf=ordf)


@mod.route('/feed/')
def atom_feed():
    """Generate and return rss-feed."""
    feed = AtomFeed("Teknologkören", feed_url=request.url,
                    url=request.url_root)

    posts = (Post.query
             .filter_by(published=True)
             .order_by(Post.timestamp.desc())
             .limit(15))

    for post in posts:
        if isinstance(post, Event):
            path_base = "konserter/"
        else:
            path_base = "blog/"

        feed.add(post.title,
                 post.content_to_html(),
                 content_type='html',
                 url=urljoin(request.url_root, path_base+post.url),
                 updated=post.timestamp
                 )

    return feed.get_response()
