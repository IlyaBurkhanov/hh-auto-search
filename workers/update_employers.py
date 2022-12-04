from sqlalchemy.orm import Session
from tqdm import tqdm
import os

os.chdir('../')
from hh_api.responser import Responser, Validator
from hh_api.endpoints import Settings
from db.save_manager import SaveManager
from db.core import engine


class SaveEmployers:
    save = SaveManager()
    validator = Validator()
    responser = Responser()
    settings = Settings.EMPLOYERS
    model = settings.db_model
    set_id = set()
    params = {'page': 0}
    max_page = None

    def __init__(self):
        self.session = Session(engine)
        self.set_id = set(
            [x.id for x in self.session.query(self.model.id).all()]
        )

    def __del__(self):
        self.session.close()

    # def start_service(self, use_max_page=0, page_per_list=100,
    #                   with_vacancies=True):
    #     self.params['per_page'] = page_per_list
    #     self.params['only_with_vacancies'] = with_vacancies
    #     result = self.response_employers()
    #     max_page = use_max_page or int(result['pages'])
    #     self.save_result((result.pop('items')))
    #     for _ in tqdm(range(max_page))
    #
    # def response_employers(self):
    #     response = self.responser.response(self.settings.endpoint,
    #                                        params=self.params)
    #     if response.request.status_code != 200:
    #         raise ValueError('Ошибка запроса!!!!')
    #     self.params['page'] += 1
    #     return response.get_json()
    #
    # def check_open_vacancy(self, employer):
    #     if employer.id in self.set_id:
    #         employ = self.session.query(self.model).filter(
    #             self.model.id == employer.id).first()
    #         employ.open_vacancies = employer.open_vacancies
    #         self.session.commit()
    #         return True
    #     return False
    #
    #
    # def save_result(self, items):
    #     check_employer = self.validator.return_objects(
    #         self.settings.validator,items)
    #     save_result = []
    #     for employer in check_employer:
    #         if self.check_open_vacancy(employer):
    #             continue
    #         self.set_id.add(employer.id)
    #         save_result.append(employer)
    #
    #     if save_result:
    #         self.session.bulk_insert_mappings(
    #             self.model, [dict(x) for x in save_result])
    #         self.session.commit()
