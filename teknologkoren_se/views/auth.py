from flask import jsonify, request
from teknologkoren_se import app, token_auth


@token_auth.verify_token
def verify_token(token):
    if token in app.config['TOKENS']:
        return True
    return False


@token_auth.error_handler
def auth_error():
    if request.path.startswith('/api'):
        return jsonify({"error": "Unauthorized"})
    else:
        return "Unauthorized"
