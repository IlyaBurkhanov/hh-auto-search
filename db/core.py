from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm.decl_api import DeclarativeMeta
engine = create_engine('sqlite:///hh.db', echo=True, future=True)

Base = declarative_base()
