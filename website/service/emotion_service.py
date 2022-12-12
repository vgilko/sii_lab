from website import db
from website.constants.emotions_constants import sorted_child_emotions
from website.domain.models import Emotion, EmotionValue
from website.dto.emotion_dto import EmotionDto


def create_emotion(video_id: int, emotion_dto: EmotionDto):
    add_emotions(emotion_dto, video_id)
    vectorize_emotions(emotion_dto, video_id)

    db.session.flush()


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