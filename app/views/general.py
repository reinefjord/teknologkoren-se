#!/usr/bin/env python3
import datetime
from flask import Blueprint, request, redirect, render_template, url_for
from flask.ext.login import (current_user, login_user, logout_user,
                             login_required)
from app import app, login_manager
from app.forms import LoginForm, RegisterForm, CreatePostForm
from app.models import User, Page, Post

mod = Blueprint('general', __name__)


@login_manager.user_loader
def load_user(userid):
    return User.get(User.id == userid)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page


@app.route('/<page>/new-post', methods=['GET', 'POST'])
@login_required
def new_post(page):
    page_obj = Page.get(Page.name == page)
    form = CreatePostForm(request.form)
    if form.validate_on_submit():
        Post.create(title=form.title.data,
                    content=form.trix.data,
                    published=form.published.data,
                    timestamp=datetime.datetime.now(),
                    author=current_user.id,
                    page=page_obj.id)

    return render_template('new-post.html', page=page_obj, form=form)


@app.route('/edit-post/<slug>', methods=['GET', 'POST'])
@login_required
def edit_post(slug):
    post = Post.get(Post.slug == slug)
    form = CreatePostForm(request.form, post)
    return render_template('new-post.html',
                           page=None,
                           form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        User.create(email=form.email.data, password=form.password.data)
        return form.redirect('login')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if form.validate_on_submit():
        login_user(form.user, remember=form.remember.data)
        return form.redirect('index')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        return redirect(url_for('index'))
