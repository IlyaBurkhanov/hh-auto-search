from sqlalchemy.orm import Session

from configs.config import settings, engine, EMPLOYER_RATING_PROTOCOL, EmployerRatingDict
from db.models import IndustriesRating, IndustryRating, AreasRating
from hh_api.response_validators import Employer


def final_rating(text_rating, area_rating, industry_rating):
    result = (area_rating / 10) * (industry_rating / 100) * text_rating
    return int(round(result))


class CalcEmployerRating:
    __CalcRating = None
    default_area_rating = settings.DEFAULT_AREA_RATING
    default_industry_rating = settings.DEFAULT_INDUSTRY_RATING

    def __new__(cls, func_employer_rating):
        if cls.__CalcRating is None:
            cls.__CalcRating = super().__new__(cls)
        return cls.__CalcRating

    def __init__(self, func_employer_rating: EMPLOYER_RATING_PROTOCOL):
        self.func_employer_rating = func_employer_rating  # DI - use our func of calculate rating by description!
        with Session(engine) as session:
            self.areas = self.get_ratings(session, AreasRating)
            self.industry = self.get_ratings(session, IndustryRating)
            self.industries = self.get_ratings(session, IndustriesRating)

    def get_area_rating(self, area) -> int:
        if area is None or area.id is None:
            return self.default_area_rating
        return self.areas.get(area.id, self.default_area_rating)

    def rating_for_industry(self, industry_id: int) -> int:
        return self.industry.get(industry_id, None)

    def rating_for_industries(self, industry_id: str) -> int:
        rating = self.industries.get(industry_id, None)
        if rating is None:
            return self.rating_for_industry(int(float(industry_id)))
        return rating

    def get_industry_rating(self, industries: list) -> int:
        func = {int: self.rating_for_industry, str: self.rating_for_industries}
        index_list = [industry.id for industry in industries if industry.id]
        result = [rating for rating in (func[type(idx)](idx) for idx in index_list) if rating is not None]
        if len(result) == 0:
            return self.default_industry_rating
        return max(result)

    def get_employer_rating(self, employer: Employer) -> EmployerRatingDict:
        text_rating, result_dict = self.func_employer_rating(employer.description)
        area_rating = self.get_area_rating(employer.area)
        industry_rating = self.get_industry_rating(employer.industries)
        rating = final_rating(text_rating, area_rating, industry_rating)
        rating *= 1 if employer.trusted else settings.UN_TRUST_RATING
        result_dict['auto_rating'] = rating
        return result_dict

    @staticmethod
    def get_ratings(session, model):
        return {obj.id: obj.my_rating for obj in session.query(model).all()}
