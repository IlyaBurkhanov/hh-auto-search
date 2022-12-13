import re
from typing import Union

from configs.conf import MORPH, RATING_CONFIG


def final_rating(rating_profile, rating_work_with, rating_benefits,
                 rating_areas):
    if rating_profile + rating_work_with == 0:
        return 0
    return (1 + .2 * rating_profile) * (
            rating_work_with * 3 + rating_benefits * 2 + rating_areas + 10)


MAX_RATING = final_rating(10, 10, 10, 10)


def get_morph_set(text: str) -> set:
    """Возврат приведенных слов (граммемы)"""
    return {
        MORPH.parse(word)[0].normal_form for word in
        set(re.findall(r'[a-яa-zййё-]+', text.lower().strip()))
        if len(word) > 3
    }


def calc_rating(morph_set: set, list_find: list):
    def finder_str_one(word):
        result = word in morph_set
        words_list = word.split('-')
        if not result and len(words_list) > 1:
            return all(word in morph_set for word in words)
        return result

    def finder(word_rating: Union[list, str]):
        if isinstance(word_rating, str):
            return finder_str_one(word_rating)

        result = finder_str_one(word_rating[0])

        if not result:
            return False

        if isinstance(word_rating[1], str):
            return all(finder_str_one(word_rating[i])
                       for i in range(1, len(word_rating)))

        return finder(words[1])

    for words in list_find:
        if finder(words):
            return True
    return False


def get_rating(morph_set, rating_list):
    rating_list.sort(key=lambda x: x[0], reverse=True)
    for rating, list_find in rating_list:
        if calc_rating(morph_set, list_find):
            return rating
    return 0


def get_employ_rating(text):
    morph_set = get_morph_set(text)
    rating_profile = get_rating(morph_set, RATING_CONFIG['profile'])
    rating_work_with = get_rating(morph_set, RATING_CONFIG['work_with'])
    rating_benefits = get_rating(morph_set, RATING_CONFIG['benefits'])
    rating_areas = get_rating(morph_set, RATING_CONFIG['areas'])
    result_dict = {'rating_profile': rating_profile,
                   'rating_work_with': rating_work_with,
                   'rating_benefits': rating_benefits,
                   'rating_areas': rating_areas}
    return int(100 * final_rating(**result_dict) / MAX_RATING), result_dict
