__all__ = ['DictionariesDB']

from .core import Base, engine

from sqlalchemy import Column, Integer, String, Text




class DictionariesDB(Base):
    __tablename__ = 'dictionaries'

    key_attr = Column(String(300), nullable=False, primary_key=True)
    id = Column(String(300), nullable=False)
    name = Column(Text)
