class EmotionDto:
    anger: []
    sadness: []
    astonishment: []
    joy: []
    love: []
    fear: []

    def __init__(self, **entries):
        self.__dict__.update(entries)


    @staticmethod
    def get_attribute_names() -> [str]:
        return 'anger', 'sadness', 'astonishment', 'joy', 'love', 'fear'