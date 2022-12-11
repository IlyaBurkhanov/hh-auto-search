from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine('sqlite:///hh.db', echo=False, future=True,
                       pool_recycle=3600, pool_pre_ping=True)

Base = declarative_base()
