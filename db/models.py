__all__ = [
    'Dictionaries', 'DictionariesKey', 'Currency', 'Industry', 'Industries',
    'Languages', 'Business', 'WorkRole', 'Areas', 'Employers', 'AreasRating',
    'CompanyIndustryRelated', 'IndustryRating', 'IndustriesRating',
    'BusinessRating', 'RoleRating', 'Specialization', 'SpecializationsDetails',
    'SpecializationRating', 'SpecializationsRating'
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


class Specialization(Base):
    __tablename__ = 'specialization'

    id = Column(Integer, primary_key=True)
    name = Column(String(500), nullable=False)
    specializations = relationship('SpecializationsDetails',
                                   backref='specialization')


class SpecializationsDetails(Base):
    __tablename__ = 'specializations_details'
    __table_args__ = (PrimaryKeyConstraint('specialization_key', 'id'),)
    relate = RelatedMapping(model=Specialization, fk='specialization_key')

    specialization_key = Column(Integer, ForeignKey('specialization.id'))
    id = Column(String(30), nullable=False)
    name = Column(String(500), nullable=False)
    laboring = Column(Boolean, default=False)


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
    rating_profile = Column(Integer)
    rating_work_with = Column(Integer)
    rating_benefits = Column(Integer)
    rating_areas = Column(Integer)
    auto_rating = Column(Integer)
    manual_rating = Column(Integer)

    area = relationship('Areas', backref='employers')
    industries = relationship('Industries', secondary='company_industry',
                              backref='employers')


class AreasRating(Base):
    __tablename__ = 'areas_rating'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    my_rating = Column(Integer, default=5)


class IndustryRating(Base):
    __tablename__ = 'industry_rating'

    id = Column(Integer, primary_key=True)
    name = Column(String(500))
    my_rating = Column(Integer, default=50)


class IndustriesRating(Base):
    __tablename__ = 'industries_rating'

    id = Column(String(10), primary_key=True)
    name = Column(String(2000))
    my_rating = Column(Integer, default=50)


class BusinessRating(Base):
    __tablename__ = 'business_rating'

    id = Column(Integer, primary_key=True)
    name = Column(String(500))
    my_rating = Column(Integer, default=2)


class RoleRating(Base):
    __tablename__ = 'role_rating'
    __table_args__ = (PrimaryKeyConstraint('business_id', 'id'),)

    business_id = Column(Integer, ForeignKey('business_rating.id'),
                         nullable=True)
    id = Column(Integer)
    name = Column(String(500))
    my_rating = Column(Integer, default=2)


class SpecializationRating(Base):
    __tablename__ = 'specialization_rating'

    id = Column(Integer, primary_key=True)
    name = Column(String(500))
    my_rating = Column(Integer, default=50)


class SpecializationsRating(Base):
    __tablename__ = 'specializations_rating'
    __table_args__ = (PrimaryKeyConstraint('specialization_id', 'id'),)

    specialization_id = Column(Integer, ForeignKey('specialization_rating.id'),
                               nullable=True)
    id = Column(String(30), nullable=False)
    name = Column(String(500))
    my_rating = Column(Integer, default=50)
