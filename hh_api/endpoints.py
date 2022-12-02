from enum import Enum
from dataclasses import dataclass


API = 'https://api.hh.ru/'


class ResponseData(Enum):
    ONE = dict
    MANY = list


@dataclass
class URLDict:
    endpoint: str
    response_data: ResponseData


class UseURLs:
    DICTIONARIES = URLDict(endpoint='dictionaries',
                           response_data=ResponseData.ONE)
