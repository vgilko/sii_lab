from sqlalchemy.orm import relationship
from flask_login import UserMixin

from website import db


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150))
    url = db.Column(db.String(150))
    description = db.Column(db.String(4000))
    length = db.Column(db.Integer)
    release_date = db.Column(db.Date)
    blogger = db.Column(db.String(150))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video = db.Column(db.Integer, db.ForeignKey('video.id'))
    tag = db.Column(db.String(300))

    def __init__(self, video_id: int, tag: str):
        self.video = video_id
        self.tag = tag


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150))
    password = db.Column(db.String(150))

    likes = relationship('Likes')
    dislikes = relationship('Dislikes')

    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password

class Emotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emotion = db.Column(db.String(25))

    video = db.Column(db.Integer, db.ForeignKey('video.id'))

    def __init__(self, video_id: int, emotion: str):
        self.video = video_id
        self.emotion = emotion


class EmotionValue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String(1000))
    video = db.Column(db.Integer, db.ForeignKey('video.id'))

    def __init__(self, value, video):
        self.value = value
        self.video = video


class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    video = db.Column(db.Integer, db.ForeignKey('video.id'))

class Dislikes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    video = db.Column(db.Integer, db.ForeignKey('video.id'))

