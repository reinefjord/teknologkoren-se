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
login_manager.login_view = 'users.login'

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


flask_admin = Admin(app, index_view=AdminHomeView(), name='teknologkoren.se')
flask_admin.add_view(ModelView(User, name='User'))
flask_admin.add_view(ModelView(Post, name='Post'))
flask_admin.add_view(ModelView(Event, name='Event'))
flask_admin.add_view(ModelView(Tag, name='Tag'))
flask_admin.add_view(ModelView(UserTag, name='UserTag'))

from teknologkoren_se.views.public import general, users, blog, events
from teknologkoren_se.views.intranet import (intranet, administration,
                                             edit_post, edit_event)

app.register_blueprint(general.mod)
app.register_blueprint(users.mod)
app.register_blueprint(blog.mod)
app.register_blueprint(events.mod)
app.register_blueprint(intranet.mod)
app.register_blueprint(administration.mod)
app.register_blueprint(edit_post.mod)
app.register_blueprint(edit_event.mod)
