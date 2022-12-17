from flask import Blueprint, Flask, render_template, request, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.datastructures import ImmutableMultiDict

from website.domain.models import Video
from website.dto.create_video_dto import CreateVideoDto
from website.dto.emotion_dto import EmotionDto
from website.dto.video_dto import VideoDto
from website.service.measure_service import measures
from website.service.videos_service import add_video, read_all_videos, add_reaction, get_videos_like, find_similarities, \
    find_like_watched

videos = Blueprint('videos', __name__)


@videos.route("/add", methods=['GET', 'POST'])
def create_video():
    if request.method == 'POST':
        video_dto = map_to_video_dto(request.form)
        emotion_dto = map_to_emotions_dto(request.form)

        create_video_dto = CreateVideoDto(video_dto, emotion_dto)

        add_video(create_video_dto)

    return render_template("emotions.html")


@videos.route('/all', methods=['GET'])
def read_video():
    videos = read_all_videos()
    return render_template('print_video.html', videos=videos)


@login_required
@videos.route('/reaction', methods=["POST"])
def react_on_video():
    reaction = request.form.get('reaction')
    video = int(request.form.get('video'))

    if video is not None and reaction is not None:
        add_reaction(current_user.id, reaction, video)

    return redirect(url_for('videos.read_video'))


@videos.route('/like/<video>')
def get_like_videos(video: int):
    videos = get_videos_like(video)

    return render_template('print_video.html', videos=videos)


@videos.route('/similarities')
def get_similarities():
    videos = find_similarities(current_user.id)

    return render_template('print_video.html', videos=videos)


@videos.route('/like/watched')
def get_like_watched():
    videos = find_like_watched(current_user.id)

    return render_template('print_video.html', videos=videos)


@videos.route('/measures', methods=['GET'])
def get_measures():
    measures()

    return ""


def map_to_video_dto(request_data: dict) -> VideoDto:
    video_dto_fields = VideoDto.get_attributes_names()

    data = {}
    for field in request_data:
        if field in video_dto_fields:
            data[field] = request_data[field]

    return VideoDto(**data)


def map_to_emotions_dto(request_data: ImmutableMultiDict) -> EmotionDto:
    data = {}

    for field in request_data:
        if field in EmotionDto.get_attribute_names():
            data[field] = request_data.getlist(field)

    return EmotionDto(**data)


@videos.route("/", methods=["GET"])
def get_videos():
    return Video.query
