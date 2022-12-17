import datetime
import logging

import requests
from bs4 import BeautifulSoup
from requests import Response

from website import db
from website.domain.models import Video, Tag, Likes, Dislikes
from website.dto.create_video_dto import CreateVideoDto
from website.dto.video_dto import VideoDto
from website.service.emotion_service import create_emotion, get_emotions_vector, extract_child_emotions
from website.service.proximity_measures import generalize_measure
from website.util.text_util import normalize_sentence


def add_video(create_video_dto: CreateVideoDto):
    response = requests.get(create_video_dto.video_dto.url)

    if response.status_code == 200:
        video_id = create_video(create_video_dto, response)
        create_emotion(video_id, create_video_dto.emotion_dto)

        db.session.commit()


def create_video(create_video_dto: CreateVideoDto, response: Response):
    video, tags = build_video(response, create_video_dto.video_dto)
    video.release_date = datetime.date.fromisoformat(video.release_date)

    db.session.add(video)
    db.session.flush()

    tags = tags.split(', ')
    insert_tags(video.id, tags)

    logging.info('Added new video: ', video)

    return video.id


def find_similarities(user_id: int):
    likes, unwatched_videos = get_likes_and_unwatched_videos(user_id)
    liked_videos = get_video_by_ids(likes)

    return find_best_matches_for_unwatched(liked_videos, unwatched_videos)


def find_like_watched(user_id: int):
    likes = get_liked_video_ids(user_id)
    liked_videos = get_video_by_ids(likes)

    videos = read_all_videos()

    measures = []
    for liked_idx, liked_video in enumerate(liked_videos):
        for video_idx, video in enumerate(videos):
            if video['id'] not in likes:
                match_value = generalize_measure(liked_video, video)
                measures.append((match_value, video_idx, video))

    sorted_by_measure = sorted(measures, key=lambda x: x[0])

    returning_videos_ids = []
    videos_result = []
    for row in sorted_by_measure:
        video_id = row[1]
        if video_id not in returning_videos_ids:
            returning_videos_ids.append(video_id)
            videos_result.append(row[2])

    return videos_result


def find_best_matches_for_unwatched(liked_videos, unwatched_videos):
    general_measures = []
    for unwatched_idx, video in enumerate(unwatched_videos):
        best_match = find_best_match_from_likes(liked_videos, video)
        general_measures.append((best_match, unwatched_idx, video))

    sorted_by_measure = sorted(general_measures, key=lambda x: x[0], reverse=True)
    extracted_video = [row[2] for row in sorted_by_measure]

    return extracted_video


def find_best_match_from_likes(liked_videos, video):
    measures = []
    for liked_idx, liked_video in enumerate(liked_videos):
        measure_result = generalize_measure(liked_video, video)
        measures.append((measure_result, liked_idx))

    sorted_by_measure = sorted(measures, key=lambda x: x[0], reverse=True)
    best_match = sorted_by_measure[0][0]

    return best_match


def get_likes_and_unwatched_videos(user_id):
    liked_videos_ids = get_liked_video_ids(user_id)

    videos = read_all_videos()
    disliked_videos_ids = get_disliked_video_ids(user_id)

    unwatched_videos = [video for video in videos if
                        video['id'] not in set(disliked_videos_ids).union(liked_videos_ids)]

    return liked_videos_ids, unwatched_videos


def get_disliked_video_ids(user_id):
    disliked_videos_ids = db.session.query(Dislikes.video).filter_by(user=user_id).all()
    disliked_videos_ids = [row[0] for row in disliked_videos_ids]

    return disliked_videos_ids


def get_liked_video_ids(user_id):
    liked_videos_ids = db.session.query(Likes.video).filter_by(user=user_id).all()
    liked_videos_ids = [row[0] for row in liked_videos_ids]

    return liked_videos_ids


def get_video_by_ids(video_ids: [int]):
    videos = Video.query.filter(Video.id.in_(video_ids)).all()

    mapped_videos = []
    for video in videos:
        mapped_videos.append(get_data_for_video(video))

    return mapped_videos


def get_videos_like(video_id: int):
    videos = read_all_videos()

    main_video = get_video(video_id)

    comparison_result = []
    videos_map = {}
    for video in videos:
        if video['id'] != video_id:
            measure_result = generalize_measure(main_video, video)
            videos_map[video['id']] = video

            comparison_result.append((measure_result, video['id']))

    sorted_by_measure = sorted(comparison_result, key=lambda x: x[0], reverse=True)

    result = []
    for video in sorted_by_measure:
        if int(video[1]) != int(video_id):
            result.append(videos_map.get(video[1]))

    return result


def add_reaction(user: id, reaction: str, video: int):
    is_reacted = is_user_reacted_on_video(user, video)

    if not is_reacted:
        if reaction == 'like':
            db.session.add(Likes(video, user))
            db.session.commit()
        elif reaction == 'dislike':
            db.session.add(Dislikes(video, user))
            db.session.commit()


def is_user_reacted_on_video(user, video):
    like = Likes.query.filter_by(video=video, user=user).first()
    dislike = Dislikes.query.filter_by(video=video, user=user).first()
    return dislike is not None or like is not None


def get_video(video_id: int):
    video = Video.query.filter_by(id=video_id).first()

    return get_data_for_video(video)


def read_all_videos():
    videos = Video.query.order_by(Video.id).all()

    result = []
    for video in videos:
        unpacked_video = get_data_for_video(video)

        result.append(unpacked_video)

    return result


def get_data_for_video(video: Video):
    unpacked_video = vars(video)

    unpacked_video['likes'] = get_video_likes(video)
    unpacked_video['dislikes'] = get_video_dislikes(video)
    unpacked_video['tags'] = get_video_tags(video)
    unpacked_video['emotions'] = get_emotions_vector(video.id)
    unpacked_video['child_emotions'] = extract_child_emotions(unpacked_video['emotions'])
    unpacked_video['child_emotions_ru'] = extract_child_emotions(unpacked_video['emotions'])

    return unpacked_video


def get_video_dislikes(video):
    return db.session.query(Dislikes).filter_by(video=video.id).count()


def get_video_likes(video):
    return db.session.query(Likes).filter_by(video=video.id).count()


def get_video_tags(video):
    tags = Tag.query.with_entities(Tag.tag).filter_by(video=video.id).all()
    result = []
    for tag in tags:
        result.append(tag.tag)

    return result


def insert_tags(video_id, tags):
    for tag in tags:
        db.session.add(Tag(video_id, tag.lower()))
        db.session.flush()


def build_video(response: Response, video_dto: VideoDto):
    description, keywords, title, blogger = get_data_from_youtube(response)

    video = Video(**video_dto.__dict__)
    video.title = title
    # video.description = make_description_normal(description)
    video.blogger = blogger

    return video, normalize_sentence(keywords)


def get_data_from_youtube(response: Response):
    soup = BeautifulSoup(response.content, 'html.parser')

    title = extract_title(soup)
    description = extract_description(soup)
    keywords = extract_keywords(soup)
    blogger = extract_blogger(soup)

    return description, keywords, title, blogger


def extract_blogger(soup) -> str:
    return soup.find('link', {'itemprop': 'name'}).get('content')


def extract_title(soup):
    return extract_content_from_meta(soup, 'title')


def extract_description(soup):
    return extract_content_from_meta(soup, 'description')


def extract_keywords(soup):
    return extract_content_from_meta(soup, 'keywords')


def extract_content_from_meta(soup, meta_name: str) -> str:
    meta = soup.find('meta', attrs={'name': f'{meta_name}'})
    content = meta.get('content')
    return content
