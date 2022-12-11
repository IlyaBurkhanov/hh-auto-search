# from collections import namedtuple
from sqlalchemy.orm import Session

from db.core import engine
from db.models import IndustriesRating, IndustryRating, AreasRating
from employers.employer_auto_rating import get_employ_rating


UN_TRUST_COFF = 0.5  # Умножаем фин рейтинг если компания не проверена!


def final_rating(text_rating, area_rating, industry_rating):
    result = (area_rating / 10) * (industry_rating / 100) * text_rating
    return int(round(result))


class CalcEmployerRating:
    _CalcRating = None
    # !!!! Хардкод потом убрать !!!!
    default_area_rating = 5
    default_industry_rating = 50

    def __new__(cls):
        if cls._CalcRating is None:
            cls._CalcRating = super().__new__(cls)
        return cls._CalcRating

    def __init__(self):
        with Session(engine) as session:
            self.areas = self.get_ratings(session, AreasRating)
            self.industry = self.get_ratings(session, IndustryRating)
            self.industries = self.get_ratings(session, IndustriesRating)

    def get_area_rating(self, area):
        if area is None or area.id is None:
            return self.default_area_rating
        return self.areas.get(area.id, self.default_area_rating)

    def rating_for_industry(self, industry_id: int):
        return self.industry.get(industry_id, None)

    def rating_for_industries(self, industry_id: str):
        rating = self.industries.get(industry_id, None)
        if rating is None:
            return self.rating_for_industry(int(float(industry_id)))
        return rating

    def get_industry_rating(self, industries: list):
        func = {int: self.rating_for_industry,
                str: self.rating_for_industries}
        index_list = [industry.id for industry in industries if industry.id]
        result = [rating for rating in
                  (func[type(inx)](inx) for inx in index_list)
                  if rating is not None]
        if len(result) == 0:
            return self.default_industry_rating
        return max(result)

    def get_employer_rating(self, employer):
        text_rating, result_dict = get_employ_rating(employer.description)
        area_rating = self.get_area_rating(employer.area)
        industry_rating = self.get_industry_rating(employer.industries)
        rating = final_rating(text_rating, area_rating, industry_rating)
        rating *= 1 if employer.trusted else UN_TRUST_COFF
        result_dict['auto_rating'] = rating
        return result_dict

    @staticmethod
    def get_ratings(session, model):
        return {obj.id: obj.my_rating for obj in session.query(model).all()}
