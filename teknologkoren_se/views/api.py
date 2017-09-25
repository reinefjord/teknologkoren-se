import datetime
from flask import abort, Blueprint, jsonify, request, url_for
from teknologkoren_se import app, token_auth, db, images
from teknologkoren_se.models import Post, Event, Contact


mod = Blueprint('api', __name__, url_prefix='/api')


@mod.before_request
@token_auth.login_required
def check_token():
    """Auth-token required before any calls to this blueprint.

    The decorator is doing all the work, this function doesn't need to
    do anything.
    """
    pass


def make_post_dict(post):
    """Convert post or event to jsonable dict"""
    post_dict = post.to_dict()

    if isinstance(post, Event):
        uri = url_for('.get_event', event_id=post.id)
    else:
        uri = url_for('.get_post', post_id=post.id)

    post_dict['uri'] = uri
    return post_dict


def get_new_data(fields):
    """Validate and return POSTed data.

    `fields` should be a dict mapping model fields to the type of the
    fields, or None if nullable field, e.g.:
    ```
    fields = {
        'title': str,
        'published': bool,
        'image': (str, type(None))
    }
    ```
    """
    data = request.get_json()
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


# ----- POSTS ----- #

POST_FIELDS = {
    'title': str,
    'content': str,
    'published': bool,
    'image': (str, type(None)),
}


@mod.route('/posts', methods=['GET'])
def get_posts():
    """Get all posts.

    Returns all posts in a list in a json.
    """
    posts = Post.query.filter_by(type='post')
    response = [make_post_dict(post) for post in posts]
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
    data = get_new_data(POST_FIELDS)
    post = Post(**data)
    post.timestamp = datetime.datetime.now()
    db.session.add(post)
    db.session.commit()

    response = make_post_dict(post)
    return jsonify(response), 201


@mod.route('/posts/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    """Overwrite existing post.

    All fields are required, partial updates should use "PATCH" as
    method.
    """
    post = Post.query.get_or_404(post_id)
    data = get_new_data(POST_FIELDS)
    post.title = data['title']
    post.content = data['content']
    post.published = data['published']
    if data['image']:
        post.image = data['image']
    db.session.commit()

    response = make_post_dict(post)
    return jsonify(response)


@mod.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    """Delete a post."""
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return '', 204

# ----- END POSTS ----- #

# ----- EVENTS ----- #


EVENT_FIELDS = {
    'title': str,
    'content': str,
    'published': bool,
    'image': (str, type(None)),
    'start_time': str,
    'location': str,
}


@mod.route('/events', methods=['GET'])
def get_events():
    """Get all events.

    Returns a jsonified list of all events.
    """
    events = Event.query.all()
    response = [make_post_dict(event) for event in events]
    return jsonify(response)


@mod.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get specific event.

    Returns a jsonified event.
    """
    event = Event.query.get_or_404(event_id)
    response = make_post_dict(event)
    return jsonify(response)


@mod.route('/events', methods=['POST'])
def new_event():
    """Create a new event.

    Field requirements are defined with get_new_data().
    """
    data = get_new_data(EVENT_FIELDS)
    data['start_time'] = datetime.datetime.strptime(data['start_time'],
                                                    '%Y-%m-%dT%H:%M')
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

    data = get_new_data(EVENT_FIELDS)
    data['start_time'] = datetime.datetime.strptime(data['start_time'],
                                                    '%Y-%m-%dT%H:%M')
    event.title = data['title']
    event.content = data['content']
    event.published = data['published']
    event.start_time = data['start_time']
    event.location = data['location']
    event.image = data['image']
    db.session.commit()

    response = make_post_dict(event)
    return jsonify(response)


@mod.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete a post."""
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    return '', 204

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


@mod.route('/contact', methods=['GET'])
def get_contacts():
    contacts = [c.to_dict() for c in Contact.query.all()]
    return jsonify(contacts)


@mod.route('/contact', methods=['POST'])
def new_contact():
    fields = {
        'title': str,
        'first_name': str,
        'last_name': str,
        'email': str,
        'phone': (str, type(None)),
        'weight': int
    }
    data = get_new_data(fields)
    contact = Contact(**data)
    db.session.add(contact)
    db.session.commit()
    return jsonify(contact.to_dict())


@mod.route('/contact/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    db.session.delete(contact)
    db.session.commit()
    return '', 204
