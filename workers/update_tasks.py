from configs.workers import SAVE_MANAGER, VALIDATOR, RESPONSER
from hh_api.endpoints import Settings


def update_other(response_type, parse_as_dict=False, del_key=None):
    settings = getattr(Settings, response_type)
    response = RESPONSER.response(settings.endpoint)
    data = response.get_json()
    if del_key:
        data = data.pop(del_key)
    check = VALIDATOR.return_objects(settings.validator, data, parse_as_dict=parse_as_dict)
    SAVE_MANAGER.update_dict(
        model=settings.db_model,
        data=check,
        mapping=settings.mapping,
        full_update=True
    )


def update_dictionaries():
    dictionary_settings = Settings.DICTIONARIES
    dictionary = RESPONSER.response(dictionary_settings.endpoint).get_json()
    currency = dictionary.pop('currency')
    curr_settings = Settings.CURRENCY
    check_currency = VALIDATOR.return_objects(curr_settings.validator, currency)
    SAVE_MANAGER.update_dict(model=curr_settings.db_model, data=check_currency, full_update=True)
    check_dictionary = VALIDATOR.return_objects(dictionary_settings.validator, dictionary, parse_as_dict=True)
    SAVE_MANAGER.update_dict(
        model=dictionary_settings.db_model,
        data=check_dictionary,
        mapping=dictionary_settings.mapping,
        full_update=True
    )


def update_areas():
    settings = Settings.AREAS
    response = RESPONSER.response(settings.endpoint)
    data = response.get_json()
    check = VALIDATOR.return_objects(settings.validator, data)
    SAVE_MANAGER.update_recursive(
        model=settings.db_model,
        data=check,
        recursion_value=settings.recursion_value,
        full_update=True
    )
