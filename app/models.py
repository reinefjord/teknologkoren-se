import re
from flask.ext.login import UserMixin
from app import db, flask_db, bcrypt
from peewee import (CharField, TextField, BooleanField, DateTimeField,
                    ForeignKeyField)
from playhouse.hybrid import hybrid_property


class User(UserMixin, flask_db.Model):
    email = CharField(unique=True)
    _password = CharField()

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def verify_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)


class Page(flask_db.Model):
    name = CharField()
    is_blog = BooleanField()
    published = BooleanField()


class Post(flask_db.Model):
    title = CharField()
    slug = CharField(unique=True)
    content = TextField()
    published = BooleanField()
    timestamp = DateTimeField()
    author = ForeignKeyField(User)
    page = ForeignKeyField(Page)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = re.sub('[^\w]+', '-', self.title.lower())
        ret = super(Post, self).save(*args, **kwargs)


class Event(Post):
    start_time = DateTimeField()
    duration = DateTimeField()
    location = CharField()
