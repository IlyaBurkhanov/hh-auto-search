import pickle
import time
from urllib.parse import parse_qs, urlparse, urlencode

from httpx import Client
from selenium import webdriver

from configs.config import settings


def _manual_user_auth_code() -> str:
    params = {
        "response_type": "code",
        "client_id": settings.CLIENT_ID.get_secret_value(),
    }
    use_url = settings.URL_MANUAL_AUTH + '?' + urlencode(params)
    browser = webdriver.Firefox()
    browser.get(use_url)
    while True:
        redirect_url = browser.current_url
        if urlparse(redirect_url).netloc != settings.REDIRECT_URI:
            time.sleep(.2)
            continue
        browser.close()
        break
    # github.com/hhru/api/blob/master/docs/authorization_for_user.md
    return parse_qs(urlparse(redirect_url).query)['code'][0]


def _recreate_access() -> dict:
    code = _manual_user_auth_code()
    header = dict(**settings.HEADER, **settings.HEADER_GET_TOKEN)
    data = {
        'grant_type': settings.GRANT_TYPE_AUTH,
        'client_id': settings.CLIENT_ID.get_secret_value(),
        'client_secret': settings.CLIENT_SECRET.get_secret_value(),
        'code': code,
    }
    return Client().post(settings.URL_GET_TOKEN, data=data, headers=header).json()


def _save_access_data(access_token: dict) -> None:
    with open(settings.ACCESS_DATA_FILE, 'wb') as file:
        pickle.dump(access_token, file)


def _read_access_data() -> dict:
    with open(settings.ACCESS_DATA_FILE, 'rb') as file:
        return pickle.load(file)


def get_token_header(token: dict) -> dict:
    token = {'Authorization': f'{settings.TOKEN_TYPE} {token["access_token"]}'}
    return dict(**settings.HEADER, **token)


def get_access_token(refresh=False) -> dict:
    try:
        token = _read_access_data()
    except FileNotFoundError:
        token = _recreate_access()
        _save_access_data(token)
        return token

    if not refresh:
        if _check_valid_token(token):
            return token
    return refresh_token(token)


def refresh_token(token: dict) -> dict:
    data = {
        'grant_type': settings.GRANT_TYPE_REFRESH,
        'refresh_token': token['refresh_token'],
    }
    header = dict(**settings.HEADER, **settings.HEADER_GET_TOKEN)
    request = Client().post(settings.URL_GET_TOKEN, data=data, headers=header)
    new_token = request.json()
    if request.status_code == 400 and new_token['error_description'].lower() == 'token not expired':
        print('Токен еще жив!')  # FIXME: after test -> logger
        return token
    if request.status_code == 200:
        _save_access_data(new_token)
        return new_token
    raise Exception('Some problem with refresh token!')


def _check_valid_token(token: dict) -> bool:
    headers = get_token_header(token)
    check = Client().get(settings.URL_ALL_RESUMES, headers=headers)
    return True if check.status_code == 200 else False
