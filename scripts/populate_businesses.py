import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scripts.overpass_api import fetch_businesses, compose_json
from backend.storage.json_handler import save_businesses


city = 'Ottawa'
data = fetch_businesses(city)[2]
businesses = compose_json(data)
save_businesses(businesses)

print("="*60)
print(f'{city} businesses successfully saved')
print("="*60)