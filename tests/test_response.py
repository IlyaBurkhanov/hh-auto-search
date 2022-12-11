import pytest
from hh_api.endpoints import Settings
from hh_api.responser import Responser, Validator
from db.save_manager import SaveManager
from employers.main import WorkEmployers
from db.models import Employers


def test_employers():
    SaveManager().truncate(Employers)
    w = WorkEmployers()
    w.update_employers(employer_type='private_recruiter',
                       area=113)
    assert len(w.set_id) > 250


def test_response_dictionaries():
    save = SaveManager()

    dictionary_settings = Settings.DICTIONARIES
    response = Responser().response(dictionary_settings.endpoint)

    assert response.request.status_code == 200

    dictionary = response.get_json()
    currency = dictionary.pop('currency')
    curr_settings = Settings.CURRENCY

    assert currency is not None

    check_currency = Validator().return_objects(
        curr_settings.validator, currency)

    assert len(currency) == len(check_currency), 'Что-то незавалидировалось'

    save.update_dict(model=curr_settings.db_model,
                     data=check_currency, full_update=True)

    check_dictionary = Validator().return_objects(
        dictionary_settings.validator, dictionary, parse_as_dict=True
    )

    assert len(check_dictionary) == len(dictionary)

    save.update_dict(model=dictionary_settings.db_model,
                     data=check_dictionary,
                     mapping=dictionary_settings.mapping,
                     full_update=True)


@pytest.mark.parametrize('response_type, parse_as_dict, del_key', [
    ('INDUSTRY', False, None), ('LANGUAGES', False, None),
    ('BUSINESS_ROLE', False, 'categories')
])
def test_response(response_type, parse_as_dict, del_key):
    save = SaveManager()
    settings = getattr(Settings, response_type)
    response = Responser().response(settings.endpoint)

    assert response.request.status_code == 200

    data = response.get_json()
    if del_key:
        data = data.pop(del_key)
    check = Validator().return_objects(
        settings.validator, data, parse_as_dict=parse_as_dict)

    assert len(check) == len(data)

    save.update_dict(model=settings.db_model,
                     data=check,
                     mapping=settings.mapping,
                     full_update=True)


def test_areas():
    save = SaveManager()
    settings = Settings.AREAS
    response = Responser().response(settings.endpoint)

    assert response.request.status_code == 200

    data = response.get_json()
    check = Validator().return_objects(
        settings.validator, data)

    assert len(check) == len(data)

    save.update_recursive(model=settings.db_model,
                          data=check,
                          recursion_value=settings.recursion_value,
                          full_update=True)
