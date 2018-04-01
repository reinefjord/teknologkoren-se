import os
from flask import Flask, abort, g, request, redirect, session, url_for
from flask_httpauth import HTTPBasicAuth
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from PIL import Image


def init_views(app):
    from teknologkoren_se.views import (
            api,
            auth,
            blog,
            events,
            errors,
            general,
            )

    app.register_blueprint(api.mod)
    app.register_blueprint(blog.mod)
    app.register_blueprint(events.mod)
    app.register_blueprint(general.mod)


def catch_image_resize(image_size, image):
    """Redirect requests to resized images.

    Flask's built-in server does not understand the image resize
    path argument that nginx uses. This redirects those urls to the
    original images.
    """
    if request.endpoint == 'image_resize':
        non_resized_url = '/static/images/{}'
    elif request.endpoint == 'upload_resize':
        non_resized_url = '/static/uploads/images/{}'
    else:
        # Why are we in this function?
        abort(500)

    non_resized_url = non_resized_url.format(image)

    return redirect(non_resized_url)


def setup_flask_assets(app):
    """Setup Flask-Assets, auto generation of prefixed and minified files."""
    from flask_assets import Bundle, Environment

    bundles = {
            'common_css': Bundle(
                'css/lib/normalize.css',
                'css/style.css',
                output='gen/common.css',
                filters=['autoprefixer6', 'cleancss'],
                ),
            }

    assets = Environment(app)
    assets.register(bundles)
    return assets


def setup_babel(app):
    import flask_babel
    from werkzeug.routing import RequestRedirect, MethodNotAllowed, NotFound

    babel = flask_babel.Babel(app)

    @babel.localeselector
    def get_locale():
        lang_code = getattr(g, 'lang_code', None) or \
                session.get('lang_code', None)

        if lang_code is not None:
            return lang_code

        lang_code = request.accept_languages.best_match(['sv', 'en'])

        return lang_code

    @app.before_request
    def fix_missing_lang_code():
        if getattr(g, 'lang_code', None) or request.endpoint == 'static':
            # Lang code is not missing.
            return

        # If g.lang_code is not set, the lang code in path (/sv/) is
        # probably missing (or misspelled/invalid).

        # Get a MapAdapter, the object used for matching urls.
        urls = app.url_map.bind(app.config['SERVER_NAME'])

        # Get whatever lang get_locale() decides (cookie or, if no cookie,
        # default), and prepend it to the requested path.
        proposed_lang = flask_babel.get_locale().language
        new_path = proposed_lang + request.path

        try:
            # Does this new path match any view?
            urls.match(new_path)
        except RequestRedirect as e:
            # The new path results in a redirect.
            return redirect(e.new_url)
        except (MethodNotAllowed, NotFound):
            # The new path does not match anything, we allow the request
            # to continue with the non-lang path. Probably 404. In case
            # this request results in something that does want a lang
            # code (error pages need it as main.html builds urls for the
            # nav), we set it to whatever was proposed by get_locale().
            # If we don't set it AND the client does not have lang saved
            # in a cookie, we'd get a 500.
            g.lang_code = proposed_lang
            return None

        # The new path matches a view! We redirect there.
        return redirect(new_path)

    def url_for_lang(endpoint,
                     lang_code,
                     view_args,
                     default='blog.index',
                     **args):

        if (endpoint and
                app.url_map.is_endpoint_expecting(endpoint, 'lang_code')):

            return url_for(endpoint,
                           lang_code=lang_code,
                           **view_args or {},
                           **args)

        return url_for(default, lang_code=lang_code, **view_args or {}, **args)

    app.jinja_env.globals['locale'] = flask_babel.get_locale
    app.jinja_env.globals['format_datetime'] = flask_babel.format_datetime
    app.jinja_env.globals['format_date'] = flask_babel.format_date
    app.jinja_env.globals['url_for_lang'] = url_for_lang

    return babel


app = Flask(__name__)
app.config.from_object('config')

app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

token_auth = HTTPBasicAuth()

CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))


def img_dimensions(img, upload=True):
    if upload:
        path = images.path(img)
    else:
        path = os.path.join('teknologkoren_se/static/images', img)

    abs_path = os.path.join(app.config['BASEDIR'], path)

    try:
        pimg = Image.open(abs_path)
    except FileNotFoundError:
        return ('', '')

    return pimg.size


app.jinja_env.globals['img_dimensions'] = img_dimensions

assets = setup_flask_assets(app)

babel = setup_babel(app)

init_views(app)  # last, views might import stuff from this file

if app.debug:
    # If in debug mode, add rule for resized image paths to go through
    # the redirection function.
    app.add_url_rule('/static/images/<image_size>/<image>',
                     endpoint='image_resize',
                     view_func=catch_image_resize)

    app.add_url_rule('/static/uploads/images/<image_size>/<image>',
                     endpoint='upload_resize',
                     view_func=catch_image_resize)
