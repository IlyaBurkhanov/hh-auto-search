import pymorphy3
from db.save_manager import SaveManager
from hh_api.responser import Responser, Validator


VALIDATOR = Validator()  # Валидатор
RESPONSER = Responser()  # Запросы к HH
SAVE_MANAGER = SaveManager()  # Менеджер для записи

# в 3.11 ошибка. Исправление -> github.com/kmike/pymorphy2/pull/157
MORPH = pymorphy3.MorphAnalyzer()  # Приведение слов к нормальной форме
