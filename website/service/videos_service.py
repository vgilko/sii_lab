import datetime
import json
import logging

import requests
import sqlalchemy
from bs4 import BeautifulSoup
from requests import Response
from werkzeug.datastructures import ImmutableMultiDict

from website import db
from website.domain.Filter import Filter
from website.domain.models import Video, Tag, Likes, Dislikes, SearchHistory, User
from website.dto.create_video_dto import CreateVideoDto
from website.dto.emotion_dto import EmotionDto
from website.dto.video_dto import VideoDto
from website.service.emotion_service import create_emotion, get_emotions_vector, extract_child_emotions, \
    vectorize_emotions, get_russian_names
from website.service.proximity_measures import generalize_measure, is_emotions_similar
from website.util.mapping import map_to_emotions_dto
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

    if len(liked_videos) == 0:
        videos = read_all_videos()
        return False, sorted(videos, key=lambda x: x['likes'], reverse=True)
    else:
        return True, find_best_matches_for_unwatched(liked_videos, unwatched_videos)


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

    sorted_by_measure = sorted(measures, key=lambda x: x[0], reverse=True)

    returning_videos_ids = []
    videos_result = []
    for row in sorted_by_measure:
        video_id = row[1]
        if video_id not in returning_videos_ids:
            returning_videos_ids.append(video_id)
            videos_result.append(row[2])

    return videos_result


def get_filtered(args: ImmutableMultiDict, user: User = None) -> (str, [dict]):
    if user is not None:
        save_search(user.id, args)

    message = ''
    emotion_dto = map_to_emotions_dto(args)
    filters = build_filters_list(args)

    print(f"Built filters {filters.non_strict_filters, filters.strict_filters}")

    videos = []

    filtered_videos = get_by_filter(filters)
    if len(filtered_videos) == 0:
        print(f'There is no videos for parameters {args}. Expanding border for request')

        filters = build_filters_list(args, expand_borders=True)
        filtered_videos = get_by_filter(filters)

        if len(filtered_videos) != 0:
            print(f'There is no videos for {args} after borders expanding too')
            message = 'Строгие критерии поиска, я немного сдвинул границы, чтобы порекомендовать вам видео:'
            videos = filtered_videos

        if len(filtered_videos) == 0:
            message = 'Увы, по вашему запросу ничего не нашлось. Рекомедую посмотреть:'
            videos = read_all_videos()
    else:
        print(f"Finding videos similar to {filtered_videos}")
        videos = extract_similar(filtered_videos, emotion_dto)

        if len(videos) != 0 and message == '':
            message = 'По вашему запросу найдены видео:'
            videos = filtered_videos + videos
        else:
            print(f'There is no similar videos for videos {filtered_videos}')
            videos = filtered_videos

    return message, videos, get_selected_emotions(emotion_dto)


def save_search(user_id: int, args: ImmutableMultiDict):
    string_args = json.dumps(args)
    history = SearchHistory(user_id, string_args)

    db.session.add(history)
    db.session.flush()


def get_selected_emotions(emotion_dto: EmotionDto) -> [str]:
    emotions = []
    emotions_dict = vars(emotion_dto)
    for emotion in emotions_dict:
        emotions += emotions_dict.get(emotion)

    return emotions


def get_by_filter(filters: Filter):
    comparator = build_comparator_for_filtering(filters)

    videos = db.session.query(Video).filter(comparator).all()

    return [get_data_for_video(video) for video in videos]


def build_comparator_for_filtering(filters):
    comparator = None
    if len(filters.non_strict_filters) != 0:
        comparator = sqlalchemy.or_(*filters.non_strict_filters)

    if len(filters.strict_filters) != 0:
        comparator_strict = sqlalchemy.and_(*filters.strict_filters)

        if comparator is None:
            comparator = comparator_strict
        else:
            comparator = comparator & comparator_strict

    return comparator


def extract_similar(videos: [dict], emotion_dto: EmotionDto) -> [dict]:
    # TODO: приведение к видео, сравнение по generalize мере
    #       сравнение векторов базовых эмоций:
    #           * Сложение всех векторов найденных видосов и их с вектором эмоций из поиска

    output = []
    for video in videos:
        if is_emotions_similar(video['emotions'], vectorize_emotions(emotion_dto)):
            output.append(video)

    return output


def build_filters_list(args, expand_borders=False) -> Filter:
    non_strict_filters = []

    blogger = args.get('blogger')
    title = args.get('title')
    time_lower = args.get('time_lower_border')
    time_upper = args.get('time_upper_border')
    start_date = args.get('start_date')
    end_date = args.get('end_date')

    strict_filters = build_date_filters(start_date, end_date, expand_borders)
    strict_filters += get_time_filters(time_lower, time_upper, expand_borders)

    if blogger != '':
        blogger = f'%{blogger}%'
        non_strict_filters.append(Video.blogger.ilike(blogger))

    if title != '':
        title = f'%{title}%'
        non_strict_filters.append(Video.title.ilike(title))

    print(f'Filters: strict: {strict_filters}, non strict: {non_strict_filters}')

    return Filter(non_strict_filters, strict_filters)


def build_date_filters(start_date, end_date, expand_border=False):
    start_date_obj = None
    end_date_obj = None

    if start_date == '' and end_date == '':
        return []

    if start_date != '':
        start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start_date_obj = datetime.datetime.now()

    if end_date != '':
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end_date_obj = datetime.datetime.now()

    if start_date_obj > end_date_obj:
        start_date, end_date = end_date, start_date

    if expand_border:
        days_delta = get_days_delta(start_date_obj, end_date_obj)

        if days_delta < 1:
            days_delta = 1
        else:
            days_delta *= 0.3

        result_date_delta = datetime.timedelta(days=days_delta)

        if start_date != '':
            start_date_obj -= result_date_delta
        if end_date != '':
            end_date_obj += result_date_delta

    filters = []
    if start_date != '':
        filters.append(Video.release_date >= start_date_obj)
    if end_date != '':
        filters.append(Video.release_date <= end_date_obj)

    print(f"Dates for building filters {start_date_obj} - {end_date_obj}")

    return filters


def get_days_delta(start_date_obj, end_date_obj):
    time_delta = end_date_obj - start_date_obj
    days_delta = time_delta.days
    return abs(days_delta)


def get_time_filters(time_lower, time_upper, expand_border=False):
    if time_lower == '' or time_upper == '':
        return []

    time_lower = int(time_lower)
    time_upper = int(time_upper)
    filters = []

    if time_lower > time_upper:
        time_lower, time_upper = time_upper, time_lower

    time_delta = (time_upper - time_lower) * 0.1

    if expand_border:
        time_lower -= time_delta
        time_upper += time_delta

    if time_lower != '':
        filters.append(Video.length >= int(time_lower) * 60)
    if time_upper != '':
        filters.append(Video.length <= int(time_upper) * 60)

    return filters


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


def likes(user_id: int):
    videos = get_video_by_ids(get_liked_videos(user_id))
    return videos


def get_liked_videos(user_id):
    liked_videos = Likes.query.filter_by(user=user_id).all()
    return [row.video for row in liked_videos]


def get_disliked_videos(user_id):
    disliked_videos = Dislikes.query.filter_by(user=user_id).all()
    return [row.video for row in disliked_videos]


def dislikes(user_id: int):
    videos = get_video_by_ids(get_disliked_videos(user_id))
    return videos


def get_data_for_video(video: Video):
    unpacked_video = vars(video)

    unpacked_video['likes'] = get_video_likes(video)
    unpacked_video['dislikes'] = get_video_dislikes(video)
    unpacked_video['tags'] = get_video_tags(video)
    unpacked_video['emotions'] = get_emotions_vector(video.id)
    unpacked_video['child_emotions'] = extract_child_emotions(unpacked_video['emotions'])
    unpacked_video['child_emotions_ru'] = get_russian_names(unpacked_video['child_emotions'])

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
