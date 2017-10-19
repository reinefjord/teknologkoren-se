from flask import Flask, abort, g, request, redirect, session, url_for
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
            return

        urls = app.url_map.bind(app.config['SERVER_NAME'])
        new_path = flask_babel.get_locale().language + request.path

        try:
            urls.match(new_path)
        except RequestRedirect as e:
            return redirect(e.new_url)
        except (MethodNotAllowed, NotFound):
            return None

        return redirect(new_path)

    def url_for_lang(endpoint, lang_code, view_args, default='blog.index'):
        if endpoint and \
                app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            return url_for(endpoint, lang_code=lang_code, **view_args or {})

        return url_for(default, lang_code=lang_code, **view_args or {})

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
