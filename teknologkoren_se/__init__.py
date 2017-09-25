import locale
from flask import Flask, abort, request, redirect
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

locale.setlocale(locale.LC_TIME, "sv_SE.utf8")


def init_views(app):
    from teknologkoren_se.views import (
            api,
            blog,
            events,
            errors,
            general,
            )

    app.register_blueprint(api.mod)
    app.register_blueprint(blog.mod)
    app.register_blueprint(events.mod)
    app.register_blueprint(general.mod)


def setup_flask_admin(app):
    """Setup Flask-Admin and restrict access to it."""
    from flask_admin import Admin, AdminIndexView
    from flask_admin.contrib.sqla import ModelView
    from flask_login import current_user

    class AdminLoginMixin:
        def is_accessible(self):
            if current_user.is_authenticated:
                return current_user.has_tag('Webmaster')
            return False

        def inaccessible_callback(self, name, **kwargs):
            return abort(403)

    class LoginIndexView(AdminLoginMixin, AdminIndexView):
        pass

    class LoginModelView(AdminLoginMixin, ModelView):
        pass

    from teknologkoren_se.models import Post, Event

    admin = Admin(app,
                  name='teknologkoren.se',
                  static_url_path='/flask-admin/',
                  index_view=LoginIndexView(url='/flask-admin'))

    admin.add_view(LoginModelView(Post, db.session, name='Post'))
    admin.add_view(LoginModelView(Event, db.session, name='Event'))

    return admin


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

CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))

admin = setup_flask_admin(app)
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
