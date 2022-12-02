import pytest
from hh_api.endpoints import UseURLs
from hh_api.responser import Responser, Validator
from hh_api.response_validators import Dictionaries, ListDictionaries, Currency
from db.save_manager import SaveManager


def test_response_dictionaries(response_dictionary, db):
    dictionary = response_dictionary.json()
    currency = dictionary.pop('currency')

    assert currency is not None

    check_currency = Validator().return_objects(
        Currency, currency, return_list=True)

    assert len(currency) == len(check_currency)



