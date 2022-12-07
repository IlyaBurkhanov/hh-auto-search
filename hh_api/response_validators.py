from pydantic import BaseModel, validator, AnyUrl, Field
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
    name: str
    default: bool
    rate: float
    in_use: bool


class ListCurrency(BaseModel):
    key: List[Currency]


class Industry(BaseModel):
    id: str
    name: str


class ListIndustry(BaseModel):
    id: int
    name: str
    industries: List[Industry]


class Languages(BaseModel):
    id: str
    name: str


class WorkRole(BaseModel):
    id: int
    name: str
    accept_incomplete_resumes: bool
    is_default: bool


class Business(BaseModel):
    id: int
    name: str
    roles: List[WorkRole]


class Areas(BaseModel):
    id: int
    parent_id: int = None
    name: str
    areas: List['Areas'] = None


class Employers(BaseModel):
    id: int
    name: str
    open_vacancies: int


class Employer(Employers):
    description: str
    type: str
    trusted: bool = False
    site_url: AnyUrl = None
    alternate_url: AnyUrl = None
    area: Areas = None
    industries: List[Industry] = Field(default_factory=list)

    class Config:
        fields = {
            'area': {'exclude': True},
            'industries': {'exclude': True}
        }

