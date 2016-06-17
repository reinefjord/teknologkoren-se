import re
from flask_login import UserMixin
from app import flask_db, bcrypt
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

    def __str__(self):
        return self.email


class Page(flask_db.Model):
    name = CharField()
    is_blog = BooleanField()
    published = BooleanField()

    def __str__(self):
        return self.name


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

    def __str__(self):
        return self.slug


class Event(Post):
    start_time = DateTimeField()
    duration = DateTimeField()
    location = CharField()

    def __str__(self):
        return self.slug
