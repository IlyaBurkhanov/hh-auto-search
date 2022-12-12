import json

json_file = 'config_for_rating/search_config.json'  # ENV

with open(json_file, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

