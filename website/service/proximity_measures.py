from numpy import dot
from numpy.linalg import norm

from website.service.emotion_service import extract_base_emotions_vector
from website.util.text_util import make_description_normal, clean_string


def jaccard(list1, list2):
    intersection = len(set(list1).intersection(list2))
    union = len(set(list1).union(list2))

    return 0 if union == 0 else float(intersection) / union


def cosine(list1, list2):
    return dot(list1, list2) / (norm(list1) * norm(list2))


def jaccard_description(description1: str, description2):
    list1 = make_description_normal(clean_string(description1)).split(' ')
    list2 = make_description_normal(clean_string(description2)).split(' ')

    return jaccard(list1, list2)


def is_emotions_similar(emotions1, emotions2):
    return 1 - cosine(emotions1, emotions2) < 0.4


def generalize_measure(video_1: dict, video_2: dict) -> float:
    jaccard_tags_value = jaccard(video_1['tags'], video_2['tags'])
    jaccard_description_value = jaccard_description(video_1['description'], video_2['description'])
    cosine_child_emotions = cosine(video_1['emotions'], video_2['emotions'])
    cosine_grand_emotions = cosine(extract_base_emotions_vector(video_1['emotions']),
                                   extract_base_emotions_vector(video_2['emotions']))

    return (jaccard_tags_value + jaccard_description_value) + (cosine_grand_emotions + cosine_child_emotions)
