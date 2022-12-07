from functools import partial
from tqdm import tqdm

from db.core import Base, engine
from db.models import *
from workers.update_tasks import (
    update_dictionaries, update_areas, update_other
)
from workers.employers import WorkEmployers

Base.metadata.create_all(engine)

start_once_a_day = [
    update_dictionaries,
    update_areas,
    partial(update_other, response_type='INDUSTRY'),
    partial(update_other, response_type='LANGUAGES'),
    partial(update_other, response_type='BUSINESS_ROLE', del_key='categories'),
]


def start_tasks(tasks: list):
    for task in tqdm(tasks, desc='update dictionaries'):
        task()


if __name__ == '__main__':
    # start_tasks(start_once_a_day)
    WorkEmployers().get_employer_by_id(1740)

