import random
from string import ascii_letters, digits
from flask import Blueprint, request, redirect, render_template, url_for, abort
from flask_login import current_user, login_user, logout_user, login_required
from playhouse.flask_utils import get_object_or_404
from app import login_manager
from app.forms import LoginForm, AddUserForm, PasswordForm, EmailForm
from app.models import User
from app.util import send_email, ts


mod = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(userid):
    return User.get(User.id == userid)


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        user = form.user
        login_user(user, remember=form.remember.data)
        return form.redirect(url_for('blog.overview'))

    return render_template('users/login.html', form=form)


@mod.route('/logout/')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('blog.overview'))


@mod.route('/adduser/', methods=['GET', 'POST'])
@login_required
def adduser():
    form = AddUserForm(request.form)
    if form.validate_on_submit():
        password = ''.join(
                random.choice(ascii_letters + digits) for _ in range(30))

        User.create(
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                voice=form.voice.data,
                active=form.active.data,
                password=password,
                )

        return form.redirect(url_for('blog.overview'))

    return render_template('users/adduser.html', form=form)


@mod.route('/reset/', methods=['GET', 'POST'])
def reset():
    form = EmailForm()
    if form.validate_on_submit():
        user = form.user
        token = ts.dumps(user.email, salt='recover-key')

        recover_url = url_for('.reset_token', token=token, _external=True)

        email_body = render_template(
            'users/password_reset_email.jinja2',
            name=user.first_name,
            link=recover_url)

        send_email(user.email, email_body)

        return render_template('users/reset_sent.html', email=form.email.data)

    elif form.email.data is not None:
        return render_template('users/reset_sent.html', email=form.email.data)

    return render_template('users/reset.html', form=form)


@mod.route('/reset/<token>/', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = ts.loads(token, salt='recover-key', max_age=900)
    except:
        abort(404)

    form = PasswordForm()

    if form.validate_on_submit():
        user = get_object_or_404(User, (User.email == email))

        user.password = form.password.data
        if user.reset_password:
            user.reset_password = False
        user.save()

        return redirect(url_for('.login'))

    return render_template('users/reset_token.html', form=form)
