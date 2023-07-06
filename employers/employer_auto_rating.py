import re

from configs.config import RATING_RESULT_PROTOCOL, settings
from configs.dictionaries import RATING_CONFIG
from configs.workers import MORPH


def final_rating(rating_profile: int, rating_work_with: int, rating_benefits: int, rating_areas: int) -> float:
    if rating_profile + rating_work_with == 0:
        return 0
    return (
            (1 + .2 * settings.COEFFICIENT_PROFILE_RATING) * (
                rating_work_with * settings.COEFFICIENT_FIELD_RATING
                + rating_benefits * settings.COEFFICIENT_BENEFIT_RATING
                + rating_areas * settings.COEFFICIENT_AREA_RATING
            )
    )


MAX_RATING = final_rating(10, 10, 10, 10)


def get_morph_set(text: str) -> set:
    """Возврат приведенных слов (граммемы)"""
    return {
        MORPH.parse(word)[0].normal_form for word in
        set(re.findall(r'[a-яa-zййё-]+', text.lower().strip()))
        if len(word) > 3
    }


def calc_rating(morph_set: set, signal_words: list) -> bool:
    def finder_str_one(word: str):
        result = word in morph_set
        if not result:
            words_list = word.split('-')
            if len(words_list) > 1:
                return all(word in morph_set for word in words_list)
        return result

    def finder(word_rating: list | str):
        if isinstance(word_rating, str):
            return finder_str_one(word_rating)

        if isinstance(word_rating[0], str):
            result = finder_str_one(word_rating[0])
        else:
            result = all(finder_str_one(word) for word in word_rating[0])
        if not result:
            return False

        if isinstance(word_rating[1], str):
            return all(finder_str_one(word_rating[i]) for i in range(1, len(word_rating)))
        return any(finder_str_one(word) for word in word_rating[1])

    for words in signal_words:
        if finder(words):
            return True
    return False


def get_rating(morph_set: set, rating_list: list[int, list]) -> int:
    rating_list.sort(key=lambda x: x[0], reverse=True)
    for rating, signal_words in rating_list:
        if calc_rating(morph_set, signal_words):
            return rating
    return 0


def get_employer_rating(text: str) -> RATING_RESULT_PROTOCOL:
    """
    Существует 4 типа рейтинга хранящихся в формате json в RATING_CONFIG:
    Это ключи: profile, work_with, benefits, areas
    Каждый ключ содержит список списков. В списке первое значение это рейтинг, а второе значение - список слов.
    Список слов может быть представлен в виде перечисления str и list. В list перечисляются слова обязательно
    встречающиеся вместе, если второе значение - str; если второе значение - list, то первое слово обязательно, и
    обязательно одно из слов списка.
    Примеры:
    - [5, ['abc', 'dct']] - рейтинг 5, если встречается либо 'abc', либо 'dct';
    - [8, [['abc', 'dct'], 'qwe'] - рейтинг 8, если встречается либо ('abc' И 'dct') ИЛИ 'qwe';
    - [4, [['xyz', ['abc', 'dct']], 'qwe'] - рейтинг 4, если встречается ('xyz' И ('abc' ИЛИ 'dct')) ИЛИ 'qwe';
    :param text: описание компании;
    :return: рейтинг в процентах и сами рейтинги
    """
    morph_set = get_morph_set(text)
    result_dict = {
        'rating_profile': get_rating(morph_set, RATING_CONFIG['profile']),
        'rating_work_with': get_rating(morph_set, RATING_CONFIG['work_with']),
        'rating_benefits': get_rating(morph_set, RATING_CONFIG['benefits']),
        'rating_areas': get_rating(morph_set, RATING_CONFIG['areas'])
    }
    return int(100 * final_rating(**result_dict) / MAX_RATING), result_dict
