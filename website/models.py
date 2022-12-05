from sqlalchemy.orm import relationship

from . import db


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vectory = db.Column(db.String(4000))


class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    href = db.Column(db.String(150))
    description = db.Column(db.String(4000))
    length = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True))

    category = db.Column(db.Integer, db.ForeignKey('category.id'))
    blogger = db.Column(db.Integer, db.ForeignKey("blogger.id"))


class Blogger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    videos = relationship("Video")


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video = db.Column(db.Integer, db.ForeignKey('video.id'))
    tags = db.Column(db.String(300))


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))

    likes = relationship('Likes')


class Likes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('user.id'))
    like = db.Column(db.Integer, db.ForeignKey('video.id'))

