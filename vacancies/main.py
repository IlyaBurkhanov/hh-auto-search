import requests
from datetime import datetime, date, timedelta

from employers.main import Employer
from vacancies.models import ResponseVacancy, FindVacancies, Params
from configs.conf import (
    CONFIG_SEARCH, VACANCY_ENDPOINT, API, HEADER, FULL_EMPLOYERS_ID,
    MAX_VACANCIES_BY_REQUEST
)

SEARCH_FILE = 'config_for_rating/search_config.json'  # ENV


def request_vacancies(endpoint, params: dict = None, headers: dict = None):
    if headers:
        headers = dict(**HEADER, **headers)
    response = requests.get(endpoint, params=params, headers=headers)
    response.raise_for_status()
    return response.json()


class JobSearch:
    ENDPOINT = API + '/' + VACANCY_ENDPOINT

    def search_vacancies_by_date(self, date_from: datetime = None,
                                 date_to: datetime = None, **kwargs):
        if date_from is None:
            # Запрос последней даты запроса из БД. Если ее нет, возврат ошибки
            # Если есть, запрос от нее до текущей даты - 1 день.
            pass
        for delta in range((date_to - date_from).days + 1):
            date_found = (date_from + timedelta(days=delta)
                          ).strftime('%Y-%m-%d')
            kwargs['date_from'] = kwargs['date_to'] = date_found
            self.search_vacancies(**kwargs)

    def search_best_clusters(self, response):
        pass

    def request_vacancy_strategy(self, response: FindVacancies):
        vacancy_cnt = response.found
        if vacancy_cnt > MAX_VACANCIES_BY_REQUEST:
            pass


    def search_vacancies(self, **kwargs) -> None:
        """
        :param kwargs: Детали запроса в модели Params
        """
        request_params = Params(**kwargs)  # Валидация параметров запроса
        response = request_vacancies(endpoint=self.ENDPOINT, headers=HEADER,
                                     params=request_params.dict())
        vacancies = FindVacancies(**response)
        strategy = self.request_vacancy_strategy(vacancies)
