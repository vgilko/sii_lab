import re
import string

import en_core_web_sm
import nltk
import pymorphy2
from nltk import PorterStemmer, WordNetLemmatizer

analyzer = pymorphy2.MorphAnalyzer()
nlp = en_core_web_sm.load()
nltk.download('stopwords')


def clean_string(text, stem="None"):
    text = text.lower()

    text = re.sub(r'\n', '', text)

    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)

    text = text.split()
    useless_words = nltk.corpus.stopwords.words("english")
    useless_words = useless_words + ['hi', 'im']

    text_filtered = [word for word in text if not word in useless_words]

    text_filtered = [re.sub(r'\w*\d\w*', '', w) for w in text_filtered]

    if stem == 'Stem':
        stemmer = PorterStemmer()
        text_stemmed = [stemmer.stem(y) for y in text_filtered]
    elif stem == 'Lem':
        lem = WordNetLemmatizer()
        text_stemmed = [lem.lemmatize(y) for y in text_filtered]
    elif stem == 'Spacy':
        text_filtered = nlp(' '.join(text_filtered))
        text_stemmed = [y.lemma_ for y in text_filtered]
    else:
        text_stemmed = text_filtered

    final_string = ' '.join(text_stemmed)

    return final_string


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
