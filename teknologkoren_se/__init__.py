import locale
from flask import Flask, abort
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

locale.setlocale(locale.LC_TIME, "sv_SE.utf8")

app = Flask(__name__, static_folder=None)
app.config.from_object('config')

app.static_folder = 'static'
app.add_url_rule('/static/<path:filename>',
                 endpoint='static',
                 subdomain='www',
                 view_func=app.send_static_file)

app.jinja_env.lstrip_blocks = True
app.jinja_env.trim_blocks = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

bcrypt = Bcrypt(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))

from .util import ListConverter
app.url_map.converters['list'] = ListConverter


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


from teknologkoren_se.models import User, Post, Event, Tag

admin = Admin(app, index_view=LoginIndexView(), name='teknologkoren.se')
admin.add_view(LoginModelView(User, db.session, name='User'))
admin.add_view(LoginModelView(Post, db.session, name='Post'))
admin.add_view(LoginModelView(Event, db.session, name='Event'))
admin.add_view(LoginModelView(Tag, db.session, name='Tag'))

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
