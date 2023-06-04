from functools import partial

from tqdm import tqdm

from configs.config import Base, engine
from rating.set_rating_config import (
    set_areas_rating_from_csv,
    set_industries_rating_from_csv,
    set_industry_rating_from_csv,
    set_business_role_rating,
    set_specializations_rating
)
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


if __name__ == '__main__':
    start_tasks(set_dictionaries, description='set_dictionaries')
    start_tasks(set_config, description='set_config')
    # Employer().get_employer_by_id(1740, update=True)
    # UpdateEmployers().update_employers(page_per_list=100, with_vacancies=True,
    #                                    area=1, employer_type='company',
    #                                    text='банк')
    # employer = Employer()
    # employer.update_empty_employers()
    # with Session(engine) as session:
    #     q = [x for x, in session.query(model.Employers.id).filter(
    #         model.Employers.auto_rating).all()]
    # errs = []
    # print(q)
    # for x in q:
    #     try:
    #         employer.get_employer_by_id(x, update=True)
    #     except Exception as e:
    #         print(e.args[0], x)
    #         errs.append(x)
    #     time.sleep(0.3)
    # print(errs)
