import importlib

import db.models as models
from db.core import Base, engine
from sqlalchemy.orm import Session
from typing import Optional


class SaveManager:
    models = {
        getattr(models, model).__tablename__.lower(): getattr(models, model)
        for model in models.__all__
    }

    @staticmethod
    def truncate(*truncate_models):
        tables = [model.__table__ for model in truncate_models]
        Base.metadata.drop_all(engine, tables=tables)
        Base.metadata.create_all(engine, tables=tables)

    def get_model(self, table_name: str) -> Optional[Base]:
        table_name = table_name.lower()
        return (self.models.get(table_name)
                or self.models.get(table_name + 'db')
                or self.models.get(table_name + '_db'))

    def update_dict(self, table_name: str,
                    data: dict,
                    mapping: dict = None,
                    full_update: bool = False) -> None:
        model = self.get_model(table_name)
        if model is None:
            raise KeyError('NOT FOUND MODEL')

        if full_update:
            self.truncate(model)

        if mapping:
            # self.foo(data, mapping) и изменяем поля, пока заглушка
            pass
        with Session(bind=engine) as s:
            s.bulk_insert_mappings(model, [{'key_attr': 'vacancy_label',
                                            'id': 'with_address',
                                            'name': 'Только с адресом'}])
            s.commit()
