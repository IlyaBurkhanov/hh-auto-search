from typing import List, Optional

from math import ceil
import requests
from datetime import datetime, date, timedelta

# from employers.main import Employer
from vacancies.models import (
    ResponseVacancy, FindVacancies, Params, ClusterItem, Clusters
)
from configs.conf import (
    CONFIG_SEARCH, VACANCY_ENDPOINT, API, HEADER, FULL_EMPLOYERS,
    MAX_VACANCIES_BY_REQUEST, UN_USE_CLUSTER_ID, DROP_PARAMS,
    SPECIALIZATION_RATING, INDUSTRY_RATING, ROLE_RATING
)

ClusterRatings = {
    'professional_area': (SPECIALIZATION_RATING, 'specialization'),
    'industry': (INDUSTRY_RATING, 'industry'),
    'professional_role': (ROLE_RATING, 'professional_role'),
}


def request_vacancies(endpoint,
                      params: dict = None, headers: dict = None) -> dict:
    if headers:
        headers = dict(**HEADER, **headers)
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


def cluster_analysis(items: List[ClusterItem],
                     rating_dict: dict,
                     field_name: str) -> (int, List[ClusterItem]):
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
            continue
        if biggest_cnt < item.count:
            biggest_cnt = item.count
        item_copy.append(item)
    return biggest_cnt, item_copy


def check_and_save_vacancy(vacancies: List[ResponseVacancy]):
    # Проверка вакансий, если были пропускает, запрашивает работодателя если
    # нет в справочнике, записывает его
    # Расчет рейтинга
    pass


class JobSearch:
    """Для каждого запроса создаем отдельный экземпляр данного класса"""
    ENDPOINT = API + '/' + VACANCY_ENDPOINT

    def __init__(self):
        self.params: Optional[Params] = None
        self.un_use_clusters = UN_USE_CLUSTER_ID.copy()

    def search_best_clusters(
            self, clusters: List[Clusters]) -> Optional[Clusters]:
        """
        Ищем и записываем значение кластера, с минимальным количеством вакансий
        на параметр поиска. Правильно выбранный кластер позволяет сократить
        количество рекурсивных вызовов поиска (ответ ограничен 2 000 вакансий,
        по наблюдениям, при запросе от 1000 вакансий HH может
        возвращать ошибки).
        """
        best_cluster_cnt = float('inf')
        best_cluster = None
        for num, cluster in enumerate(clusters):
            # area, ЗП, label, edu и ранее используемые - исключаем
            if cluster.id in self.un_use_clusters:
                continue
            analysis_attr = ClusterRatings.get(cluster.id)
            if analysis_attr:
                biggest_cnt, cluster.items = cluster_analysis(
                    cluster.items, *analysis_attr)
            else:
                biggest_cnt = max([item.count for item in cluster.items])
            if biggest_cnt < best_cluster_cnt:
                best_cluster_cnt = biggest_cnt
                best_cluster = num
        if best_cluster is None:
            return
        use_clusters = clusters[best_cluster]
        use_clusters.items.sort(key=lambda item: item.count)
        self.un_use_clusters.append(use_clusters.id)
        return use_clusters

    def search_vacancies_by_date(self, date_from: datetime = None,
                                 date_to: datetime = None, **params):
        if date_from is None:
            # Запрос последней даты запроса из БД. Если ее нет, возврат ошибки
            # Если есть, запрос от нее до текущей даты - 1 день.
            pass
        for delta in range((date_to - date_from).days + 1):
            date_found = (date_from + timedelta(days=delta)
                          ).strftime('%Y-%m-%d')
            params['date_from'] = params['date_to'] = date_found
            self.start_searching(**params)

    def pars_by_vacancy_strategy(self, response: FindVacancies):
        vacancy_cnt = response.found
        has_cluster = bool(response.clusters)
        if vacancy_cnt > MAX_VACANCIES_BY_REQUEST and has_cluster:
            use_clusters = self.search_best_clusters(response.clusters)
            if use_clusters is None:
                self.pars_worker(response)
            else:
                for cluster in use_clusters.items:
                    params = cluster.params.dict()
                    if cluster.count > MAX_VACANCIES_BY_REQUEST:
                        params['clusters'] = True
                    else:
                        params['clusters'] = False
                    self.start_searching(**params)
                self.un_use_clusters.pop()
        else:
            self.pars_worker(response)

    def pars_worker(self, response: FindVacancies):
        self.params.clusters = None
        use_page = ceil(response.found / response.per_page)
        max_page = min(use_page, MAX_VACANCIES_BY_REQUEST / response.per_page)
        check_and_save_vacancy(response.items)
        for page in range(1, max_page):
            self.params.page = page
            vacancies = self.return_vacancies()
            check_and_save_vacancy(vacancies.items)

    def return_vacancies(self, **params):
        """Передаем параметры запроса, возвращаем валидный результат."""
        if params:
            self.params = Params(**params)  # Валидация параметров запроса
        response = request_vacancies(endpoint=self.ENDPOINT, headers=HEADER,
                                     params=self.params.dict())
        return FindVacancies(**response)

    def start_searching(self, **params) -> None:
        """
        :param params: Детали запроса в модели Params
        """
        vacancies = self.return_vacancies(**params)
        self.pars_by_vacancy_strategy(vacancies)
