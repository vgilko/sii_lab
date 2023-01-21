import json
import json
import os

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import current_user, login_required

from website.constants.emotions_constants import emotions, translate
from website.domain.models import SearchHistory
from website.dto.create_video_dto import CreateVideoDto
from website.service.measure_service import measures
from website.service.videos_service import add_video, read_all_videos, add_reaction, get_videos_like, find_similarities, \
    find_like_watched, likes, dislikes, get_video, get_filtered
from website.util.mapping import map_to_video_dto, map_to_emotions_dto, get_selected_emotions

videos = Blueprint('videos', __name__)


@videos.route("/add", methods=['GET', 'POST'])
def create_video():
    if request.method == 'POST':
        video_dto = map_to_video_dto(request.form)
        emotion_dto = map_to_emotions_dto(request.form)

        create_video_dto = CreateVideoDto(video_dto, emotion_dto)

        add_video(create_video_dto)

    return render_template("emotions.html")


@videos.route('/all', methods=['GET'])
def read_video():
    videos = read_all_videos()
    return render_template('print_video.html', videos=videos)


@login_required
@videos.route('/reaction', methods=["POST"])
def react_on_video():
    reaction = request.form.get('reaction')
    video = int(request.form.get('video'))

    if video is not None and reaction is not None:
        add_reaction(current_user.id, reaction, video)

    return redirect(url_for('videos.read_video'))


@videos.route('/like/<video_id>')
def get_like_videos(video_id: int):
    main_video = get_video(video_id)
    videos = get_videos_like(video_id)

    header = f'Видео, похожие на: {main_video["title"]}'

    return render_template('print_video.html', videos=videos, header=header)


@videos.route('/similarities')
@login_required
def get_similarities():
    is_prediction, videos = find_similarities(current_user.id)

    if is_prediction:
        header = 'Похожее на ранее просмотренное'
    else:
        header = 'Вы пока ничего не смотрели. Предлагаю посмотреть:'

    return render_template('print_video.html', videos=videos, header=header)


@videos.route('/like/watched')
@login_required
def get_like_watched():
    videos = find_like_watched(current_user.id)

    if len(videos) == 0:
        header = 'Добавьте хоть одно видео в любимые, чтобы я смог дать рекомендацию'
    else:
        header = 'Я подобрал вам видео на основе ваших любимых'

    return render_template('print_video.html', videos=videos, header=header)


@videos.route('/history')
@login_required
def get_history():
    find_all = SearchHistory.query.filter_by(user=current_user.id).order_by(SearchHistory.id.desc()).all()

    history = []
    for result in find_all:
        loaded_data = json.loads(result.search)
        loaded_data['id'] = result.id



        history.append(loaded_data)

        print(history)

    return render_template('history.html', history=history)


@videos.route('/from-history', methods=['GET'])
@login_required
def from_history():
    history_id = request.args.get('history')
    search = SearchHistory.query.filter_by(user=current_user.id, id=history_id).order_by(SearchHistory.id).first()

    args = json.loads(search.search)
    message, videos, selected_emotions = get_filtered(args, current_user)

    return render_template('filter_videos.html',
                           videos=videos,
                           header=message,
                           filters=args,
                           selected_emotions=selected_emotions,
                           emotions=emotions)


@videos.route('/filter', methods=['GET', 'POST'])
@login_required
def filter_video():
    if request.method == 'POST':
        request_args = request.form
        print(f"Request for filtering values. Request: {request_args}")

        message, videos, selected_emotions = get_filtered(request_args, current_user)

        return render_template('filter_videos.html',
                               videos=videos,
                               header=message,
                               filters=request_args,
                               selected_emotions=selected_emotions,
                               emotions=emotions)

    return render_template('filter_videos.html',
                           selected_emotions=[],
                           emotions=emotions)


@videos.route('/measures', methods=['GET'])
def get_measures():
    if not os.path.exists('website/static/images/measures.png'):
        measures()

    return render_template('measures.html')


@videos.route('/likes', methods=['GET'])
def get_liked():
    videos = likes(current_user.id)

    if len(videos) == 0:
        header = 'Кажется, вам еще ничего не понравилось... Посмотрите:'
        is_prediction, videos = find_similarities(current_user.id)
    else:
        header = 'Ваши любимые видео:'

    return render_template('print_video.html', videos=videos, header=header)


@videos.route('/dislikes', methods=['GET'])
def get_disliked():
    videos = dislikes(current_user.id)

    if len(videos) == 0:
        header = 'Фух, ни одного нелюбимого видео!'
    else:
        header = 'Видео, которые не понравились вам:'

    return render_template('print_video.html', videos=videos, header=header)
