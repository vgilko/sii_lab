from website.dto.emotion_dto import EmotionDto
from website.dto.video_dto import VideoDto


class CreateVideoDto:
    video_dto: VideoDto
    emotion_dto: EmotionDto

    def __init__(self, video_dto: VideoDto, emotion_dto: EmotionDto):
        self.video_dto = video_dto
        self.emotion_dto = emotion_dto
