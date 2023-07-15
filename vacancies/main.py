import time
from collections import namedtuple
from copy import deepcopy
from random import random

import requests
from sqlalchemy.orm import Session

from configs.config import settings, engine
from configs.dictionaries import (
    AREAS_RATING,
    CONFIG_SEARCH,
    CLUSTERS_STOP_LIST,
    SPECIALIZATION_RATING,
    INDUSTRY_RATING,
    ROLE_RATING,
    CURRENCY
)
from db.models import Vacancy, Employers, VacancyRating
from employers.main import Employer
from vacancies.models import ResponseVacancy, FindVacancies, Params, Clusters, Salary

# key -> id in cluster data: (Rating_dict as key: value, key of request params of vacancy)
RatingTuple = namedtuple('RatingTuple', ['rating', 'param'])
ClusterRatings = {
    'area': RatingTuple(AREAS_RATING, 'area'),
    'professional_area': RatingTuple(SPECIALIZATION_RATING, 'specialization'),
    'industry': RatingTuple(INDUSTRY_RATING, 'industry'),
    'professional_role': RatingTuple(ROLE_RATING, 'professional_role'),
}

EMPLOYER_WORKER = Employer()
ENDPOINT_VACANCY = settings.API + settings.VACANCY_ENDPOINT


def request_vacancies(endpoint: str, params: dict = None, headers: dict = None) -> dict:
    headers = dict(**settings.HEADER, **headers) if headers else settings.HEADER
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


class VacancyWorker:
    def __init__(self):
        self.download_vacancies = set()

    def get_vacancies_by_params(self, params: dict):
        params['page'] = 0
        params['per_page'] = 100
        pages = float('inf')
        safe_flag = 0  # STOP FLAG IF SOME PROBLEM ON API!
        stop_cnt = 100
        while params['page'] < pages and safe_flag < stop_cnt:
            response = request_vacancies(endpoint=ENDPOINT_VACANCY, params=params)
            data = FindVacancies(**response)
            pages = data.pages
            params['page'] += 1
            safe_flag += 1
            self._check_and_save_vacancies(data.items)
            time.sleep(random())

    def _check_and_save_vacancies(self, vacancies: list[ResponseVacancy]):
        for vacancy in vacancies:
            if (
                    vacancy.id in self.download_vacancies
                    or self.check_vacancy_in_db(vacancy)
                    or not self._check_vacancy_by_params(vacancy)
            ):
                continue
            self._check_employer(vacancy)
            self.get_and_save_vacancy(vacancy_id=vacancy.id)
            time.sleep(random())

    @staticmethod
    def save_vacancy(vacancy: ResponseVacancy):
        with Session(engine) as session:
            vacancy_model = Vacancy(**vacancy.dict())
            session.add(vacancy_model)
            session.commit()

    def check_vacancy_in_db(self, vacancy: ResponseVacancy):
        with Session(engine) as session:
            if bool(session.query(Vacancy).filter_by(id=vacancy.id).first()):
                self.download_vacancies.add(vacancy.id)
                return True
            return False

    def _check_vacancy_by_params(self, vacancy: ResponseVacancy):
        self.download_vacancies.add(vacancy.id)
        if vacancy.professional_roles and all(ROLE_RATING.get(role.id) == 0 for role in vacancy.professional_roles):
            return False
        if salary_rur := self._get_max_salary_in_rur(vacancy.salary):
            if salary_rur < CONFIG_SEARCH['min_salary']:
                return False
        lower_name = vacancy.name.lower()
        if any(stop in lower_name for stop in CONFIG_SEARCH['stop_words']):
            return False
        return True

    @staticmethod
    def _get_max_salary_in_rur(salary: Salary | None):
        if salary and salary.to:
            cross = CURRENCY.get(salary.currency)
            return int(salary.to / cross) if cross else None
        return None

    @staticmethod
    def _check_employer(vacancy: ResponseVacancy):
        if not vacancy.employer:
            return
        with Session(engine) as session:
            if not bool(session.query(Employers).filter_by(id=vacancy.employer).first()):
                EMPLOYER_WORKER.get_employer_by_id(id_company=vacancy.employer)

    @staticmethod
    def request_vacancy(vacancy_id: int) -> ResponseVacancy:
        response = request_vacancies(endpoint=f'{ENDPOINT_VACANCY}/{vacancy_id}')
        vacancy = ResponseVacancy.parse_obj(response)
        return vacancy

    def get_and_save_vacancy(self, vacancy_id: int) -> None:
        vacancy = self.request_vacancy(vacancy_id)
        self.save_vacancy(vacancy)


class SearchAndSaveVacancies:

    def __init__(self, params: Params):
        self.vacancy_worker = VacancyWorker()
        self.params = params
        self.params.clusters = False
        self.params.page = 0
        self.params.per_page = 100
        self.clusters: list[Clusters] = self._request_clusters()  # опрос вакансий только по кластерам
        self._check_clusters_in_stop_list()
        self._check_clusters_by_rating()

    def _request_clusters(self) -> list[Clusters]:
        cluster_params = deepcopy(self.params)
        cluster_params.per_page = 0  # API DOCS
        cluster_params.clusters = True
        response = request_vacancies(endpoint=ENDPOINT_VACANCY, params=cluster_params.dict(exclude_none=True))
        return [Clusters.parse_obj(cluster) for cluster in response['clusters']]

    def _check_clusters_in_stop_list(self) -> None:
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

    def _check_clusters_by_rating(self) -> None:
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

    def get_vacancies_by_clusters(self) -> None:
        for cluster in self.clusters:
            params = self.params.dict(exclude_none=True)
            param = ClusterRatings[cluster.id].param if cluster.id in ClusterRatings else cluster.id
            for item in cluster.items:
                param_value = getattr(item.params, param)
                params[param] = param_value
                if item.count > settings.MAX_VACANCIES_BY_REQUEST:
                    # FIXME: AFTER TEST -> LOGS
                    print(
                        f'Cluster {cluster.id} with [{param_value}] has {item.count} vacancies. '
                        f'Use only [{settings.MAX_VACANCIES_BY_REQUEST}]'
                    )
            self.vacancy_worker.get_vacancies_by_params(params)
