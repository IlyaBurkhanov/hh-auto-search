
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseSettings, validator
from sqlalchemy import create_engine


class Settings(BaseSettings):
    API: str
    HEADER: dict
    RATING_FILE: str
    SEARCH_FILE: str
    UN_USE_CLUSTER_ID: list[str]
    MAX_VACANCIES_BY_REQUEST: int = 500
    VACANCY_ENDPOINT: str
    DSN: str
    ECHO: bool = True
    UN_TRUST_RATING: float = .5
    DEFAULT_AREA_RATING: int = 5
    DEFAULT_INDUSTRY_RATING: int = 50
    MAX_ITEMS_BY_GET_EMPLOYERS: int = 1500

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
