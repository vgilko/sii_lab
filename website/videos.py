import string
from urllib import response

from flask import Blueprint, render_template, request, jsonify
import pymorphy2

from website import db
from website.models import Video

videos = Blueprint('videos', __name__)

analyzer = pymorphy2.MorphAnalyzer()


@videos.route("/add", methods=['GET', 'POST'])
def add_video():
    if request.method == 'POST':
        video = Video(**request.form.to_dict())
        process_video(video)

        return jsonify(success=True)
    else:
        return render_template("add_video.html")


@videos.route("/", methods=["GET"])
def get_videos():
    return Video.query


def process_video(video: Video):
    words = []

    description = delete_punctuation(video)

    normalised_description = normalize_sentence(description, words)
    video.description = normalised_description

    db.session.add(video)
    res = db.session.commit()
    print(res)


def normalize_sentence(description, words):
    for word in description.split():
        p = analyzer.parse(word)[0]
        normal_form_word = p.normal_form
        words.append(normal_form_word)
    normalised_description = ' '.join(words)
    return normalised_description


def delete_punctuation(video):
    punctuation = string.punctuation
    description = video.description
    for p in punctuation:
        description = description.replace(p, '')
    return description
