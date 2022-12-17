import numpy as np
from matplotlib import pyplot as plt

from website.service.emotion_service import extract_base_emotions_vector
from website.service.proximity_measures import jaccard, cosine, jaccard_description, generalize_measure
from website.service.videos_service import read_all_videos


def measures():
    videos = read_all_videos()
    fig, ax = plt.subplots(2, 3)
    matrix = test_measure(videos, test_jaccard_tags)
    axis = np.arange(0, matrix.shape[0])
    ax[0, 0].pcolormesh(axis, axis, matrix)
    ax[0, 0].set_title('Жаккард по тэгам', fontsize=10)

    matrix = test_measure(videos, test_jaccard_description)
    ax[0, 1].pcolormesh(axis, axis, matrix)
    change_plot_pos_y(ax[0, 1], 0.05)
    ax[0, 1].set_title('Жаккард по описанию', fontsize=10)

    matrix = test_measure(videos, test_cosine_emotions)
    ax[0, 2].pcolormesh(axis, axis, matrix)
    ax[0, 2].set_title('Косинусная \nвектор сложных эмоций', fontsize=10)

    matrix = test_measure(videos, test_cosine_base_emotions)
    ax[1, 0].pcolormesh(axis, axis, matrix)
    change_plot_pos_y(ax[1, 0], -0.05)
    ax[1, 0].set_title('Косинусная \nвектор базовых эмоций', fontsize=10)

    matrix = test_measure(videos, test_generalize_measure)
    ax[1, 2].pcolormesh(axis, axis, matrix)
    change_plot_pos_y(ax[1, 2], -0.05)
    ax[1, 2].set_title('Обобщающая мера', fontsize=10)

    fig.delaxes(ax[1, 1])

    plt.show()


def change_plot_pos_y(plot, move_coeff: float):
    pos = plot.get_position()
    pos.y0 += move_coeff
    pos.y1 += move_coeff
    plot.set_position(pos)


def test_generalize_measure(videos, measure_matrix):
    calculation_lamda = lambda video_1, video_2: generalize_measure(video_1, video_2)
    calculate_measure(videos, measure_matrix, calculation_lamda)


def test_cosine_base_emotions(videos, measure_matrix):
    calculation_lamda = lambda video_1, video_2: cosine(extract_base_emotions_vector(video_1['emotions']),
                                                        extract_base_emotions_vector(video_2['emotions']))
    calculate_measure(videos, measure_matrix, calculation_lamda)


def test_cosine_emotions(videos, measure_matrix):
    calculation_lamda = lambda video_1, video_2: cosine(video_1['emotions'], video_2['emotions'])
    calculate_measure(videos, measure_matrix, calculation_lamda)


def test_jaccard_description(videos, measure_matrix):
    calculation_lamda = lambda video_1, video_2: jaccard_description(video_1['description'],
                                                                     video_2['description'])
    calculate_measure(videos, measure_matrix, calculation_lamda)


def test_measure(videos, measure_lamda):
    measure_matrix = build_measure_matrix(videos)
    measure_lamda(videos, measure_matrix)
    return measure_matrix


def test_jaccard_tags(videos, measure_matrix):
    calculation_lambda = lambda video_1, video_2: jaccard(video_1['tags'], video_2['tags'])
    calculate_measure(videos, measure_matrix, calculation_lambda)


def build_measure_matrix(videos):
    measure_matrix = np.zeros(len(videos) ** 2)
    measure_matrix = measure_matrix.reshape((len(videos), len(videos)))
    return measure_matrix


def calculate_measure(videos: list[dict], measure_matrix, calculation_lamda):
    for idx_i, video in enumerate(videos):
        for idx_j, second_video in enumerate(videos):
            measure_matrix[idx_i, idx_j] = calculation_lamda(video, second_video)
