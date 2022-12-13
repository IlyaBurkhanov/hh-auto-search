import json
import pymorphy3
from sqlalchemy.orm import Session

from db.core import engine
from db.models import Employers
from db.save_manager import SaveManager
from hh_api.responser import Responser, Validator


with Session(engine) as session:
    FULL_EMPLOYERS_ID = set(idx for idx, in session.query(Employers.id))

VALIDATOR = Validator()
RESPONSER = Responser()
SAVE_MANAGER = SaveManager()

# в 3.11 ошибка. Исправление -> github.com/kmike/pymorphy2/pull/157
MORPH = pymorphy3.MorphAnalyzer()

with open('config_for_rating/employer_rating_config.json',
          'r', encoding='utf8') as file:
    RATING_CONFIG = json.load(file)
