import csv
from typing import List, Dict, Mapping, Callable

from sqlalchemy.orm import Session

from db.core import engine, Base
from db.models import AreasRating, IndustryRating, IndustriesRating


def read_end_parse(what_parse: str, column_name_pos: Mapping[str, int],
                   type_dict: Mapping[str, Callable]) -> List[Dict]:
    def parse(row):
        return {key: type_dict.get(key, lambda x: x)(row[val])
                for key, val in column_name_pos.items()}

    with open(f'config_for_rating/{what_parse}_rating.csv', 'r',
              encoding='utf-8-sig') as file:
        csv_reader = csv.reader(file, delimiter=';')
        next(csv_reader)
        return [parse(row) for row in csv_reader]


def drop_and_creat_table(model: Base.metadata) -> None:
    Base.metadata.drop_all(engine, tables=[model.__table__])
    Base.metadata.create_all(engine, tables=[model.__table__])


def save_rating(model: Base.metadata, rating_list: List[Dict]) -> None:
    with Session(engine) as session:
        session.bulk_insert_mappings(model, rating_list)
        session.commit()


def save_worker(model, what_parse, column_name_pos, type_dict) -> None:
    drop_and_creat_table(model)
    rating_list = read_end_parse(what_parse, column_name_pos, type_dict)
    save_rating(model, rating_list)


def set_areas_rating_from_csv():
    """
    Обновляем рейтинги местоположения работодателя.
    Поля csv id/parent_id/name/rating.
    Рейтинг в промежутке от 0 до 10 включительно.
    """
    model = AreasRating
    what = 'area'
    column_name_pos = {'id': 0, 'name': 2, 'my_rating': 3}
    type_dict = {'id': int, 'my_rating': int}
    save_worker(model, what, column_name_pos, type_dict)


def set_industry_rating_from_csv():
    """
    Обновляем рейтинг сферы деятельности.
    Поля csv id/name/rating.
    Рейтинг в промежутке от 0 до 100 включительно.
    """
    model = IndustryRating
    what = 'industry'
    column_name_pos = {'id': 0, 'name': 1, 'my_rating': 2}
    type_dict = {'id': int, 'my_rating': int}
    save_worker(model, what, column_name_pos, type_dict)


def set_industries_rating_from_csv():
    """
    Обновляем рейтинг области сферы деятельности.
    Поля csv id/name/rating.
    Рейтинг в промежутке от 0 до 100 включительно.
    """
    model = IndustriesRating
    what = 'industries'
    column_name_pos = {'id': 0, 'name': 1, 'my_rating': 2}
    type_dict = {'my_rating': int}
    save_worker(model, what, column_name_pos, type_dict)