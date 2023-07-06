from datetime import datetime
from functools import partial
from sqlalchemy.orm import Session
from tqdm import tqdm

from db.models import get_time_integer, Vacancy
from configs.config import Base, engine
from configs.dictionaries import CONFIG_SEARCH
from cv_responses.response import CVResponser
from rating.set_rating_config import (
    set_areas_rating_from_csv,
    set_industries_rating_from_csv,
    set_industry_rating_from_csv,
    set_business_role_rating,
    set_specializations_rating
)
from employers.main import Employer
from vacancies.main import SearchAndSaveVacancies
from vacancies.models import Params
from vacancy_rating.vacancy_rating import VacancyRatingCalc  # USE YOUR CLASS IT's HIDDEN ON GITHUB!!!
from workers.update_tasks import (
    update_dictionaries,
    update_areas,
    update_other,
)

Base.metadata.create_all(engine)

set_dictionaries = [
    update_dictionaries,
    update_areas,
    partial(update_other, response_type='INDUSTRY'),
    partial(update_other, response_type='LANGUAGES'),
    partial(update_other, response_type='BUSINESS_ROLE', del_key='categories'),
    partial(update_other, response_type='SPECIALIZATIONS'),
]

set_config = [
    set_areas_rating_from_csv,
    set_industries_rating_from_csv,
    set_industry_rating_from_csv,
    set_business_role_rating,
    set_specializations_rating,
]


def start_tasks(tasks: list, description=''):
    for task in tqdm(tasks, desc=description):
        task()


def get_new_vacancy():
    with Session(bind=engine) as s:
        last_date = s.query(Vacancy).order_by(Vacancy.published_at.desc()).one().published_at
    now_date = datetime.now().strftime('%Y-%m-%d')
    SearchAndSaveVacancies(
        Params(text=CONFIG_SEARCH['text'], date_from=last_date, date_to=now_date)
    ).get_vacancies_by_clusters()
    VacancyRatingCalc().calculate_vacancies_rating()


if __name__ == '__main__':
    # start_tasks(set_dictionaries, description='set_dictionaries')
    # start_tasks(set_config, description='set_config')

    # CV = CVResponser()
    # CV.vacancy_response(40379537)
    # CV.get_best_vacancies_id(limit=10, from_date=20230626, from_vacancy_id=82463500, only_vacancy_role='dev',
    #                          except_vacancy_ids=[82466390, 82467015, 82467257])
    # v = VacancyRatingCalc()
    # v.calculate_vacancies_rating()
    # v.calculate_rating(43342136)
    new_vacancy = SearchAndSaveVacancies(
        Params(
            text=CONFIG_SEARCH['text'],
            date_from='2023-07-05',
            date_to='2023-07-05',
        )
    )
    new_vacancy.get_vacancies_by_clusters()

