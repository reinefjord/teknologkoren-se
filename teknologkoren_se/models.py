import random
import string
from datetime import datetime
from flask_login import UserMixin
from slugify import slugify
from markdown import markdown
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from teknologkoren_se import db, bcrypt


# Many-to-many relationship between User and Tag
user_tags = db.Table(
    'user_tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    """A representation of a user.

    An email address cannot be longer than 254 characters:
    http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20), nullable=True)

    # Do not change the following directly, use User.password
    _password = db.Column(db.String(128))
    _password_timestamp = db.Column(db.DateTime)

    tags = db.relationship('Tag',
                           secondary=user_tags,
                           backref=db.backref('users'),
                           order_by='Tag.name'
                           )

    def __init__(self, *args, **kwargs):
        if 'password' not in kwargs:
            password = ''.join(random.choice(string.ascii_letters +
                                             string.digits) for _ in range(30))
            kwargs['password'] = password

        super().__init__(*args, **kwargs)


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

    @hybrid_method
    def has_tag(self, tag_name):
        """Return True if User instance has tag with name tag_name."""
        tag = Tag.query.filter_by(name=tag_name).first()
        return tag in self.tags

    @has_tag.expression
    def has_tag(self, tag_name):
        """Return query with all Users that has tag with name tag_name."""
        return self.tags.any(name=tag_name)

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
        user = User.query.filter_by(email=email).first()

        if user and user.verify_password(password):
            return user

        return None

    def __str__(self):
        """String representation of the user."""
        return "{} {}".format(self.first_name, self.last_name)


class Tag(db.Model):
    """Representation of a tag."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)

    def __str__(self):
        """String representation of the tag."""
        return self.name


class Post(db.Model):
    """Representation of a blogpost."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    slug = db.Column(db.String(200))
    content = db.Column(db.Text)
    published = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('posts'))
    image = db.Column(db.String(300), nullable=True)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'post',
        'polymorphic_on': type
    }

    def __init__(self, *args, **kwargs):
        """Initialize object and generate slug if not set."""
        if 'slug' not in kwargs:
            kwargs['slug'] = slugify(kwargs.get('title', ''))
        super().__init__(*args, **kwargs)

    @property
    def url(self):
        """Return the path to the post."""
        return '{}/{}/'.format(self.id, self.slug)

    def content_to_html(self):
        """Return content formatted for html."""
        return markdown(self.content)

    def __str__(self):
        """String representation of the post."""
        return "<{} {}/{}>".format(self.__class__.__name__, self.id, self.slug)


class Event(Post):
    """Representation of an event."""
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    start_time = db.Column(db.DateTime)
    location = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }
