import json

import numpy as np

from website import db
from website.constants.emotions_constants import sorted_child_emotions, get_grand_emotion_by_child, \
    get_child_emotion_by_index, grand_emotions
from website.domain.models import Emotion, EmotionValue
from website.dto.emotion_dto import EmotionDto


def create_emotion(video_id: int, emotion_dto: EmotionDto):
    add_emotions(emotion_dto, video_id)
    vectorize_emotions(emotion_dto, video_id)

    db.session.flush()


def get_emotions_vector(video_id: int):
    string_emotions = EmotionValue.query.with_entities(EmotionValue.value).filter_by(video=video_id).first()[0]

    return np.array(json.loads(string_emotions))


def add_emotions(emotion_dto, video_id: int):
    emotion_dto_dict = vars(emotion_dto)
    for base_emotion in emotion_dto_dict:
        for emotion in emotion_dto_dict[base_emotion]:
            db.session.add(Emotion(video_id, emotion))


def vectorize_emotions(emotion_dto: EmotionDto, video_id: int):
    emotions = []
    emotion_dto_dict = vars(emotion_dto)
    vector = []

    for base_emotion in emotion_dto_dict:
        for emotion in emotion_dto_dict[base_emotion]:
            emotions.append(emotion)

    for emotion in sorted_child_emotions:
        value = 0
        if emotion in emotions:
            value = 1
        vector.append(value)

    db.session.add(EmotionValue(str(vector), video_id))


def get_vector_of_base_emotions_by(video_id: int):
    emotions_vector = get_emotions_vector(video_id)

    return extract_base_emotions_vector(emotions_vector)


def extract_base_emotions_vector(emotions_vector: np.array):
    grand_emotions_values = {}

    for idx, emotion_value in enumerate(emotions_vector):
        grand_emotion = get_grand_emotion_by_child(get_child_emotion_by_index(idx))

        if grand_emotion in grand_emotions_values.keys():
            grand_emotions_values[grand_emotion] += emotion_value
        else:
            grand_emotions_values[grand_emotion] = emotion_value

    grand_emotions_vector = []
    for grand_emotion in grand_emotions:
        emotion_value = grand_emotions_values[grand_emotion]
        grand_emotions_vector.append(emotion_value)

    return np.array(grand_emotions_vector)


def extract_child_emotions(emotions_vector: np.array):
    result = []
    for idx, emotion in enumerate(emotions_vector):
        if emotion > 0:
            result.append(sorted_child_emotions[idx])

    return list(set(result))
