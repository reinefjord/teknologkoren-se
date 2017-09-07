import locale
from flask import Flask, abort, request, redirect
from flask_bcrypt import Bcrypt
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

locale.setlocale(locale.LC_TIME, "sv_SE.utf8")


def init_views(app):
    from teknologkoren_se.views import (
            auth,
            blog,
            events,
            errors,
            general,
            intranet
            )

    app.register_blueprint(auth.mod, subdomain='www')
    app.register_blueprint(blog.mod, subdomain='www')
    app.register_blueprint(events.mod, subdomain='www')
    app.register_blueprint(general.mod, subdomain='www')
    app.register_blueprint(intranet.mod, subdomain='intranet')


def setup_login_manager(app):
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    return login_manager


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

    from teknologkoren_se.models import User, Post, Event, Tag, UserTag

    admin = Admin(app,
                  name='teknologkoren.se',
                  subdomain='intranet',
                  static_url_path='/flask-admin/',
                  index_view=LoginIndexView(url='/flask-admin'))

    admin.add_view(LoginModelView(User, db.session, name='User'))
    admin.add_view(LoginModelView(Post, db.session, name='Post'))
    admin.add_view(LoginModelView(Event, db.session, name='Event'))
    admin.add_view(LoginModelView(Tag, db.session, name='Tag'))
    admin.add_view(LoginModelView(UserTag, db.session, name='UserTag'))

    return admin


def setup_converters(app):
    from .util import ListConverter
    app.url_map.converters['list'] = ListConverter


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
        # Why are we in this functions?
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

            'intranet_css': Bundle(
                'css/intranet.css',
                output='gen/intranet.css',
                filters=['autoprefixer6', 'cleancss'],
                ),
            }

    assets = Environment(app)
    assets.register(bundles)
    return assets


app = Flask(__name__, static_folder=None)
app.config.from_object('config')

app.static_folder = 'static'
app.add_url_rule('/static/<path:filename>',
                 endpoint='static',
                 subdomain='www',
                 view_func=app.send_static_file)

app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

CORS(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

bcrypt = Bcrypt(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))


login_manager = setup_login_manager(app)
admin = setup_flask_admin(app)
assets = setup_flask_assets(app)

setup_converters(app)

init_views(app) # last, views might import stuff from this file


if app.debug:
    # If in debug mode, add rule for resized image paths to go through
    # the redirection function.
    app.add_url_rule('/static/images/<image_size>/<image>',
                     endpoint='image_resize',
                     subdomain='www',
                     view_func=catch_image_resize)

    app.add_url_rule('/static/uploads/images/<image_size>/<image>',
                     endpoint='upload_resize',
                     subdomain='www',
                     view_func=catch_image_resize)
