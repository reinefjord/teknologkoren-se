from flask import Blueprint, render_template
from flask.ext.login import login_required

mod = Blueprint('intranet', __name__, url_prefix='/intranet')


@mod.route('/')
@login_required
def index():
    return render_template('intranet.html')
