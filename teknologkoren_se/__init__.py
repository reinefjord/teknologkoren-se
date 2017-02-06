import locale
from flask import Flask, abort
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_uploads import configure_uploads, IMAGES, UploadSet
from flask_sqlalchemy import SQLAlchemy

locale.setlocale(locale.LC_TIME, "sv_SE.utf8")

app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))

from .util import ListConverter
app.url_map.converters['list'] = ListConverter

from teknologkoren_se.models import User, Post, Event, Tag, user_tags


class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return 'Webmaster' in current_user.tag_names
        return False

    def inaccessible_callback(self, name, **kwargs):
        return abort(403)


admin = Admin(app, index_view=AdminHomeView(), name='teknologkoren.se')
admin.add_view(ModelView(User, db.session, name='User'))
admin.add_view(ModelView(Post, db.session, name='Post'))
admin.add_view(ModelView(Event, db.session, name='Event'))
admin.add_view(ModelView(Tag, db.session, name='Tag'))

from teknologkoren_se.views import (
    auth,
    blog,
    events,
    general,
    intranet
    )

app.register_blueprint(auth.mod)
app.register_blueprint(blog.mod)
app.register_blueprint(events.mod)
app.register_blueprint(general.mod)
app.register_blueprint(intranet.mod)
