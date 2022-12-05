from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('sqlite:///hh.db', echo=False, future=True)

Base = declarative_base()
