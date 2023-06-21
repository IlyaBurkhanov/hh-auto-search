from typing import Callable
from typing_extensions import TypedDict, NotRequired
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseSettings
from sqlalchemy import create_engine


class Settings(BaseSettings):
    API: str
    HEADER: dict
    RATING_FILE: str
    SEARCH_FILE: str
    CLUSTERS_STOP_LIST_FILE: str
    UN_USE_CLUSTER_ID: list[str]
    MAX_VACANCIES_BY_REQUEST: int = 500
    VACANCY_ENDPOINT: str
    DSN: str
    ECHO: bool = True
    UN_TRUST_RATING: float = .5
    DEFAULT_AREA_RATING: int = 5
    DEFAULT_INDUSTRY_RATING: int = 50
    MAX_ITEMS_BY_GET_EMPLOYERS: int = 1500
    COEFFICIENT_PROFILE_RATING: float
    COEFFICIENT_FIELD_RATING: float
    COEFFICIENT_BENEFIT_RATING: float
    COEFFICIENT_AREA_RATING: float

    PATH_TO_EMPLOYER_RATING_MODULE: str = 'employers.employer_auto_rating'
    EMPLOYER_RATING_FUNCTION: str = 'get_employer_rating'

    class Config:
        env_file = '.env'


settings = Settings()

engine = create_engine(
    settings.DSN,
    echo=settings.ECHO,
    future=True,
    pool_recycle=3600,
    pool_pre_ping=True
)
Base = declarative_base()


class EmployerRatingDict(TypedDict):
    rating_profile: int
    rating_work_with: int
    rating_benefits: int
    rating_areas: int
    auto_rating: NotRequired[int]


RATING_RESULT_PROTOCOL = tuple[int, EmployerRatingDict]
EMPLOYER_RATING_PROTOCOL = Callable[[str], RATING_RESULT_PROTOCOL]
