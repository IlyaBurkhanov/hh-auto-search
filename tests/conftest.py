import pytest
import sqlalchemy

import db.save_manager as save_manager
import employers.main as ue

result = sqlalchemy.create_engine('sqlite:///test.db', echo=False,
                                  future=True)


@pytest.fixture(autouse=True)
def monkey_db():
    mp = pytest.MonkeyPatch()
    mp.setitem(save_manager.__dict__, 'engine', result)
    mp.setitem(ue.__dict__, 'engine', result)

