import pytest
from hh_api.responser import Responser
from hh_api.endpoints import UseURLs
from sqlalchemy import create_engine
from db.core import Base
from db.models import *


@pytest.fixture(scope='function')
def response_dictionary():
    use_urls = UseURLs.DICTIONARIES
    request = Responser().get_response(use_urls.endpoint)
    assert request.status_code == 200
    return request


@pytest.fixture(scope='session')
def db():
    engine = create_engine('sqlite:///test.db', echo=False, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

