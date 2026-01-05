"""
./scripts/populate_businesses.py

Pulls together entire business population pipeline.

IDEA: Use geolocation to find user's latitude and longitude, they can select a radius in which
businesses are shown. The radius (in km) is translated to deg, and we estimate that way.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from scripts.overpass_api import fetch_businesses, compose_json
from backend.storage.json_handler import save_businesses


city = 'Winnipeg'
data = fetch_businesses(city)[2]
businesses = compose_json(data, city=city)
save_businesses(businesses, io_type='a')

print("="*60)
print(f'{city} businesses successfully saved')
print("="*60)