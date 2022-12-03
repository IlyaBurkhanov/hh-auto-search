import pytest

import db.core as db_core
import sqlalchemy
import db.save_manager as save_manager

# from hh_api.responser import Responser
# from hh_api.endpoints import Settings


@pytest.fixture(autouse=True)
def monkey_db():
    result = sqlalchemy.create_engine('sqlite:///test.db', echo=False,
                                      future=True)
    mp = pytest.MonkeyPatch()
    mp.setitem(save_manager.__dict__, 'engine', result)
    db_core.Base.metadata.drop_all(save_manager.engine)
    db_core.Base.metadata.create_all(save_manager.engine)

