from flask import Blueprint, render_template, request, jsonify
from werkzeug.datastructures import ImmutableMultiDict

from website.domain.models import Video
from website.dto.create_video_dto import CreateVideoDto
from website.dto.emotion_dto import EmotionDto
from website.dto.video_dto import VideoDto
from website.service.videos_service import add_video

videos = Blueprint('videos', __name__)


@videos.route("/add", methods=['GET', 'POST'])
def create_video():
    if request.method == 'POST':
        video_dto = map_to_video_dto(request.form)
        emotion_dto = map_to_emotions_dto(request.form)

        create_video_dto = CreateVideoDto(video_dto, emotion_dto)

        add_video(create_video_dto)

    return render_template("emotions.html")


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
