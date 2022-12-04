from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel as PydanticModel

import hh_api.response_validators as validator
from db.core import Base as DB_Base
import db.models as models

API = 'https://api.hh.ru/'
HEADER = {'User-Agent': 'Ilya_APP/0.1 (iaburhanov@mail.ru)'}

def get_mapping_dict(*args):
    return {x: x for x in args}


class ResponseData(Enum):
    DICT = dict
    LIST = list
    ONE = None


@dataclass
class MappingDict:
    mapping: dict
    value_key: str


@dataclass
class SettingDict:
    validator: PydanticModel.__class__
    db_model: DB_Base.__class__
    mapping: MappingDict = None
    endpoint: str = None
    response_data: ResponseData = None
    recursion_value: str = None


class Settings:
    DICTIONARIES = SettingDict(
        endpoint='dictionaries',
        response_data=ResponseData.DICT,
        validator=validator.ListDictionaries,
        db_model=models.Dictionaries,
        mapping=MappingDict(mapping={'key': 'attribute'}, value_key='value'),

    )
    CURRENCY = SettingDict(
        response_data=ResponseData.LIST,
        validator=validator.Currency,
        db_model=models.Currency
    )
    INDUSTRY = SettingDict(
        endpoint='industries',
        response_data=ResponseData.DICT,
        validator=validator.ListIndustry,
        db_model=models.Industries,
        mapping=MappingDict(mapping=get_mapping_dict('id', 'name'),
                            value_key='industries')
    )
    LANGUAGES = SettingDict(
        endpoint='languages',
        response_data=ResponseData.LIST,
        validator=validator.Languages,
        db_model=models.Languages
    )
    BUSINESS_ROLE = SettingDict(
        endpoint='professional_roles',
        response_data=ResponseData.LIST,
        validator=validator.Business,
        db_model=models.WorkRole,
        mapping=MappingDict(mapping=get_mapping_dict('id', 'name'),
                            value_key='roles')
    )
    AREAS = SettingDict(
        endpoint='areas',
        response_data=ResponseData.LIST,
        validator=validator.Areas,
        db_model=models.Areas,
        recursion_value='areas'
    )
    EMPLOYERS = SettingDict(
        endpoint='employers',
        response_data=ResponseData.LIST,
        validator=validator.Employers,
        db_model=models.Employers
    )