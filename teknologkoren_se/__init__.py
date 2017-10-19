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

    @app.route('/')
    def redirect_to_lang():
        """Redirect root to lang-version"""
        return redirect(url_for('blog.index',
                                lang_code=flask_babel.get_locale()))

    @app.before_request
    def check_lang_code():
        # Some requests do not have any view args, do nothing
        if request.view_args is None:
            return

        # Remove lang_code from the view args, none of our views
        # actually want that argument. None if view_args is missing
        # lang_code.
        lang_code = request.view_args.pop('lang_code', None)

        if lang_code in ('sv', 'en'):
            # Valid lang_code, set the global lang_code
            g.lang_code = lang_code

        elif app.url_map.is_endpoint_expecting(request.endpoint, 'lang_code'):
            # Invalid lang_code (garbage?), if the endpoint is expecting
            # a lang_code, prepend whatever locale flask_babel wants to
            # default to, and redirect to the requested thing.
            return redirect(request.url_root +
                            flask_babel.get_locale().language +
                            request.full_path)

        # else...
        # Endpoint was probably static or something that does not want
        # lang_code, return nothing (None). Execution continues as if
        # nothing happened.

    @app.url_defaults
    def add_lang_code(endpoint, values):
        if 'lang_code' in values or not g.lang_code:
            return
        if app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values['lang_code'] = g.lang_code

    def url_for_lang(endpoint, lang_code, default='blog.index'):
        if endpoint and \
                app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            return url_for(endpoint, lang_code=lang_code)

        return url_for(default, lang_code=lang_code)

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
