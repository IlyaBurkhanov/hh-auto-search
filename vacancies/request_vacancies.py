from enum import Enum
from pydantic import BaseModel, validator, Field
from datetime import date, datetime
from typing import List, Union

from configs.conf import DROP_PARAMS
# from sqlalchemy.orm import Session

# from db.core import engine
# from db.models import Currency
#
# with Session(engine) as session:
#     CURRENCIES = {code: rate for code, rate in
#                   session.query(Currency.code, Currency.rate).all()}
#
# Currency = Enum('Currency', CURRENCIES)


