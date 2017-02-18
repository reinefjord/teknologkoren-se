import locale
from flask import Flask, abort
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.peewee import ModelView
from flask_uploads import configure_uploads, IMAGES, UploadSet
from playhouse.flask_utils import FlaskDB

locale.setlocale(locale.LC_TIME, "sv_SE.utf8")

app = Flask(__name__)
app.config.from_object('config')


@app.before_request
def _db_connect():
    db.connect()


@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

flask_db = FlaskDB(app)
db = flask_db.database

bcrypt = Bcrypt(app)

images = UploadSet('images', IMAGES)
configure_uploads(app, (images,))


from .util import ListConverter
app.url_map.converters['list'] = ListConverter


from teknologkoren_se.models import User, Post, Event, Tag, UserTag


class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return 'Webmaster' in current_user.tag_names
        return False

    def inaccessible_callback(self, name, **kwargs):
        return abort(403)


admin = Admin(app, index_view=AdminHomeView(), name='teknologkoren.se')
admin.add_view(ModelView(User, name='User'))
admin.add_view(ModelView(Post, name='Post'))
admin.add_view(ModelView(Event, name='Event'))
admin.add_view(ModelView(Tag, name='Tag'))
admin.add_view(ModelView(UserTag, name='UserTag'))

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
