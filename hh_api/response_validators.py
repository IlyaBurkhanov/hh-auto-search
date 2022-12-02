from pydantic import BaseModel, validator
from typing import List


class Dictionaries(BaseModel):
    id: str
    name: str = None

    @validator('name', always=True)
    def set_name(cls, name, values):
        if not name:
            return values['id']
        return name


class ListDictionaries(BaseModel):
    key: str
    value: List[Dictionaries]


class Currency(BaseModel):
    code: str
    abbr: str
    default: bool
    rate: float
    in_use: bool


class ListCurrency(BaseModel):
    key: List[Currency]
