import logging
from os import path

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
# DB_NAME = "database.sqlite"
DB_NAME = "videos"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'key'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql+psycopg2:///{DB_NAME}'
    db.init_app(app)

    from website.controller.videos_controller import videos
    from website.controller.auth_controller import auth

    app.register_blueprint(videos, url_prefix='/video')
    app.register_blueprint(auth, url_prefix='/')

    from website.domain.models import Video, User, SearchHistory

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    configure_logging(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app


def configure_logging(app: Flask):
    logging.basicConfig(format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

    if app.debug:
        logging.getLogger().setLevel(logging.DEBUG)


def create_database(app):
    # if not path.exists('website/' + DB_NAME):
    with app.app_context():
        db.create_all()
        db.session.commit()
