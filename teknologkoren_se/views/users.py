import random
from string import ascii_letters, digits
from flask import (Blueprint, request, redirect, render_template, url_for,
                   abort, flash)
from flask_login import current_user, login_user, logout_user, login_required
from playhouse.flask_utils import get_object_or_404
from itsdangerous import SignatureExpired
from teknologkoren_se import login_manager
from teknologkoren_se.forms import LoginForm, AddUserForm, PasswordForm, EmailForm
from teknologkoren_se.models import User
from teknologkoren_se.util import send_email, ts


mod = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(userid):
    return User.get(User.id == userid)


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)

    if current_user.is_authenticated:
        return form.redirect('intranet.index')

    if form.validate_on_submit():
        user = form.user
        login_user(user, remember=form.remember.data)
        return form.redirect('intranet.index')
    elif form.email.errors or form.password.errors:
        flash("Sorry, your email address or password was incorrect.", 'error')

    return render_template('users/login.html', form=form)


@mod.route('/logout/')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('blog.index'))


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
                phone=form.phone.data,
                password=password,
                )

        return form.redirect('blog.index')

    return render_template('users/adduser.html', form=form)


def verify_email(user, email):
    token = ts.dumps([user.id, email], 'verify-email')

    verify_link = url_for('users.verify_token', token=token, _external=True)

    email_body = render_template(
            'users/email_verification.jinja2',
            name=user.first_name,
            link=verify_link)

    send_email(email, email_body)


@mod.route('/verify/<token>/')
def verify_token(token):
    try:
        user_id, email = ts.loads(token, salt='verify-email', max_age=900)
    except SignatureExpired:
        flash("Sorry, the link has expired. Please try again.", 'error')
        return redirect(url_for('blog.index'))
    except:
        abort(404)

    user = get_object_or_404(User, User.id == user_id)

    user.email = email
    user.save()

    flash("{} is now verified!".format(email), 'success')
    return redirect(url_for('blog.index'))


@mod.route('/reset/', methods=['GET', 'POST'])
def reset():
    form = EmailForm()

    reset_flash = \
        "A password reset link valid for one hour has been sent to {}."

    if form.validate_on_submit():
        user = form.user
        token = ts.dumps(user.id, salt='recover-key')

        recover_url = url_for('.reset_token', token=token, _external=True)

        email_body = render_template(
            'users/password_reset_email.jinja2',
            name=user.first_name,
            link=recover_url)

        send_email(user.email, email_body)

        flash(reset_flash.format(form.email.data), 'info')
        return redirect(url_for('.login'))

    elif form.email.data:
        flash(reset_flash.format(form.email.data), 'info')
        return redirect(url_for('.login'))

    elif form.errors:
        flash("Please enter your email.", 'error')

    return render_template('users/reset.html', form=form)


@mod.route('/reset/<token>/', methods=['GET', 'POST'])
def reset_token(token):
    expired = "Sorry, the link has expired. Please try again."
    invalid = "Sorry, the link appears to be broken. Please try again."

    try:
        data, timestamp = ts.loads(token, salt='recover-key', max_age=3600,
                                   return_timestamp=True)
        user = User.get(User.id == data)
    except SignatureExpired:
        flash(expired, 'error')
        return redirect(url_for('.login'))
    except:
        flash(invalid, 'error')
        return redirect(url_for('.login'))

    if timestamp < user._password_timestamp:
        flash(expired, 'error')
        return redirect(url_for('.login'))

    form = PasswordForm()

    if form.validate_on_submit():
        user.password = form.password.data
        user.save()
        flash("Your password has been reset!", 'success')
        return redirect(url_for('.login'))

    return render_template('users/reset_token.html', form=form)
