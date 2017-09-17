import datetime
from flask import abort, Blueprint, jsonify, request, url_for
from teknologkoren_se import db, images
from teknologkoren_se.models import Post, Event


mod = Blueprint('api', __name__, url_prefix='/api')


def make_post_dict(post):
    """Convert post or event to jsonable dict"""
    post_dict = post.to_dict()

    if isinstance(post, Event):
        uri = url_for('.get_event', event_id=post.id)
    else:
        uri = url_for('.get_post', post_id=post.id)

    post_dict['uri'] = uri
    return post_dict


# ----- POSTS ----- #

def get_new_post_data():
    """Validate and return POSTed post-data."""
    data = request.get_json()
    fields = {
            'title': str,
            'content': str,
            'published': bool,
            'image': (str, type(None)),
            }

    if not all(key in data for key in fields):
        abort(400)

    try:
        if not all(isinstance(data[key], fields[key]) for key in data):
            abort(400)
    except KeyError:
        # Found key not in template
        abort(400)

    if not all(data[key] for key in fields if isinstance(data[key], str)):
        abort(400)

    return data


@mod.route('/posts', methods=['GET'])
def get_posts():
    """Get all posts.

    Returns all posts in a list in a json.
    """
    posts = Post.query.filter_by(type='post')
    response = {'posts': [make_post_dict(post) for post in posts]}
    return jsonify(response)


@mod.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get specific post

    Returns a jsonified post.
    """
    # None if no post (not event) with that id (return 404), raises
    # exception if multiple found.
    post = Post.query.filter_by(type='post', id=post_id).one_or_none()
    if post:
        response = make_post_dict(post)
        return jsonify(response)
    abort(404)


@mod.route('/posts', methods=['POST'])
def new_post():
    """Create a new post.

    Creates a new post and returns the post jsonified.
    """
    data = get_new_post_data()
    post = Post(**data)
    post.timestamp = datetime.datetime.now()
    db.session.add(post)
    db.session.commit()

    response = make_post_dict(post)
    return jsonify(response)


@mod.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Overwrite existing post.

    All fields are required, partial updates should use "PATCH" as
    method.
    """
    post = Post.query.get_or_404(post_id)
    data = get_new_post_data()
    post.title = data['title']
    post.content = data['content']
    post.published = data['published']
    post.image = data['image']
    db.session.commit()

    response = make_post_dict(post)
    return jsonify(response)

# ----- END POSTS ----- #

# ----- EVENTS ----- #


@mod.route('/events', methods=['GET'])
def get_events():
    """Get all events.

    Returns a jsonified list of all events.
    """
    events = Event.query.all()
    response = {'events': [make_post_dict(event) for event in events]}
    return jsonify(response)


@mod.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get specific event.

    Returns a jsonified event.
    """
    event = Event.query.get_or_404(event_id)
    response = make_post_dict(event)
    return jsonify(response)


def get_new_event_data():
    """Validate and return POSTed event-data.

    All fields that does not make sense to create server side are
    required, otherwise abort with 400.
    """
    data = request.get_json()
    fields = {
            'title': str,
            'content': str,
            'published': bool,
            'image': (str, type(None)),
            'start_time': str,
            'location': str,
            }

    if not all(key in data for key in fields):
        abort(400)

    try:
        if not all(isinstance(data[key], fields[key]) for key in data):
            abort(400)
    except KeyError:
        # Found key not in template
        abort(400)

    if not all(data[key] for key in fields if isinstance(data[key], str)):
        abort(400)

    try:
        data['start_time'] = datetime.datetime.strptime(data['start_time'],
                                                        '%Y-%m-%dT%H:%M')
    except ValueError:
        abort(400)

    return data


@mod.route('/events', methods=['POST'])
def new_event():
    """Create a new event.

    Field requirements are defined with get_new_event_data().
    """
    data = get_new_event_data()
    event = Event(**data)
    event.timestamp = datetime.datetime.now()
    db.session.add(event)
    db.session.commit()

    response = make_post_dict(event)
    return jsonify(response)


@mod.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Overwrite existing event.

    All fields are required, partials updates should use "PATCH" as
    method.
    """
    event = Event.query.get_or_404(event_id)
    data = get_new_event_data()
    event.title = data['title']
    event.content = data['content']
    event.published = data['published']
    event.image = data['image']
    db.session.commit()

    response = make_post_dict(event)
    return jsonify(response)

# ----- END EVENTS ----- #


@mod.route('/images', methods=['POST'])
def upload_image():
    """Upload a image.

    Returns image info jsonified.
    """
    if 'image' in request.files:
        filename = images.save(request.files['image'])
        response = {"filename": filename, "path": images.url(filename)}
        return jsonify(response)

    abort(400)
