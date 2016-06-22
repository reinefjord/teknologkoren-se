from flask_login import UserMixin
from app import flask_db, bcrypt
from peewee import (CharField, TextField, BooleanField, DateTimeField,
                    ForeignKeyField)
from playhouse.hybrid import hybrid_property
from slugify import slugify


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


class Post(flask_db.Model):
    title = CharField()
    slug = CharField(unique=True)
    content = TextField()
    published = BooleanField()
    timestamp = DateTimeField()
    author = ForeignKeyField(User)
    is_page = BooleanField()

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(self.title)
            self.slug = slug
            uid = 2
            while True:
                try:
                    Post.get(Post.slug == self.slug)
                except Post.DoesNotExist:
                    break
                else:
                    self.slug = slug + '-' + str(uid)
                    uid += 1

        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.slug


class Event(Post):
    start_time = DateTimeField()
    duration = DateTimeField()
    location = CharField()

    def __str__(self):
        return self.slug
