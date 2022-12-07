__all__ = [
    'Dictionaries', 'DictionariesKey', 'Currency', 'Industry', 'Industries',
    'Languages', 'Business', 'WorkRole', 'Areas', 'Employers',
    'CompanyIndustryRelated',
]

from sqlalchemy.orm import relationship
from dataclasses import dataclass
from .core import Base

from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, PrimaryKeyConstraint, Boolean,
    Float
)

Base.__table_args__ = {'sqlite_autoincrement': True}
Base.relate = None


@dataclass
class RelatedMapping:
    fk: str
    model: Base.metadata


class DictionariesKey(Base):
    __tablename__ = 'dictionaries_keys'

    id = Column(Integer, primary_key=True)
    attribute = Column(String(300), nullable=False)
    dictionaries = relationship('Dictionaries', backref='dict')


class Dictionaries(Base):
    __tablename__ = 'dictionaries'
    __table_args__ = (PrimaryKeyConstraint('attr_key', 'id'),)

    relate = RelatedMapping(model=DictionariesKey,
                            fk='attr_key')

    attr_key = Column(Integer, ForeignKey('dictionaries_keys.id'))
    id = Column(String(300), nullable=False)
    name = Column(Text)


class Currency(Base):
    __tablename__ = 'currency'

    id = Column(Integer, primary_key=True)
    code = Column(String(8), nullable=False)
    abbr = Column(String(20))
    name = Column(String(100))
    default = Column(Boolean, nullable=False)
    rate = Column(Float, nullable=False)
    in_use = Column(Boolean, nullable=False)


class Industry(Base):
    __tablename__ = 'industry'

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    industries = relationship('Industries', backref='industry')


class Industries(Base):
    __tablename__ = 'industries'
    __table_args__ = (PrimaryKeyConstraint('industry_key', 'id'),)
    relate = RelatedMapping(model=Industry,
                            fk='industry_key')

    industry_key = Column(Integer, ForeignKey('industry.id'))
    id = Column(String(30))
    name = Column(Text)


class Languages(Base):
    __tablename__ = 'languages'

    id = Column(String(10), primary_key=True)
    name = Column(String(30))


class Business(Base):
    __tablename__ = 'business'

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    role = relationship('WorkRole', backref='role')


class WorkRole(Base):
    __tablename__ = 'work_role'
    __table_args__ = (PrimaryKeyConstraint('business_key', 'id'),)
    relate = RelatedMapping(model=Business,
                            fk='business_key')

    business_key = Column(Integer, ForeignKey('business.id'))
    id = Column(Integer)
    name = Column(Text, nullable=False)
    accept_incomplete_resumes = Column(Boolean)
    is_default = Column(Boolean)


class Areas(Base):
    __tablename__ = 'areas'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('areas.id'), nullable=True)
    name = Column(String(100))


class CompanyIndustryRelated(Base):
    __tablename__ = 'company_industry'
    __table_args__ = (PrimaryKeyConstraint('id_industry', 'id_employer'),)

    id_industry = Column(String(30), ForeignKey('industries.id'),
                         nullable=True)
    id_employer = Column(Integer, ForeignKey('employers.id'),
                         nullable=True)


class Employers(Base):
    __tablename__ = 'employers'

    id = Column(Integer, primary_key=True)
    name = Column(Text, default='')
    open_vacancies = Column(Integer, default=0)
    trusted = Column(Boolean, default=False)
    type = Column(String(100))
    description = Column(Text)
    site_url = Column(String(500))
    alternate_url = Column(String(500))
    area_id = Column(Integer, ForeignKey('areas.id'), nullable=True)

    area = relationship('Areas', backref='employers')
    industries = relationship('Industries', secondary='company_industry',
                              backref='employers')
