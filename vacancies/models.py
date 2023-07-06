from datetime import date, datetime
from enum import Enum
from urllib.parse import parse_qsl, urlparse

from bs4 import BeautifulSoup
from pydantic import BaseModel, validator, Field

from configs.workers import MORPH

# Извлекаемые поля из объектов связанных с моделью
OBJECT_FIELD = {
    'department': 'name',  # Имя департамента
    'area': 'id',  # id местоположения
    'type_': 'id',  # тип вакансии
    'employer': 'id',  # ИД работодателя
    'schedule': 'id',  # График работы
    'counters': 'responses',  # Количество откликов на вакансию
    'experience': 'id',  # Требуемый опыт работы
    'employment': 'id',  # Тип занятости
    'billing_type': 'id',  # Тип вакансии для работодателя (платная или нет)
    'test': 'required',  # Отклик без прохождения теста?
}


class OrderVacancy(Enum):
    """Детали в справочнике по полю vacancy_search_order"""
    salary_desc = 'по убыванию дохода'
    salary_asc = 'по возрастанию дохода'
    relevance = 'по соответствию'


class BaseModelWithDict(BaseModel):
    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        keys = list(result.keys())
        for key in keys:
            if result[key] is None:
                result.pop(key, None)
        return result


class Params(BaseModelWithDict):
    text: str  # hh.ru/article/1175 - параметры запросов
    area: list[int] = None  # id локаций для поиска из справочника
    industry: list[int | str] = None  # id индустрии или ее подвида
    employer_id: list[int] = None  # id работодателей
    currency: str = None  # Код валюты из справочника. Использовать с salary
    salary: int = None  # ЗП с этой вилкой или без указания ЗП. DEFAULT: RUR
    only_with_salary: bool = False  # Только с указанием ЗП
    date_from: str = None  # (YYYY-MM-DD или YYYY-MM-DDThh:mm:ss±hhmm)
    date_to: str = None  # Публикация С/ПО. Нельзя использовать вместе с period
    period: int = None  # Макс число дней осуществления поиска. DEFAULT: 30
    order_by: OrderVacancy = OrderVacancy.relevance.name  # Сортировка
    clusters: bool = False  # Выдает кластеры в поисковой выдаче.
    per_page: int = Field(le=100, ge=0, default=100)  # Число вакансий на лист
    responses_count_enabled: bool = True  # Количеством откликов на вакансию
    professional_role: int | list[int] = None  # id проф ролей
    page: int = 0  # Страница в пагинации

    @validator('date_from', 'date_to', pre=True)
    def check_date(cls, value):
        format_date = '%Y-%m-%d'
        if isinstance(value, (date, datetime)):
            return value.strftime(format_date)
        return value

    @validator('period')
    def check_period(cls, value, values):
        if value is None or (values['date_from'] is None and values['date_to'] is None):
            return value
        raise ValueError('period не используется вместе с date_from и date_to')


class Salary(BaseModel):
    from_: int | float = Field(default=None, alias='from')
    to: int | float = None
    gross: bool | None = True
    currency: str = None


class KeySkill(BaseModel):
    name: str


class ProfRole(BaseModel):
    id: int


class Specializations(BaseModel):
    id: str = None
    profarea_id: int = None


class Languages(BaseModel):
    id: str
    level: str = None

    @validator('id', pre=True)
    def check_level(cls, v):
        return v['id'] if v else None


class ResponseVacancy(BaseModel):
    id: int
    premium: bool = False  # Премиальная?
    name: str = None  # Название
    department: str = None  # Департамент работодателя
    has_test: bool = False  # Прикрепленный тест к вакансии
    response_letter_required: bool = False  # сообщение при отклике ?
    area: int = None  # id местоположения
    salary: Salary = None  # ЗП вилка
    # на close и direct нет смысла откликаться
    type_: str = Field(default='closed', alias='type')
    response_url: str = None  # Внешний сайт, если нельзя откликаться
    published_at: str = None  # Дата публикации
    created_at: str = None  # Дата создания вакансии
    archived: bool = False  # В Архиве?
    employer: int = None  # ID Работодателя
    snippet: str = ''  # Ключевые найденные слова в str, через пробел
    schedule: str = None  # График работы
    counters: int = None
    description: str = None  # Описание
    branded_description: str = None  # Красивое описание
    key_skills: list[KeySkill] = None
    experience: str = None
    employment: str = None  # Тип занятости
    billing_type: str = None  # Тип вакансии для работодателя (платная, нет)
    allow_messages: bool = None  # Писать после приглашения, отзыва
    accept_incomplete_resumes: bool = None  # отзыв неполным резюме?
    professional_roles: list[ProfRole] = None  # Проф роли
    specializations: list[Specializations] = None  # Специализации
    hidden: bool = False  # Скрытая?
    quick_responses_allowed: bool = False  # Быстрый отклик?
    test: bool = None  # Надо проходить тест?

    @validator('published_at', 'created_at', pre=True)
    def check_date(cls, v):
        if v is None:
            return v
        return str(v)[:10]

    @validator('snippet', pre=True)
    def check_snippet(cls, v: str | dict):
        """
        :return: Ключевые слова требуемых навыков в нормальной форме
        """
        if v is None:
            return ''
        if isinstance(v, str):
            return v
        result = set()
        for text in ['requirement', 'responsibility']:
            for words in BeautifulSoup(v.get(text) or '', 'lxml').find_all('highlighttext'):
                for word in words.text.lower().split():
                    result.add(MORPH.normal_forms(word)[0])
        return ' '.join(result)

    @validator('description', 'branded_description', pre=True)
    def check_description(cls, v):
        if v is None:
            return ''
        return BeautifulSoup(v or '', 'lxml').text

    @validator(*OBJECT_FIELD, pre=True)
    def check_department(cls, v, config, field):
        """
        Извлекаем только полезные данные из объекта.
        Чтобы не писать в БД и не анализировать связанные с данным объектом
        модели.
        :return: Полезное поле из связанного объекта
        """
        if v is None:
            return v
        return config.return_value_from_object(v, field.name)

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        keys = list(result.keys())
        for key in keys:
            if result[key] is None:
                result.pop(key, None)
        return result

    class Config:
        @classmethod
        def return_value_from_object(cls, value_dict, field_name):
            field = OBJECT_FIELD[field_name]
            return value_dict.get(field)


class ClustersParams(BaseModelWithDict):
    # Модель используется только при нарезке запросов, большом числе найденных вакансий
    clusters: bool = None
    date_from: str = None
    date_to: str = None
    per_page: int = 100
    salary: int = None
    text: str = None
    area: int | list[int] = None
    only_with_salary: bool = None
    specialization: int = None
    industry: int = None
    experience: str = None  # Опыт работы
    schedule: str = None  # График
    label: str = None  # Ключевые исключения
    professional_role: int = None  # Должность
    education: str = None


class ClusterItem(BaseModel):
    name: str
    count: int
    params: ClustersParams = Field(default=None, alias='url')

    @validator('params', pre=True)
    def return_params(cls, v, values):
        if not v:
            return None
        request_params = {key: value[0] if len(value) == 1 else value for key, value in parse_qsl(urlparse(v).query)}
        # if values['count'] <= settings.MAX_VACANCIES_BY_REQUEST:
        #     request_params['clusters'] = None
        return request_params


class Clusters(BaseModel):
    name: str
    id: str
    items: list[ClusterItem] = None


class FindVacancies(BaseModel):
    items: list[ResponseVacancy]
    found: int
    pages: int
    per_page: int
    page: int
    clusters: list[Clusters] = None
