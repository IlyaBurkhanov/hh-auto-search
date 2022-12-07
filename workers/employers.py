import unicodedata

from bs4 import BeautifulSoup as bs
from sqlalchemy.orm import Session
from tqdm import tqdm
from time import sleep
from random import random

from hh_api.responser import Responser, Validator
from hh_api.endpoints import Settings
from db.save_manager import engine
from db.models import CompanyIndustryRelated

EMPLOYER_TYPE_DICT = 'employer_type'


class WorkEmployers:
    validator = Validator()
    responser = Responser()
    settings = Settings.EMPLOYERS
    employer_validator = Settings.EMPLOYER.validator
    model = settings.db_model
    set_id = set()  # Наш мемкэш для работодателей.
    params = {'page': 0}
    # API допускает получение до 5 000 работодателей, но по наблюдениям
    # запрос от 3000-4000 позиции вызывает странные ошибки на стороне сервера
    max_items = 3000  # Не более 5 000

    def __init__(self):
        self.session = Session(engine)
        self.set_id = set(idx for idx, in self.session.query(self.model.id))
        employers_count = self.get_employers_count()
        # В ЛОГИ
        print('Доля заполнения базы работодателями составляет: '
              f'{len(self.set_id) / employers_count:.1%}')

    def __del__(self):
        """
        Вместо вызовов менеджера контекста. Все коннекты закроются при
        завершении сеанса.
        """
        self.session.close()

    def get_employers_count(self) -> int:
        """
        Запрос числа работодателей с открытыми вакансиями. Используем
        как показатель полноты данных во внутренней БД.
        :return: Число работодателей
        """
        params = {'page': 0, 'only_with_vacancies': True,
                  'per_page': 1}
        # Тут нужно обернуть, перехватывая ошибку response.code != 200
        found_employers = self.__response_employers(params).get('found', None)
        if found_employers is None:
            raise ValueError('При запросе количества работодателей, '
                             'что-то пошло не так')
        return int(found_employers)

    @staticmethod
    def __return_request_params(page_per_list, with_vacancies,
                                text, area, employer_type):

        params = dict(page=0, only_with_vacancies=with_vacancies,
                      per_page=page_per_list)
        if employer_type:
            params['type'] = employer_type
        for par in ['text', 'area']:
            if locals()[par] is not None:
                params[par] = locals()[par]
        return params

    def update_employers(self, page_per_list: int = 100,
                         with_vacancies: bool = True,
                         text: str = None, area: int = None,
                         employer_type: str = None) -> None:
        """
        Запрос списка работодателей. По факту API HH
        :param page_per_list: значений на листе <= 100
        :param with_vacancies: Только с вакансиями
        :param text: Текст поиска компании
        :param area: Код региона или страны (справочник Area)
        :param employer_type: Тип лица поиска (компания, рекрутер и т.д.)
        Детали в справочнике по ключу employer_type
        :return: Запрашиваем партиями и пишем в БД (или обновляем)
        """
        params = self.__return_request_params(page_per_list, with_vacancies,
                                              text, area, employer_type)
        result = self.__response_employers(params)
        max_request = (
                min(self.max_items, int(result['found'])) // page_per_list
        )
        self.__save_result((result.pop('items')))

        for _ in tqdm(range(1, max_request + 1),
                      disable='Обновление справочника Работодателей'):
            sleep(random() * 3)  # Шоб не забаняли
            try:
                params['page'] += 1
                self.__save_result(
                    self.__response_employers(params).pop('items'))
            except Exception:
                # Логируем
                print('При обновлении справочника Работодателей '
                      'что-то пошло не так')
                break

    def __response_employers(self, params: dict, endpoint: str = None) -> dict:
        """Наш опросник hh.api на работодателей"""
        endpoint = endpoint or self.settings.endpoint
        response = self.responser.response(endpoint, params=params)
        if response.request.status_code != 200:
            raise ValueError('Ошибка запроса!!!!')
        return response.get_json()

    #
    def __check_open_vacancy(self, employer: Settings.EMPLOYERS):
        """Чекаем вакансии работодателя. Если работодатель есть, обновляем
        открытые вакансии."""
        if employer.id in self.set_id:
            employ = self.session.query(self.model).filter(
                self.model.id == employer.id).first()
            employ.open_vacancies = employer.open_vacancies
            self.session.commit()
            return True
        return False

    def __save_result(self, items: list[Settings.EMPLOYERS]) -> None:
        """
        Обновление или запись
        :param items: Верифицированные записи работодателя.
        :return: None
        """
        check_employer = self.validator.return_objects(
            self.settings.validator, items)
        save_result = []
        for employer in check_employer:
            if self.__check_open_vacancy(employer):
                continue
            self.set_id.add(employer.id)
            save_result.append(employer)

        if save_result:
            self.session.bulk_insert_mappings(
                self.model, [dict(x) for x in save_result])
            self.session.commit()

    def __save_employer(self, employer):
        area = int(employer.area.id) if employer.area else None
        industries_id = ([industry.id for industry in employer.industries]
                         if employer.industries else [])
        employer_in_db = self.model(**employer.dict())
        if area:
            employer_in_db.area_id = area
        self.session.add(employer_in_db)
        for inx in industries_id:
            self.session.add(CompanyIndustryRelated(
                id_industry=inx,
                id_employer=employer.id)
            )
        self.session.commit()
        self.set_id.add(employer.id)

    def __check_employer(self, raw_employer: dict):
        employer_valid = self.employer_validator.parse_obj(raw_employer)
        text_employer = bs(employer_valid.description, 'lxml')
        employer_valid.description = unicodedata.normalize(
            'NFKD', text_employer.text.lower().strip())
        return employer_valid

    def get_employer_by_id(self, id_company):
        if int(id_company) in self.set_id:
            print(f'Работодатель с ID[{id_company}] уже в базе')  # В ЛОГ
            return
        endpoint = self.settings.endpoint + f'/{id_company}'
        employer_raw = self.__response_employers(endpoint=endpoint, params={})
        employer_valid = self.__check_employer(employer_raw)
        self.__save_employer(employer_valid)

        # Check.EMPLOYER !!!!
