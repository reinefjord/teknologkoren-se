from datetime import datetime
from flask_babel import get_locale, gettext
from markdown import markdown
from slugify import slugify
from sqlalchemy import event
from teknologkoren_se import db, images


class Contact(db.Model):
    """Representation of a person on the 'kontakt' page.

    Should be the board (+ webmaster if you're feeling like it).

    An email address cannot be longer than 254 characters:
    http://www.rfc-editor.org/errata_search.php?rfc=3696&eid=1690
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(254))
    phone = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.Integer)

    def to_dict(self):
        d = {}
        d['id'] = self.id
        d['title'] = self.title
        d['first_name'] = self.first_name
        d['last_name'] = self.last_name
        d['email'] = self.email
        d['phone'] = self.phone
        d['weight'] = self.weight
        return d


class Post(db.Model):
    """Representation of a blogpost.

    This is the parent for "joined table inheritance". This means
    classes can inherit from this class and get an unique table with
    the extra attributes. The tables are joined automatically when
    querying, and when querying the parent children are also included.
    Querying children, however, only returns children.

    To keep track of which kind of object an object is, we have created
    the 'type' attribute and set 'polymorphic_on' to that. The 'type'
    attribute will then contain the 'polymorphic identity', which is
    in this class set to 'post'.

    To query only the parent one simply filters the query by the parent
    type, e.g. `Post.query.filter_by(type='post')`.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    slug = db.Column(db.String(200))
    content_sv = db.Column(db.Text)
    content_en = db.Column(db.Text)
    published = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime)
    image = db.Column(db.String(300), nullable=True)
    type = db.Column(db.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'post',
        'polymorphic_on': type
    }

    @property
    def content(self):
        """Return localized content.

        If not available, prepend notice about missing translation.
        """
        not_available = gettext('(No translation available)\n\n')
        lang = get_locale().language

        if lang == 'sv':
            return self.content_sv or not_available + self.content_en

        if lang == 'en':
            return self.content_en or not_available + self.content_sv

    @property
    def url(self):
        """Return the path to the post."""
        return '{}/{}/'.format(self.id, self.slug)

    def content_to_html(self, content):
        """Return content formatted for html."""
        return markdown(content)

    def to_dict(self):
        d = {}
        d['id'] = self.id
        d['title'] = self.title
        d['slug'] = self.slug
        d['content_sv'] = self.content_sv
        d['content_en'] = self.content_en
        d['published'] = self.published
        d['timestamp'] = self.timestamp
        d['image'] = self.image
        d['image_path'] = images.url(self.image) if self.image else None
        return d

    def __str__(self):
        """String representation of the post."""
        return "<{} {}/{}>".format(self.__class__.__name__, self.id, self.slug)


@event.listens_for(Post.title, 'set', propagate=True)
def create_slug(target, value, oldvalue, initiator):
    """Create slug when new title is set.

    Listens for Post and subclasses of Post.
    """
    target.slug = slugify(value)


class Event(Post):
    """Representation of an event.

    This is so called "joined table inheritance". The attributes in
    this class is in a unique table with only the attributes of this
    class, and is joined with the parent class Post automatically when
    queried to form the table/object with all attributes.
    """
    id = db.Column(db.Integer, db.ForeignKey('post.id'), primary_key=True)
    start_time = db.Column(db.DateTime)
    location = db.Column(db.String(100))

    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }

    def to_dict(self):
        d = super().to_dict()
        d['start_time'] = datetime.strftime(self.start_time, '%Y-%m-%dT%H:%M')
        d['location'] = self.location
        return d
