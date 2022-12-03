from db.core import Base, engine
from sqlalchemy.orm import Session
from hh_api.endpoints import MappingDict
from typing import Optional


class SaveManager:

    @staticmethod
    def truncate(*truncate_models):
        tables = []
        for model in truncate_models:
            tables.append(model.__table__)
            if model.relate:
                tables.append(model.relate.model.__table__)
        Base.metadata.drop_all(engine, tables=tables)
        Base.metadata.create_all(engine, tables=tables)

    def update_dict(self, model: Base.__class__,
                    data: dict,
                    mapping: MappingDict = None,
                    full_update: bool = False) -> None:
        if full_update:
            self.truncate(model)

        with Session(bind=engine) as session:
            if mapping is None:
                session.bulk_insert_mappings(model, [dict(x) for x in data])
            else:
                if model.relate is None:
                    raise ValueError('Mapping without related is '
                                     f'impossible [{model.__tablename__}]')
                self.save_with_mapping(session, model, data, mapping)
            session.commit()

    def update_recursive(self, model: Base.__class__,
                         data: dict,
                         recursion_value: str,
                         full_update: bool = False,
                         session=None):
        def save(data_, session_):
            for obj in data_:
                dict_obj = dict(obj)
                recursion = dict_obj.pop(recursion_value, [])
                session.bulk_insert_mappings(model, [dict_obj])
                if recursion:
                    save(recursion, session_)

        if full_update:
            self.truncate(model)
        with Session(bind=engine) as session:
            save(data, session)
            session.commit()



    @staticmethod
    def save_with_mapping(session, model, data, mapping):
        related_model = model.relate.model
        fk = model.relate.fk
        for obj_ in data:
            dict_obj = dict(obj_)
            obj = related_model(
                **{value: dict_obj.pop(key)
                   for key, value in mapping.mapping.items()}
            )
            session.add(obj)
            session.flush()
            save_list = []
            for val in dict_obj[mapping.value_key]:
                dict_save = dict(val)
                dict_save[fk] = obj.id
                save_list.append(dict_save)
            if save_list:
                session.bulk_insert_mappings(model, save_list)
