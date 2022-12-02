import requests
from pydantic import ValidationError

from .endpoints import API, UseURLs


class Validator:

    @staticmethod
    def valid(validator, value, skip_error=True):
        try:
            result = validator.parse_obj(value)
            return result
        except ValidationError as e:
            # logging написать попозже
            if not skip_error:
                raise e
            return

    def return_objects(self, validator,data, return_list=False,
                       skip_error=True, parse_as_dict=False):
        if not return_list:
            return self.valid(validator, data, skip_error)

        if parse_as_dict:
            data = [{'key': key, 'value': value}
                    for key, value in data.items()]

        result = []
        for val in data:
            res = self.valid(validator, val, skip_error)
            if res:
                result.append(res)
        return result


class Responser:
    client_code = None
    bearer = None
    app_code = None
    #  Тут указать значение из ENV
    header = {'User-Agent': 'Ilya_APP/0.1 (iaburhanov@mail.ru)'}

    def get_response(self, endpoint, params=None, headers=None):
        if headers:
            headers = dict(**self.header, **headers)
        return requests.get(API + endpoint, params=params, headers=headers)

    def get_json_from_response(self, *args, **kwargs):
        return self.get_response(*args, **kwargs).json()

    def request_for_data(self, endpoint, params=None, headers=None,
                         result='dict'):
        if result == 'dict':
            return self.get_json_from_response(endpoint, params, headers)

