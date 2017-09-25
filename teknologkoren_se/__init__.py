import locale
from flask import Flask, abort, request, redirect
from flask_httpauth import HTTPTokenAuth
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

locale.setlocale(locale.LC_TIME, "sv_SE.utf8")


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


app = Flask(__name__)
app.config.from_object('config')

app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

# (Token) To authorize, client sends 'Authorization: Token <token>' in http
# headers.
token_auth = HTTPTokenAuth(scheme='Token')

CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))

assets = setup_flask_assets(app)

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
