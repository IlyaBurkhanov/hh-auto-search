import json

from employers.main import Employer
from vacancies.request_vacancies import Params
from vacancies.response_model import ResponseVacancy
from configs.conf import RESPONSER

JSON_FILE = 'config_for_rating/search_config.json'  # ENV

with open(JSON_FILE, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

DROP_PARAMS = CONFIG.pop('drop_params')


class JobSearch:
    pass