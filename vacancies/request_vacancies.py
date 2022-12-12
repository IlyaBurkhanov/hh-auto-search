from enum import Enum
from pydantic import BaseModel, validator, Field
from datetime import date, datetime
from typing import List, Union
# from sqlalchemy.orm import Session

# from db.core import engine
# from db.models import Currency
#
# with Session(engine) as session:
#     CURRENCIES = {code: rate for code, rate in
#                   session.query(Currency.code, Currency.rate).all()}
#
# Currency = Enum('Currency', CURRENCIES)


class OrderVacancy(Enum):
    """Детали в справочнике по полю vacancy_search_order"""
    salary_desc = 'по убыванию дохода'
    salary_asc = 'по возрастанию дохода'
    relevance = 'по соответствию'


class Params(BaseModel):
    text: str = ''  # hh.ru/article/1175 - параметры запросов
    area: List[int] = None  # id локаций для поиска из справочника
    industry: List[Union[int, str]] = None  # id индустрии или ее подвида
    employer_id: List[int] = None  # id работодателей
    currency: str = 'RUR'  # Код валюты из справочника. Использовать с salary
    salary: int = 100_000  # ЗП с этой вилкой или без указания ЗП. DEFAULT: RUR
    only_with_salary: bool = False  # Только с указанием ЗП
    date_from: str = None  # (YYYY-MM-DD или YYYY-MM-DDThh:mm:ss±hhmm)
    date_to: str = None  # Публикация С/ПО. Нельзя использовать вместе с period
    period: int = None  # Макс число дней осуществления поиска. DEFAULT: 30
    order_by: OrderVacancy = OrderVacancy.relevance.name  # Сортировка
    clusters: bool = True  # Выдает кластеры в поисковой выдаче.
    per_page: int = Field(le=100, ge=1, default=100)  # Число вакансий на лист
    responses_count_enabled: bool = True  # Количеством откликов на вакансию
    professional_role: List[int] = None  # id проф ролей
    page: int = 0  # Страница в пагинации

    @validator('date_from', 'date_to', pre=True)
    def check_date(cls, value):
        format_date = '%Y-%m-%d'
        if isinstance(value, (date, datetime)):
            return value.strftime(format_date)
        elif isinstance(value, str):
            datetime.strptime(value, format_date)
            return value
        return value

    @validator('period')
    def check_period(cls, value, values):
        if value is None or (values['date_from'] is None
                             and values['date_to'] is None):
            return value
        raise ValueError('period не используется вместе с date_from и '
                         'date_to')

    def dict(self, *args, drop: list = None, **kwargs):
        result = super().dict(*args, **kwargs)
        keys = list(result.keys())
        drop = drop or []
        for key in keys:
            if result[key] is None or key in drop:
                result.pop(key, None)
        return result
