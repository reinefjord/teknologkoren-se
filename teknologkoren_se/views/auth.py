from flask import jsonify, request
from werkzeug.security import check_password_hash
from teknologkoren_se import app, token_auth


@token_auth.verify_password
def verify_password(username, password):
    if username in app.config['USERS']:
        return check_password_hash(app.config['USERS'].get(username), password)


@token_auth.error_handler
def auth_error():
    if request.path.startswith('/api'):
        return jsonify({"error": "Unauthorized"})
    else:
        return "Unauthorized"
