from werkzeug.datastructures import ImmutableMultiDict

from website.dto.emotion_dto import EmotionDto
from website.dto.video_dto import VideoDto


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


def get_selected_emotions(emotion_dto: EmotionDto) -> [str]:
    emotions = []
    emotions_dict = vars(emotion_dto)
    for emotion in emotions_dict:
        emotions += emotions_dict.get(emotion)

    return emotions