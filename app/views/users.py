from flask import Blueprint, request, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
from app import login_manager
from app.forms import LoginForm, RegisterForm
from app.models import User


mod = Blueprint('users', __name__)


@login_manager.user_loader
def load_user(userid):
    return User.get(User.id == userid)


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        login_user(form.user, remember=form.remember.data)
        return form.redirect(url_for('index.index'))

    return render_template('login.html', form=form)


@mod.route('/logout/')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('index.index'))


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(email=form.email.data, password=form.password.data)
        return form.redirect(url_for('index.index'))

    return render_template('register.html', form=form)
