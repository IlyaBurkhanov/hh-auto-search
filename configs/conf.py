import json
import pymorphy3
from sqlalchemy.orm import Session

from db.core import engine
from db.models import (
    Employers, BusinessRating, IndustriesRating, IndustryRating, RoleRating,
    SpecializationRating, SpecializationsRating, AreasRating, Currency
)

from db.save_manager import SaveManager
from hh_api.responser import Responser, Validator

API = 'https://api.hh.ru/'
HEADER = {'User-Agent': 'Ilya_APP/0.1 (iaburhanov@mail.ru)'}  # ENV

RATING_FILE = 'config_for_rating/employer_rating_config.json'  # ENV
SEARCH_FILE = 'config_for_rating/search_config.json'  # ENV
UN_USE_CLUSTER_ID = ['salary', 'area']
MAX_VACANCIES_BY_REQUEST = 1000  # ENV
VACANCY_ENDPOINT = 'vacancies'  # ENV


def read_json(json_path):
    with open(json_path, 'r', encoding='utf8') as file:
        return json.load(file)


def get_from_db(model, what: str = 'index'):
    with Session(engine) as session:
        if what == 'index':
            result = set(idx for idx, in session.query(model.id))
        elif what == 'rating':
            result = {idx: rating for idx, rating in
                      session.query(model.id, model.my_rating)}
        elif what == 'currency':
            result = {code: rate for code, rate in
                      session.query(model.code, model.rate)}
    return result


FULL_EMPLOYERS_ID = get_from_db(Employers, what='index')
CURRENCY = get_from_db(Currency, what='currency')
AREAS_RATING = get_from_db(AreasRating, what='rating')
BUSINESS_RATING = get_from_db(BusinessRating, what='rating')
INDUSTRIES_RATING = get_from_db(IndustriesRating, what='rating')
INDUSTRY_RATING = get_from_db(IndustryRating, what='rating')
ROLE_RATING = get_from_db(RoleRating, what='rating')
SPECIALIZATION_RATING = get_from_db(SpecializationRating, what='rating')
SPECIALIZATIONS_RATING = get_from_db(SpecializationsRating, what='rating')

VALIDATOR = Validator()  # Валидатор
RESPONSER = Responser()  # Запросы к HH
SAVE_MANAGER = SaveManager()  # Менеджер для записи

# в 3.11 ошибка. Исправление -> github.com/kmike/pymorphy2/pull/157
MORPH = pymorphy3.MorphAnalyzer()  # Приведение слов к нормальной форме

RATING_CONFIG = read_json(RATING_FILE)  # Рейтинги для работодателя
CONFIG_SEARCH = read_json(SEARCH_FILE)  # Конфигурация поиска
DROP_PARAMS = CONFIG_SEARCH.pop('drop_params')  # Временно не исп. параметры
