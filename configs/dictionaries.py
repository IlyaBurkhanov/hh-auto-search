import json
from sqlalchemy.orm import Session

from configs.config import engine, settings
from db.models import (
    Employers, BusinessRating, IndustriesRating, IndustryRating, RoleRating,
    SpecializationRating, SpecializationsRating, AreasRating, Currency
)


def read_json(json_path) -> dict:
    with open(json_path, 'r', encoding='utf8') as file:
        return json.load(file)


def get_from_db(model, what: str = 'employer'):
    with Session(engine) as session:
        if what == 'employer':
            return {
                idx: auto_rating if manual_rating is None else manual_rating
                for idx, auto_rating, manual_rating in session.query(model.id, model.auto_rating, model.manual_rating)
            }
        elif what == 'rating':
            return {idx: rating for idx, rating in session.query(model.id, model.my_rating)}
        elif what == 'currency':
            return {code: rate for code, rate in session.query(model.code, model.rate)}


def clusters_stops():
    cluster_stop_list_data = read_json(settings.CLUSTERS_STOP_LIST_FILE)
    cluster_stop_list_data['use_cluster'] = set(cluster_stop_list_data.get('use_cluster', []))
    cluster_stop_list_data.setdefault('cluster_stops', {})
    for name, values in cluster_stop_list_data['cluster_stops'].items():
        cluster_stop_list_data['cluster_stops'][name] = set(values)
    return cluster_stop_list_data


# FIXME: FUTURE: 'get_from_db' rating replace on queries to DB (partial func)
FULL_EMPLOYERS = get_from_db(Employers, what='employer')  # Работодатели
ALL_VACANCIES = set()  # Вакансии в БД (ID)
CURRENCY = get_from_db(Currency, what='currency')  # Курсы валют
AREAS_RATING = get_from_db(AreasRating, what='rating')
BUSINESS_RATING = get_from_db(BusinessRating, what='rating')
INDUSTRIES_RATING = get_from_db(IndustriesRating, what='rating')
INDUSTRY_RATING = get_from_db(IndustryRating, what='rating')
ROLE_RATING = get_from_db(RoleRating, what='rating')
SPECIALIZATION_RATING = get_from_db(SpecializationRating, what='rating')
SPECIALIZATIONS_RATING = get_from_db(SpecializationsRating, what='rating')
RATING_CONFIG = read_json(settings.RATING_FILE)  # Рейтинги для работодателя
CONFIG_SEARCH = read_json(settings.SEARCH_FILE)  # Конфигурация поиска
CLUSTERS_STOP_LIST = clusters_stops()  # Стоп параметры и стоп кластера
