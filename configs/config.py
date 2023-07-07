from typing import Callable

from pydantic import BaseSettings, SecretStr
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from typing_extensions import TypedDict, NotRequired


class Settings(BaseSettings):
    # API and dictionary ENVS
    API: str
    HEADER: dict
    RATING_FILE: str
    SEARCH_FILE: str
    CLUSTERS_STOP_LIST_FILE: str
    UN_USE_CLUSTER_ID: list[str]
    MAX_VACANCIES_BY_REQUEST: int = 500
    VACANCY_ENDPOINT: str
    UN_TRUST_RATING: float = .5
    DEFAULT_AREA_RATING: int = 5
    DEFAULT_INDUSTRY_RATING: int = 50
    MAX_ITEMS_BY_GET_EMPLOYERS: int = 1500
    COEFFICIENT_PROFILE_RATING: float
    COEFFICIENT_FIELD_RATING: float
    COEFFICIENT_BENEFIT_RATING: float
    COEFFICIENT_AREA_RATING: float
    RATING_PATH: str

    # DB
    DSN: str
    ECHO: bool = True

    # RATING ENV
    PATH_TO_EMPLOYER_RATING_MODULE: str = 'employers.employer_auto_rating'
    EMPLOYER_RATING_FUNCTION: str = 'get_employer_rating'

    # ACCESS ENV
    CLIENT_ID: SecretStr
    CLIENT_SECRET: SecretStr
    GRANT_TYPE_AUTH: str = 'authorization_code'
    GRANT_TYPE_REFRESH: str = 'refresh_token'
    TOKEN_TYPE: str = 'Bearer'
    URL_MANUAL_AUTH: str = 'https://hh.ru/oauth/authorize'
    URL_GET_TOKEN: str = 'https://hh.ru/oauth/token'
    HEADER_GET_TOKEN: dict = {'Content-Type': 'application/x-www-form-urlencoded'}
    REDIRECT_URI: str = 'localhost'
    ACCESS_DATA_FILE: str
    URL_ALL_RESUMES: str = 'https://api.hh.ru/resumes/mine'

    # MESSAGES
    MESSAGE_RU_FILE: str
    MESSAGE_US_FILE: str

    HEADER_VACANCY_REQUEST: dict = {'Content-Type': 'multipart/form-data'}
    URL_FOR_REQUEST_CV: str = 'https://hh.ru/negotiations'

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
