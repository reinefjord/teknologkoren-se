from flask import Blueprint, render_template
from flask_login import current_user, login_required

mod = Blueprint('intranet', __name__, url_prefix='/intranet')


@mod.before_request
@login_required
def before_request():
    pass


@mod.route('/')
def index():
    return render_template('intranet.html')


@mod.route('/profile/')
def my_profile():
    pass


@mod.route('/profile/<int:id>')
def profile(id):
    pass
