from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.bcrypt import Bcrypt
from peewee import *
from playhouse.flask_utils import FlaskDB
from playhouse.sqlite_ext import *

app = Flask(__name__)
app.config.from_object('config')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#db = SQLAlchemy(app)

flask_db = FlaskDB(app)
db = flask_db.database

bcrypt = Bcrypt(app)

from app import views, models
