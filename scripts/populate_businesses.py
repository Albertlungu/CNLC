import sys

sys.path.append('..')

from scripts.overpass_api import fetch_businesses, compose_json
from backend.storage.json_handler import save_businesses

cities = ['Ottawa', 'Toronto', 'Montreal', 'Gatineau', 'Vancouver', 'Calgary', 'Edmonton']

all_data = []
for city in cities:
    all_data.append(fetch_businesses(city)[2])

businesses = []
for data in all_data:
    businesses.extend(compose_json(data))


save_businesses(businesses)