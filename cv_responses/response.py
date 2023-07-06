from datetime import datetime

from httpx import Client
from langdetect import detect
from sqlalchemy import select, or_, and_, case
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from authorization.authorize import get_token_header, get_access_token, refresh_token
from configs.config import engine, settings
from db.models import Employers, ResponseCV, Vacancy, VacancyRating, VacancyRoles
from vacancies.main import VacancyWorker
from vacancies.models import ResponseVacancy


def open_messages(path_to: str) -> str:
    with open(path_to, 'r') as file:
        return file.read().rstrip()


class CVResponser:
    message_ru = open_messages(settings.MESSAGE_RU_FILE)
    message_us = open_messages(settings.MESSAGE_US_FILE)
    _use_refresh_token = 0
    request_cv_errors = {
        201: None,
        303: 'Vacancy has direct type. Use vacancy url!',
    }

    def __init__(self):
        self._token = get_access_token()
        self.session = Session(bind=engine)
        self.headers = get_token_header(self._token)
        self.roles: dict[str, VacancyRoles] = self._get_vacancy_roles()

    def __del__(self):
        try:
            self.session.close()
        except ProgrammingError:
            pass

    def _refresh_token(self) -> None:
        self._token = refresh_token(self._token)
        self.headers = get_token_header(self._token)

    @property
    def _response_header(self) -> dict:
        return dict(**self.headers, **settings.HEADER_VACANCY_REQUEST)

    def _get_vacancy_roles(self) -> dict[str, VacancyRoles]:
        roles = self.session.query(VacancyRoles).all()
        return {role.role_name: role for role in roles}

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
        vacancy: ResponseVacancy = VacancyWorker.request_vacancy(vacancy_id)
        if vacancy.type_ == 'closed':
            return self.update_vacancy_to_close(vacancy_id)

        if (vacancy_db := self.session.get(Vacancy, vacancy_id)) is None:
            print(f'Vacancy with id: [{vacancy_id}] not found in db')  # FIXME: after test
            return
        employer = self.session.get(Employers, vacancy_db.employer)
        vacancy_rating = self.session.query(VacancyRating).filter(VacancyRating.vacancy_id == vacancy_id).one()
        language = detect(vacancy_db.description)
        use_role = self.roles.get(vacancy_rating.profile_type, 'default')
        message = (self.message_ru if language == 'ru' else self.message_us).format(company_name=employer.name or '')
        cv_id = use_role.cv_id_rus if language == 'ru' else use_role.cv_id_us
        result = None  # self._send_response_to_vacancy(message, cv_id, vacancy_id)
        response_cv = ResponseCV(
            vacancy_id=vacancy_id,
            employer_id=vacancy_db.employer,
            role_name=vacancy_rating.profile_type,
            vacancy_rating=vacancy_rating.manual_rating or vacancy_rating.final_rating,
            has_test=vacancy_db.has_test,
            is_success=True if result is None else False,
            error_name=result,
        )
        self.session.add(response_cv)
        self.session.commit()
        self.session.flush()

    def _send_response_to_vacancy(self, message: str, cv_id: str, vacancy_id: int) -> None | str:
        data = {'vacancy_id': vacancy_id, 'resume_id': cv_id, 'message': message}
        result = Client().post(settings.URL_FOR_REQUEST, headers=self._response_header, data=data)
        if result.status_code in self.request_cv_errors:
            return self.request_cv_errors[result.status_code]

        response = result.json()
        if result.status_code == 400 and response.get('error') == 'invalid_grant':
            if self._use_refresh_token:
                raise Exception('Available only one refresh token!')
            self._refresh_token()
            self._use_refresh_token += 1
            self._send_response_to_vacancy(message, cv_id, vacancy_id)
        return response['error_description']

    def update_vacancy_to_close(self, vacancy_id: int) -> None:
        vacancy = self.session.get(Vacancy, vacancy_id)
        if vacancy is not None:
            vacancy.type_ = 'closed'
            self.session.commit()
            self.session.flush()

    def get_best_vacancies_id(
            self,
            limit: int,
            from_date: int | datetime = None,
            from_vacancy_id: int = None,
            only_vacancy_role: str = None,
            except_vacancy_ids: list[int] = None,
            except_employer_ids: list[int] = None,
            without_test: bool = False,
    ) -> list[int]:
        """
        :param without_test: only without test
        :param limit: return limit
        :param from_date: start_datetime
        :param from_vacancy_id: with id more than from_vacancy_id
        :param only_vacancy_role: Use role by vacancy
        :param except_vacancy_ids: list of exception vacancy
        :param except_employer_ids: list of exception employer
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
                Vacancy.type_ != 'closed',
                Vacancy.test.isnot(None) if without_test else True,
                Vacancy.date_save > from_date if from_date else True,
                Vacancy.id.notin_(except_vacancy_ids or []),
                Employers.id.notin_(except_employer_ids or []),
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
