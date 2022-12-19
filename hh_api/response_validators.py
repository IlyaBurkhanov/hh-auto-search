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
    description: str = None
    type: str = None
    trusted: bool = False
    site_url: str = None
    alternate_url: str = None
    area: Areas = None
    industries: List[Industry] = Field(default_factory=list)
    rating_profile: int = None
    rating_work_with: int = None
    rating_benefits: int = None
    rating_areas: int = None
    manual_rating: int = None
    auto_rating: int = None

    def dict(self, *args, **kwargs):
        result = super().dict(*args, **kwargs)
        for val in self.__class__.Config.exclude:
            result.pop(val, None)
        return result

    class Config:
        exclude = {'area', 'industries'}


class Specializations(BaseModel):
    id: str
    name: str
    laboring: bool = False


class Specialization(BaseModel):
    id: int
    name: str
    specializations: List[Specializations] = None
