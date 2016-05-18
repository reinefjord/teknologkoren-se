from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.bcrypt import Bcrypt
from peewee import *
from playhouse.flask_utils import FlaskDB
from playhouse.sqlite_ext import *

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
login_manager.login_view = 'login'

flask_db = FlaskDB(app)
db = flask_db.database

bcrypt = Bcrypt(app)

from app import models
from app.views import (general,
                       index,
                       intranet)

app.register_blueprint(general.mod)
app.register_blueprint(index.mod)
app.register_blueprint(intranet.mod)
