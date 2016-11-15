from flask_login import UserMixin
from app import flask_db, bcrypt
from peewee import (CharField, TextField, BooleanField, DateTimeField,
                    ForeignKeyField, FixedCharField)
from playhouse.hybrid import hybrid_property
from slugify import slugify


class User(UserMixin, flask_db.Model):
    email = CharField(unique=True)
    first_name = CharField()
    last_name = CharField()
    phone = CharField(null=True)
    active = BooleanField()
    _password = CharField()

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)

    def verify_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)

    @property
    def tags(self):
        return [tag.name for tag in (
            Tag
            .select()
            .join(UserTag)
            .join(User)
            .where(User.id == self.id))]

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)


class Tag(flask_db.Model):
    name = CharField(unique=True)

    def __str__(self):
        return self.name


class UserTag(flask_db.Model):
    user = ForeignKeyField(User)
    tag = ForeignKeyField(Tag)


class Post(flask_db.Model):
    title = CharField()
    slug = CharField()
    path = CharField()
    content = TextField()
    published = BooleanField()
    timestamp = DateTimeField()
    author = ForeignKeyField(User)
    image = CharField(null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return "{}{}/{}".format(self.path, self.id, self.slug)


class Event(Post):
    start_time = DateTimeField()
    location = CharField()
