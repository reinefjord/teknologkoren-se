from urllib.parse import urljoin
from flask import Blueprint, redirect, render_template, request, session, \
        url_for
from werkzeug.contrib.atom import AtomFeed
from teknologkoren_se.models import Post, Event, Contact


mod = Blueprint('general', __name__)


@mod.route('/om-oss/')
def about():
    """Show about page."""
    return render_template('general/about.html')


@mod.route('/boka/')
def booking():
    """Show booking page."""
    return render_template('general/booking.html')


@mod.route('/sjung/')
def sing():
    """Show audition page."""
    return render_template('general/sing.html')


@mod.route('/kontakt/')
def contact():
    """Show contact page.

    Order of board members and their email addresses are hard coded.
    The template iterates over the list of tags and gets the user from
    the generated dict to display them in the same order every time.
    """
    contacts = Contact.query.order_by(Contact.weight.asc()).all()
    ordf = Contact.query.filter_by(title='Ordförande').first()

    return render_template('general/contact.html',
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


@mod.route('/sv/')
def set_swedish():
    # We make sure to look at if the user has a preferred version of
    # the lang, so that date and time formats (and languages if we
    # happen to have different versions of the same lang) stay the same
    # on first visit and later if the user switches between languages.
    session['locale'] = \
            request.accept_languages.best_match(['sv'], default='sv')
    return redirect(url_for('blog.index'))


@mod.route('/en/')
def set_english():
    session['locale'] = \
            request.accept_languages.best_match(['en'], default='en')
    return redirect(url_for('blog.index'))
