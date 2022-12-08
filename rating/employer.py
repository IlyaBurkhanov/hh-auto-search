# from collections import namedtuple
from sqlalchemy.orm import Session

from db.core import engine
from db.models import IndustriesRating, IndustryRating, AreasRating


class CalcEmployerRating:
    _CalcRating = None
    # !!!! Хардкод потом убрать !!!!
    default_area_rating = 5
    default_industry_rating = 50
    default_industries_rating = 50

    def __new__(cls):
        if cls._CalcRating is None:
            cls._CalcRating = super().__new__(cls)
        return cls._CalcRating

    def __init__(self):
        with Session(engine) as session:
            self.areas = self.get_ratings(session, AreasRating)
            self.industry = self.get_ratings(session, IndustryRating)
            self.industries = self.get_ratings(session, IndustriesRating)

    @staticmethod
    def get_ratings(session, model):
        return {obj.id: obj.my_rating for obj in session.query(model).all()}



