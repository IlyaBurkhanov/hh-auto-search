import json

import requests
import unicodedata
from pydantic import ValidationError

from configs.config import settings

API = settings.API
HEADER = settings.HEADER  # ENV


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

    def return_objects(self, validator, data, return_list=True, skip_error=True, parse_as_dict=False):
        if not return_list:
            return self.valid(validator, data, skip_error)

        if parse_as_dict:
            data = [{'key': key, 'value': value} for key, value in data.items()]

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
    header = HEADER
    request = None

    def response(self, endpoint, params=None, headers=None):
        if headers:
            headers = dict(**self.header, **headers)
        self.request = requests.get(API + endpoint, params=params, headers=headers)
        return self

    def get_json(self):
        if self.request is None:
            raise ValueError('Request has not been sent')
        text = unicodedata.normalize('NFKD', self.request.text or '')
        return json.loads(text)
