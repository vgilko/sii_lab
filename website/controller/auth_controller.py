from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from website import db
from website.controller.videos_controller import read_video
from website.domain.models import User

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_login = request.form.get('login')
        password = request.form.get('password')

        user = User.query.filter_by(login=user_login).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('videos.read_video'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('', methods=['GET'])
def default():
    if current_user:
        return read_video()

    return login()


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        user_login = request.form.get('login')
        password = request.form.get('password')

        user = User.query.filter_by(login=user_login).first()
        if user:
            flash('User already exists.', category='error')
        else:
            new_user = User(login=user_login, password=generate_password_hash(password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()

            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('videos.read_video'))

    return render_template("sign_up.html", user=current_user)
