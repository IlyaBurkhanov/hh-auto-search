import pymorphy3

from bs4 import BeautifulSoup
from pydantic import BaseModel, validator, Field
from typing import Union

# в 3.11 ошибка. Исправление -> github.com/kmike/pymorphy2/pul
MORPH = pymorphy3.MorphAnalyzer()
OBJECT_FIELD = {
    'department': 'name',
    'area': 'id',
    'type_': 'name',
    'employer': 'id',
    'schedule': 'id',
    'counters': 'responses',
}


class Salary(BaseModel):
    from_: Union[int, float] = Field(default=None, alias='from')
    to: Union[int, float] = None
    gross: bool = True
    currency: str = None


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
    type_: str = Field(default='close', alias='type')
    response_url: str = None  # Внешний сайт, если нельзя откликаться
    published_at: str = None  # Дата публикации
    created_at: str = None  # Дата создания вакансии
    archived: bool = False  # В Архиве?
    employer: int  # ID Работодателя
    snippet: str = ''  # Ключевые найденные слова в str, через пробел
    schedule: str = None  # График работы
    counters: int = None
    description: str = None  # Обновить потом!

    @validator('published_at', 'created_at', pre=True)
    def check_date(cls, v):
        if v is None:
            return v
        return str(v)[:10]

    @validator('snippet', pre=True)
    def check_snippet(cls, v):
        if v is None:
            return ''
        result = set()
        for text in ['requirement', 'responsibility']:
            for words in BeautifulSoup(
                    v.get(text, ''), 'lxml').find_all('highlighttext'):
                for word in words.text.lower().split():
                    result.add(MORPH.normal_forms(word)[0])
        return ' '.join(result)

    @validator(*OBJECT_FIELD, pre=True)
    def check_department(cls, v, config, field):
        if v is None:
            return v
        return config.return_value_from_object(v, field.name)

    class Config:
        use_obj_field = OBJECT_FIELD

        @classmethod
        def return_value_from_object(cls, value_dict, field_name):
            field = cls.use_obj_field[field_name]
            return value_dict.get(field)
