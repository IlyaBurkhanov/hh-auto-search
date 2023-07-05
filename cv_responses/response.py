from datetime import datetime
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, case


from authorization.authorize import get_token_header, get_access_token, refresh_token
from db.models import Employers, ResponseCV, Vacancy, VacancyRating, VacancyRoles
from configs.config import engine


class CVResponser:

    def __init__(self):
        self._token = get_access_token()
        self.session = Session(bind=engine)
        self.headers = get_token_header(self._token)

    def __del__(self):
        try:
            self.session.close()
        except ProgrammingError:
            pass

    def refresh_token(self) -> None:
        self._token = refresh_token(self._token)
        self.headers = get_token_header(self._token)

    def add_vacancy_role(
            self,
            role_name: str,
            cv_id_rus: str,
            cv_id_us: str,
            role_description: str = None,
    ) -> None:
        role = VacancyRoles(
            role_name=role_name,
            role_description=role_description,
            cv_id_rus=cv_id_rus,
            cv_id_us=cv_id_us,
        )
        self.session.add(role)
        self.session.commit()

    def update_vacancy_role(
            self,
            role_name: str,
            cv_id_rus: str = None,
            cv_id_us: str = None,
            role_description: str = None,
    ) -> None:
        role = self.session.get(VacancyRoles, role_name)
        if role is not None:
            role.cv_id_rus = cv_id_rus or role.cv_id_rus
            role.cv_id_us = cv_id_us or role.cv_id_us
            role.role_description = role_description or role.role_description
            self.session.commit()
            self.session.flush()

    def vacancy_response(self, vacancy_id: int) -> None:
        pass

    def update_vacancy_to_close(self, vacancy_id: int) -> None:
        vacancy = self.session.get(Vacancy, vacancy_id)
        if vacancy is not None:
            vacancy.type_ = 'close'
            self.session.commit()
            self.session.flush()

    def get_best_vacancies_id(
            self,
            limit: int,
            from_date: int | datetime = None,
            from_vacancy_id: int = None,
            only_vacancy_role: str = None,
            except_vacancy_ids: list[int] = None,
    ) -> list[int]:
        """
        :param limit: return limit
        :param from_date: start_datetime
        :param from_vacancy_id: with id more than from_vacancy_id
        :param only_vacancy_role: Use role by vacancy
        :param except_vacancy_ids: list of exception vacancy
        :return: vacancy id without responses.
        """
        if isinstance(from_date, datetime):
            from_date = int(from_date.strftime('%Y%m%d%H%M%S'))

        vacancies = select(
            VacancyRating.vacancy_id
        ).join(
            Vacancy,
            VacancyRating.vacancy_id == Vacancy.id,
            isouter=True,
        ).join(
            Employers,
            Employers.id == Vacancy.employer,
            isouter=True,
        ).where(
            and_(
                VacancyRating.vacancy_id >= from_vacancy_id if from_vacancy_id else True,
                Vacancy.date_save > from_date if from_date else True,
                Vacancy.id.notin_(except_vacancy_ids or []),
                VacancyRating.profile_type == only_vacancy_role if only_vacancy_role else True,
                VacancyRating.vacancy_id.notin_(select(ResponseCV.vacancy_id)),
                or_(Employers.manual_rating.is_(None), Employers.manual_rating > 0),
            )
        ).order_by(
            case(
                [(VacancyRating.manual_rating.isnot(None), VacancyRating.manual_rating)],
                else_=VacancyRating.final_rating,
            ).desc()
        ).limit(
            limit
        )
        return self.session.scalars(vacancies).all()


