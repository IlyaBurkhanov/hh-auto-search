from db.core import Base, engine
from db.save_manager import SaveManager



if __name__ =='__main__':
    SaveManager().update_dict('dictionaries', 1, full_update=True)