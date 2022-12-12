import datetime
import logging
import string

import pymorphy2
import requests
from bs4 import BeautifulSoup
from requests import Response

from website import db
from website.domain.models import Video, Tag
from website.dto.create_video_dto import CreateVideoDto
from website.dto.video_dto import VideoDto
from website.service.emotion_service import create_emotion

analyzer = pymorphy2.MorphAnalyzer()


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


def insert_tags(video_id, tags):
    for tag in tags:
        db.session.add(Tag(video_id, tag.lower()))
        db.session.flush()

def build_video(response: Response, video_dto: VideoDto):
    description, keywords, title, blogger = get_data_from_youtube(response)

    video = Video(**video_dto.__dict__)
    video.title = title
    video.description = make_description_normal(description)
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


def make_description_normal(description: str) -> str:
    return normalize_sentence(delete_punctuation(description))


def normalize_sentence(sentence: str) -> str:
    words = []

    for word in sentence.split():
        p = analyzer.parse(word)[0]
        normal_form_word = p.normal_form
        words.append(normal_form_word)
    normalised_description = ' '.join(words)
    return normalised_description


def delete_punctuation(video_description: str):
    punctuation = string.punctuation
    description = video_description
    for p in punctuation:
        description = description.replace(p, '')
    return description
