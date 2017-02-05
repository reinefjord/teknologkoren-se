from datetime import datetime
from flask_login import UserMixin
from teknologkoren_se import flask_db, bcrypt
from peewee import (CharField, TextField, BooleanField, DateTimeField,
                    ForeignKeyField, FixedCharField)
from playhouse.hybrid import hybrid_property
from slugify import slugify
from markdown import markdown


class User(UserMixin, flask_db.Model):
    """A representation of a user."""
    email = CharField(unique=True)
    first_name = CharField()
    last_name = CharField()
    phone = CharField(null=True)
    # Do not change the following directly, use User.password
    _password = CharField()
    _password_timestamp = DateTimeField()

    @hybrid_property
    def password(self):
        """Return password hash."""
        return self._password

    @password.setter
    def _set_password(self, plaintext):
        """Generate and save password hash, update password timestamp."""
        self._password = bcrypt.generate_password_hash(plaintext)

        # Save in UTC, password resets compare this to UTC time!
        self._password_timestamp = datetime.utcnow()

    def verify_password(self, plaintext):
        """Return True if plaintext matches password, else return False."""
        return bcrypt.check_password_hash(self._password, plaintext)

    @hybrid_property
    def tags(self):
        """Return a SelectQuery with the tags of this user."""
        return (
            Tag
            .select()
            .join(UserTag)
            .join(User)
            .where(User.id == self.id))

    @hybrid_property
    def tag_names(self):
        """Return a list of the names of this user's tags."""
        return [tag.name for tag in self.tags]

    @staticmethod
    def has_tag(tag_name):
        """Return a SelectQuery with users that have a matching tag."""
        return (User
                .select()
                .join(UserTag)
                .join(Tag)
                .where(Tag.name << User.tag_names,
                       Tag.name == tag_name))


    @staticmethod
    def authenticate(email, password):
        """Check email and password and return user if matching.

        It might be tempting to return the user that mathes the email
        and a boolean representing if the password was correct, but
        please don't. The email alone does not identify a user, only
        the email toghether with a matching password is enough to
        identify which user we want! No matching email and password ->
        no user.
        """
        try:
            user = User.get(User.email == email)
        except User.DoesNotExist:
            return None

        if user.verify_password(password):
            return user

        return None

    def __str__(self):
        """String representation of the user."""
        return "{} {}".format(self.first_name, self.last_name)


class Tag(flask_db.Model):
    """Representation of a tag."""
    name = CharField(unique=True)

    def __str__(self):
        """String representation of the tag."""
        return self.name


class UserTag(flask_db.Model):
    """Many-to-many relationship table for Users and Tags."""
    user = ForeignKeyField(User)
    tag = ForeignKeyField(Tag)


class Post(flask_db.Model):
    """Representation of a blogpost."""
    title = CharField()
    slug = CharField()
    content = TextField()
    published = BooleanField()
    timestamp = DateTimeField()
    author = ForeignKeyField(User)
    image = CharField(null=True)

    @property
    def url(self):
        """Return the path to the post."""
        return '{}/{}/'.format(self.id, self.slug)

    def save(self, *args, **kwargs):
        """Save the post.

        Extends the peewee built-in .save to generate a slug first.
        """
        self.slug = slugify(self.title)
        super(Post, self).save(*args, **kwargs)

    def content_to_html(self):
        """Return content formatted for html."""
        return markdown(self.content)

    def __str__(self):
        """String representation of the post."""
        return "<{} {}/{}>".format(self.__class__.__name__, self.id, self.slug)


class Event(Post):
    """Representation of an event."""
    start_time = DateTimeField()
    location = CharField()
