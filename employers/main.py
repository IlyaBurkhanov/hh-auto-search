import unicodedata

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError
from tqdm import tqdm
from time import sleep
from random import random

from hh_api.responser import Responser, Validator
from hh_api.endpoints import Settings
from db.save_manager import engine
from db.models import CompanyIndustryRelated
from employers.rating import CalcEmployerRating


class AddSession:
    def __init__(self):
        self.session = Session(engine)

    def __del__(self):
        try:
            self.session.close()
        except ProgrammingError:
            pass


EmployerRating = CalcEmployerRating()
ENDPOINT = Settings.EMPLOYERS.endpoint
RESPONSER = Responser()
VALIDATOR = Validator()
MODEL = Settings.EMPLOYERS.db_model
# Наш мемкэш для работодателей.
FULL_EMPLOYERS_ID = set(idx for idx, in AddSession().session.query(MODEL.id))


def return_employer_with_rating(employer):
    ratings = EmployerRating.get_employer_rating(employer)
    return employer.copy(update=ratings)


def response_employers(params: dict, endpoint: str = None) -> dict:
    """Наш опросник hh.api на работодателей"""
    endpoint = endpoint or ENDPOINT
    response = RESPONSER.response(endpoint, params=params)
    if response.request.status_code != 200:
        raise ValueError('Ошибка запроса!!!!')
    return response.get_json()


class UpdateEmployers(AddSession):
    employer_validator = Settings.EMPLOYERS.validator
    params = {'page': 0}
    # API допускает получение до 5 000 работодателей, но по наблюдениям
    # запрос от 3000-4000 позиции вызывает странные ошибки на стороне сервера
    max_items = 500  # Не более 5 000

    def __init__(self):
        super().__init__()
        employers_count = self.get_employers_count()
        # В ЛОГИ
        print('Доля заполнения базы работодателями составляет: '
              f'{len(FULL_EMPLOYERS_ID) / employers_count:.1%}')

    @staticmethod
    def get_employers_count() -> int:
        """
        Запрос числа работодателей с открытыми вакансиями. Используем
        как показатель полноты данных во внутренней БД.
        :return: Число работодателей
        """
        params = {'page': 0, 'only_with_vacancies': True,
                  'per_page': 1}
        # Тут нужно обернуть, перехватывая ошибку response.code != 200
        found_employers = response_employers(params).get('found', None)
        if found_employers is None:
            raise ValueError('При запросе количества работодателей, '
                             'что-то пошло не так')
        return int(found_employers)

    @staticmethod
    def _return_request_params(page_per_list, with_vacancies,
                               text, area, employer_type):

        params = dict(page=0, only_with_vacancies=with_vacancies,
                      per_page=page_per_list)
        if employer_type:
            params['type'] = employer_type
        for par, val in [('text', text), ('area', area)]:
            if val is not None:
                params[par] = val
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
        params = self._return_request_params(page_per_list, with_vacancies,
                                             text, area, employer_type)
        result = response_employers(params)
        max_request = (
                min(self.max_items, int(result['found'])) // page_per_list
        )
        self._save_result((result.pop('items')))

        for _ in tqdm(range(1, max_request),
                      disable='Обновление справочника Работодателей'):
            sleep(random() * 2)  # Шоб не забаняли
            try:
                params['page'] += 1
                self._save_result(
                    response_employers(params).pop('items'))
            except Exception:
                # Логируем
                print('При обновлении справочника Работодателей '
                      'что-то пошло не так')
                break

    def _save_result(self, items: list) -> None:
        """
        Обновление или запись
        :param items: Верифицированные записи работодателя.
        :return: None
        """
        check_employer = VALIDATOR.return_objects(
            self.employer_validator, items)
        save_result = []
        for employer in check_employer:
            if self._check_open_vacancy(employer):
                continue
            FULL_EMPLOYERS_ID.add(employer.id)
            save_result.append(employer)

        if save_result:
            self.session.bulk_insert_mappings(
                MODEL, [dict(x) for x in save_result])
            self.session.commit()

    def _check_open_vacancy(self, employer):
        """Чекаем вакансии работодателя. Если работодатель есть, обновляем
        открытые вакансии."""
        if employer.id in FULL_EMPLOYERS_ID:
            employ = self.session.query(MODEL).filter(
                MODEL.id == employer.id).first()
            employ.open_vacancies = employer.open_vacancies
            self.session.commit()
            return True
        return False


class Employer(AddSession):
    def __init__(self):
        super().__init__()
        self.validator = Settings.EMPLOYER.validator

    def _save_employer(self, employer):
        area = int(employer.area.id) if employer.area else None
        industries_id = ([industry.id for industry in employer.industries]
                         if employer.industries else [])
        employer_in_db = MODEL(**employer.dict())
        if area:
            employer_in_db.area_id = area
        self.session.add(employer_in_db)
        for inx in industries_id:
            self.session.add(CompanyIndustryRelated(
                id_industry=inx,
                id_employer=employer.id)
            )
        self.session.commit()
        FULL_EMPLOYERS_ID.add(employer.id)

    def _check_employer(self, raw_employer: dict):
        employer_valid = self.validator.parse_obj(raw_employer)
        text_employer = BeautifulSoup(employer_valid.description or '', 'lxml')
        employer_valid.description = unicodedata.normalize(
            'NFKD', text_employer.text.strip())
        return employer_valid

    def drop_employer(self, id_company):
        self.session.query(MODEL).filter(MODEL.id == id_company).delete()
        self.session.query(CompanyIndustryRelated).filter(
            CompanyIndustryRelated.id_employer == id_company
        ).delete()
        self.session.commit()

    def get_employer_by_id(self, id_company, update=False):
        employer_in_db = int(id_company) in FULL_EMPLOYERS_ID
        if employer_in_db and not update:
            print(f'Работодатель с ID [{id_company}] уже в базе')  # В ЛОГ
            return
        endpoint = ENDPOINT + f'/{id_company}'
        try:
            employer_raw = response_employers(endpoint=endpoint, params={})
        except ValueError as e:
            print(e.args[0])  # в лог
            return
        employer_valid = self._check_employer(employer_raw)
        employer_valid = return_employer_with_rating(employer_valid)
        if employer_in_db:
            self.drop_employer(id_company)
        self._save_employer(employer_valid)

    def update_empty_employers(self):
        id_list = [idx for idx, in self.session.query(MODEL.id).filter(
            MODEL.auto_rating.is_(None))]
        for idx in id_list:
            self.get_employer_by_id(idx, update=True)

    def employer_update_inplace(self, id_company):
        employer = self.session.query(MODEL).filter(
            MODEL.id == id_company)
        rating = EmployerRating.get_employer_rating(employer.first())
        employer.update(rating)
        self.session.commit()

    def bulk_employer_update_inplace(self):
        id_list = [idx for idx, in self.session.query(MODEL.id).all()]
        for idx in tqdm(id_list):
            self.employer_update_inplace(idx)
