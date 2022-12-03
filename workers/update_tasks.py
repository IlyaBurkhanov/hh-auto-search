from hh_api.responser import Responser, Validator
from hh_api.endpoints import Settings
from db.save_manager import SaveManager

save = SaveManager()
validator = Validator()


def update_dictionaries():
    dictionary_settings = Settings.DICTIONARIES
    dictionary = Responser().response(dictionary_settings.endpoint).get_json()
    currency = dictionary.pop('currency')
    curr_settings = Settings.CURRENCY
    check_currency = validator.return_objects(curr_settings.validator,
                                              currency)
    save.update_dict(model=curr_settings.db_model,
                     data=check_currency, full_update=True)
    check_dictionary = validator.return_objects(
        dictionary_settings.validator, dictionary, parse_as_dict=True
    )
    save.update_dict(model=dictionary_settings.db_model,
                     data=check_dictionary,
                     mapping=dictionary_settings.mapping,
                     full_update=True)
