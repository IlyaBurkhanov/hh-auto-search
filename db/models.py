
__all__ = ['Dictionaries', 'DictionariesKey', 'Currency']

from sqlalchemy.orm import relationship

from .core import Base
from .instruments import RelatedMapping

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, PrimaryKeyConstraint, Boolean,
    Float
)

Base.__table_args__ = {'sqlite_autoincrement': True}
Base.relate = None


class DictionariesKey(Base):
    __tablename__ = 'dictionaries_keys'
    # __table_args__ = {'sqlite_autoincrement': True}

    id = Column(Integer, primary_key=True)
    attribute = Column(String(300), nullable=False)
    dictionaries = relationship('Dictionaries', backref='dict')


class Dictionaries(Base):
    __tablename__ = 'dictionaries'
    __table_args__ = (
        PrimaryKeyConstraint('attr_key', 'id'),
    )
    relate = RelatedMapping(model=DictionariesKey,
                            mapping={'key': 'attribute'})

    attr_key = Column(Integer, ForeignKey('dictionaries_keys.id'))
    id = Column(String(300), nullable=False)
    name = Column(Text)


class Currency(Base):
    __tablename__ = 'currency'
    # __table_args__ = {'sqlite_autoincrement': True}

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    abbr = Column(String(8))
    name = Column(String(100))
    default = Column(Boolean, nullable=False)
    rate = Column(Float, nullable=False)
    in_use = Column(Boolean, nullable=False)
