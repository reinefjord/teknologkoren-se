import random
from string import ascii_letters, digits
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
    _password = CharField()
    _password_id = CharField()

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        self._password = bcrypt.generate_password_hash(plaintext)
        self._password_id = ''.join(random.choice(ascii_letters + digits)
                                    for _ in range(6))

    def verify_password(self, plaintext):
        return bcrypt.check_password_hash(self._password, plaintext)

    @hybrid_property
    def tags(self):
        return (
            Tag
            .select()
            .join(UserTag)
            .join(User)
            .where(User.id == self.id))

    @hybrid_property
    def tag_names(self):
        return [tag.name for tag in self.tags]

    @staticmethod
    def has_tag(tag_name):
        return (User
                .select()
                .join(UserTag)
                .join(Tag)
                .where(Tag.name << User.tag_names,
                       Tag.name == tag_name))

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
    content = TextField()
    published = BooleanField()
    timestamp = DateTimeField()
    author = ForeignKeyField(User)
    image = CharField(null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return "<{} {}/{}>".format(self.__class__.__name__, self.id, self.slug)


class Event(Post):
    start_time = DateTimeField()
    location = CharField()
