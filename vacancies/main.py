from datetime import datetime, timedelta
from collections import namedtuple
from copy import deepcopy
from math import ceil
from random import random
from time import sleep
from typing import List, Optional
from sqlalchemy.orm import Session

import requests

from db.models import Vacancy, Employers
from configs.config import settings, engine
from configs.dictionaries import (
    AREAS_RATING,
    CONFIG_SEARCH,
    CLUSTERS_STOP_LIST,
    FULL_EMPLOYERS,
    SPECIALIZATION_RATING,
    INDUSTRY_RATING,
    ROLE_RATING,
    ALL_VACANCIES,
    CURRENCY
)
from employers.main import Employer
from vacancies.models import ResponseVacancy, FindVacancies, Params, ClusterItem, Clusters, Salary

# key -> id in cluster data: (Rating_dict as key: value, key of request params of vacancy)
RatingTuple = namedtuple('RatingTuple', ['rating', 'param'])
ClusterRatings = {
    'area': RatingTuple(AREAS_RATING, 'area'),
    'professional_area': RatingTuple(SPECIALIZATION_RATING, 'specialization'),
    'industry': RatingTuple(INDUSTRY_RATING, 'industry'),
    'professional_role': RatingTuple(ROLE_RATING, 'professional_role'),
}

EMPLOYER_WORKER = Employer()


def request_vacancies(endpoint: str, params: dict = None, headers: dict = None) -> dict:
    headers = dict(**settings.HEADER, **headers) if headers else settings.HEADER
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def cluster_analysis(items: List[ClusterItem], rating_dict: dict, field_name: str) -> (int, List[ClusterItem]):
    """
    Исключает из кластеров запросы с параметрами, чей рейтинг равен 0.
    :param items: Перечисление всех параметров.
    :param rating_dict: Словарь с рейтингами.
    :param field_name: имя параметра в модели.
    :return: макс число вакансий на параметр и обновленный список значений
    (с рейтингом больше 0).
    """
    item_copy = []
    biggest_cnt = 0
    for item in items:
        if rating_dict.get(getattr(item.params, field_name, -1), 1) == 0:
            print(f'del {item.count}, {item.name}')
            continue
        if biggest_cnt < item.count:
            biggest_cnt = item.count
        item_copy.append(item)
    return biggest_cnt, item_copy


# def check_and_save_vacancy(vacancies: List[ResponseVacancy]):
#     for vacancy in vacancies:
#         if vacancy.employer is not None and vacancy.employer not in FULL_EMPLOYERS:
#             EMPLOYER_WORKER.get_employer_by_id(vacancy.employer)
#         if vacancy.id not in ALL_VACANCIES and not vacancy.archived:
#             # Считаем рейтинг вакансии.
#             # Сохраняем вакансию.
#             ALL_VACANCIES.add(vacancy.id)
#             # print(vacancy.id, vacancy.name)


class SearchAndSaveVacancies:
    ENDPOINT = settings.API + settings.VACANCY_ENDPOINT

    def __init__(self, params: Params):
        self.download_vacancies = set()
        self.params = params
        self.params.clusters = False
        self.params.page = 0
        self.params.per_page = 100
        self.clusters: list[Clusters] = self._request_clusters()  # опрос вакансий только по кластерам
        self._check_clusters_in_stop_list()
        self._check_clusters_by_rating()

    def _request_clusters(self):
        cluster_params = deepcopy(self.params)
        cluster_params.per_page = 0  # API DOCS
        cluster_params.clusters = True
        response = request_vacancies(endpoint=self.ENDPOINT, params=cluster_params.dict(exclude_none=True))
        return [Clusters.parse_obj(cluster) for cluster in response["clusters"]]

    def _check_clusters_in_stop_list(self):
        use_clusters = []
        for cluster in self.clusters:
            name = cluster.id
            if name not in CLUSTERS_STOP_LIST['use_cluster']:
                continue

            if name in CLUSTERS_STOP_LIST['cluster_stops']:
                item_list = []
                for item in cluster.items:
                    value = getattr(item.params, name)
                    if value in CLUSTERS_STOP_LIST['cluster_stops'][name]:
                        continue
                    item_list.append(item)
                if not item_list:
                    continue
                cluster.items = item_list
            use_clusters.append(cluster)
        self.clusters = use_clusters

    def _check_clusters_by_rating(self):
        use_clusters = []
        for cluster in self.clusters:
            if cluster.id in ClusterRatings:
                rating, param = ClusterRatings[cluster.id]
                item_list = []
                for item in cluster.items:
                    item_rating = rating.get(getattr(item.params, param), -1)
                    if item_rating != 0:
                        item_list.append(item)
                        if item_rating == -1:
                            # FIXME: AFTER TEST -> LOGS
                            print(f'Для {cluster.id} не определен рейтинг ключа {getattr(item.params, param)}')
                if not item_list:
                    continue
                cluster.items = item_list

            use_clusters.append(cluster)
        self.clusters = use_clusters

    def get_vacancies_by_clusters(self):
        for cluster in self.clusters:
            params = self.params.dict(exclude_none=True)
            param = ClusterRatings[cluster.id].param if cluster.id in ClusterRatings else cluster.id
            for item in cluster.items:
                param_value = getattr(item, param)
                params[param] = param_value
                if item.count > settings.MAX_VACANCIES_BY_REQUEST:
                    # FIXME: AFTER TEST -> LOGS
                    print(
                        f'Cluster {cluster.id} with [{param_value}] has {item.count} vacancies. '
                        f'Use only [{settings.MAX_VACANCIES_BY_REQUEST}]'
                    )

    def _get_vacancies_by_params(self, params: dict):
        params['page'] = 0
        params['per_page'] = 100
        pages = float('inf')
        while params['page'] < pages:
            response = request_vacancies(endpoint=self.ENDPOINT, params=params)
            data = FindVacancies(**response)
            pages = data.pages
            params['page'] += 1

    def _check_and_save_vacancies(self, vacancies: list[ResponseVacancy]):
        for vacancy in vacancies:
            if (
                    vacancy.id in self.download_vacancies
                    or self.check_vacancy_in_db(vacancy)
                    or not self._check_vacancy_by_params(vacancy)
            ):
                continue
            self._check_employer(vacancy)

    def save_vacancy(self, vacancy: ResponseVacancy):
        with Session(engine) as session:
            vacancy_model = Vacancy(**vacancy.dict())
            session.add(vacancy_model)
            session.commit()
            self.download_vacancies.add(vacancy.id)

    @staticmethod
    def check_vacancy_in_db(vacancy: ResponseVacancy):
        with Session(engine) as session:
            return bool(session.query(Vacancy).filter_by(id=vacancy.id).first())

    def _check_vacancy_by_params(self, vacancy: ResponseVacancy):
        if salary_rur := self._get_max_salary_in_rur(vacancy.salary):
            if salary_rur < CONFIG_SEARCH['min_salary']:
                self.download_vacancies.add(vacancy.id)
                return False
        lower_name = vacancy.name.lower()
        if any(stop in lower_name for stop in CONFIG_SEARCH['stop_words']):
            self.download_vacancies.add(vacancy.id)
            return False
        return True

    @staticmethod
    def _get_max_salary_in_rur(salary: Salary):
        cross = CURRENCY.get(salary.currency)
        if cross and salary.to:
            return int(salary.to / cross)
        return None

    @staticmethod
    def _check_employer(vacancy: ResponseVacancy):
        if not vacancy.employer:
            return
        with Session(engine) as session:
            if not bool(session.query(Employers).filter_by(id=vacancy.employer).first()):
                EMPLOYER_WORKER.get_employer_by_id(id_company=vacancy.employer)

    def request_vacancy(self, vacancy_id: int):
        response = request_vacancies(endpoint=f'{self.ENDPOINT}/{vacancy_id}')
        vacancy = ResponseVacancy.parse_obj(response)
        self.save_vacancy(vacancy)


#
# class JobSearch:
#     """Для каждого запроса создаем отдельный экземпляр данного класса"""
#     ENDPOINT = settings.API + settings.VACANCY_ENDPOINT
#
#     def __init__(self):
#         self.params: Params | None = None
#         self.un_use_clusters = CLUSTERS_STOP_LIST["un_use_cluster"]
#
#     def search_best_clusters(self, clusters: List[Clusters]) -> Optional[Clusters]:
#         """
#         Ищем и записываем значение кластера, с минимальным количеством вакансий
#         на параметр поиска. Правильно выбранный кластер позволяет сократить
#         количество рекурсивных вызовов поиска (ответ ограничен 2 000 вакансий,
#         по наблюдениям, при запросе от 1000 вакансий HH может возвращать ошибки).
#         """
#         best_cluster_cnt = float('inf')
#         best_cluster = None
#         for num, cluster in enumerate(clusters):
#             # area, ЗП, label, edu и ранее используемые - исключаем
#             if cluster.id in self.un_use_clusters:
#                 continue
#             analysis_attr = ClusterRatings.get(cluster.id)
#             if analysis_attr:
#                 biggest_cnt, cluster.items = cluster_analysis(cluster.items, *analysis_attr)
#             else:
#                 biggest_cnt = max([item.count for item in cluster.items])
#             if biggest_cnt < best_cluster_cnt:
#                 best_cluster_cnt = biggest_cnt
#                 best_cluster = num
#         if best_cluster is None:
#             return
#         use_clusters = clusters[best_cluster]
#         use_clusters.items.sort(key=lambda item: item.count)
#         self.un_use_clusters.append(use_clusters.id)
#         return use_clusters
#
#     def search_vacancies_by_date(self, date_from: datetime = None, date_to: datetime = None, **params):
#         if not params:
#             params = CONFIG_SEARCH
#         params['clusters'] = True
#         if date_from is None:
#             # Запрос последней даты запроса из БД. Если ее нет, возврат ошибки
#             # Если есть, запрос от нее до текущей даты - 1 день.
#             date_from = datetime(year=2022, month=12, day=19)  # Костыль
#             date_to = datetime(year=2022, month=12, day=19)  # Костыль
#         for delta in range((date_to - date_from).days + 1):
#             date_found = (date_from + timedelta(days=delta)).strftime('%Y-%m-%d')
#             params['date_from'] = params['date_to'] = date_found
#             self.start_searching(**params)
#
#     def pars_by_vacancy_strategy(self, response: FindVacancies):
#         vacancy_cnt = response.found
#         has_cluster = bool(response.clusters)
#         if vacancy_cnt > settings.MAX_VACANCIES_BY_REQUEST and has_cluster:
#             use_clusters = self.search_best_clusters(response.clusters)
#             if use_clusters is None:
#                 self.pars_worker(response)
#             else:
#                 for cluster in use_clusters.items:
#                     params = cluster.params.dict()
#                     params['clusters'] = cluster.count > settings.MAX_VACANCIES_BY_REQUEST
#                     self.start_searching(**params)
#                 self.un_use_clusters.pop()
#         else:
#             self.pars_worker(response)
#
#     def pars_worker(self, response: FindVacancies):
#         self.params.clusters = None
#         # print(f'FIND: {response.found} vacancy:')
#         # print(self.params.dict())
#         use_page = ceil(response.found / response.per_page)
#         max_page = min(use_page, settings.MAX_VACANCIES_BY_REQUEST / response.per_page)
#         check_and_save_vacancy(response.items)
#         for page in range(1, max_page):
#             self.params.page = page
#             vacancies = self.return_vacancies()
#             check_and_save_vacancy(vacancies.items)
#             sleep(random())
#
#     def return_vacancies(self, **params):
#         """Передаем параметры запроса, возвращаем валидный результат."""
#         if params:
#             self.params = Params(**params)  # Валидация параметров запроса
#         response = request_vacancies(endpoint=self.ENDPOINT, params=self.params.dict())
#         return FindVacancies(**response)
#
#     def start_searching(self, **params) -> None:
#         """
#         :param params: Детали запроса в модели Params
#         """
#         vacancies = self.return_vacancies(**params)
#         self.pars_by_vacancy_strategy(vacancies)
