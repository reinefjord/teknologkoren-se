from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.peewee import ModelView
from playhouse.flask_utils import FlaskDB

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

from app.models import User, Page, Post, Event
admin = Admin(app, name='teknologkoren.se')
admin.add_view(ModelView(User, name='User'))
admin.add_view(ModelView(Page, name='Page'))
admin.add_view(ModelView(Post, name='Post'))
admin.add_view(ModelView(Event, name='Event'))

from app.views import (general,
                       users,
                       index,
                       about,
                       intranet)

app.register_blueprint(general.mod)
app.register_blueprint(users.mod)
app.register_blueprint(index.mod)
app.register_blueprint(about.mod)
app.register_blueprint(intranet.mod)
