from flask import Flask, abort, g, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS


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

    babel = flask_babel.Babel(app)

    @babel.localeselector
    def get_locale():
        lang_code = getattr(g, 'lang_code', None)
        if lang_code is not None:
            return lang_code

        g.lang_code = request.accept_languages.best_match(['sv', 'en'])

        return g.lang_code

    app.jinja_env.globals['locale'] = flask_babel.get_locale
    app.jinja_env.globals['format_datetime'] = flask_babel.format_datetime
    app.jinja_env.globals['format_date'] = flask_babel.format_date

    @app.route('/')
    def redirect_to_lang():
        return redirect(url_for('blog.index',
                                lang_code=flask_babel.get_locale()))

    @app.url_defaults
    def add_language_code(endpoint, values):
        if 'lang_code' in values or not g.lang_code:
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        if values is not None:
            g.lang_code = values.pop('lang_code', None)

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
