from datetime import date


class VideoDto:
    url: str
    release_date: date
    length: int

    def __init__(self, **entries):
        self.__dict__.update(entries)

    @staticmethod
    def get_attributes_names() -> [str]:
        return 'url', 'release_date', 'length'
