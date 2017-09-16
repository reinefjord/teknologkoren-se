from flask import abort, Blueprint, jsonify, request, url_for
from teknologkoren_se import db
from teknologkoren_se.models import Post, Event


mod = Blueprint('api', __name__, url_prefix='/api')


def make_post_dict(post):
    post_dict = post.to_dict()

    if isinstance(post, Event):
        uri = url_for('.get_event', event_id=post.id)
    else:
        uri = url_for('.get_post', post_id=post.id)

    post_dict['uri'] = uri
    return post_dict


@mod.route('/posts', methods=['GET'])
def get_posts():
    posts = Post.query.filter_by(type='post')
    response = {'posts': [make_post_dict(post) for post in posts]}
    return jsonify(response)


@mod.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    # None if no post (not event) with that id (return 404), raises
    # exception if multiple found.
    post = Post.query.filter_by(type='post', id=post_id).one_or_none()
    if post:
        response = make_post_dict(post)
        return jsonify(response)
    abort(404)


@mod.route('/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    response = {'events': [make_post_dict(event) for event in events]}
    return jsonify(response)


@mod.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    response = make_post_dict(event)
    return jsonify(response)
