"""
./backend/core/business_manager.py

Brain of business logic, including fetching businesses from JSON file, searching with fuzzy
matching, and geolocation.
"""

import sys
import os

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.storage.json_handler import load_businesses
import backend.utils.search as search
from backend.utils.geo import Haversine

def get_all_businesses(filepath:str='./data/businesses.json') -> list[dict]:
    """
    Gets all businesses without any other processing.

    Args:
        filepath (str, optional): Filepath to businesses JSON file.
                                  Defaults to './data/businesses.json'.

    Returns:
        list[dict]: Information about the business.
    """
    return load_businesses(filepath)

def search_by_id(business_id:int) -> list:
    """
    Fetches a business given its ID and returns it.

    Args:
        business_id (int): Numerical identification of business.

    Raises:
        ValueError: Is raised if the business is not found.

    Returns:
        list: Contains the dict containing business information (normally only one result).
    """
    businesses = get_all_businesses()

    results = []
    for business in businesses:
        if business.get('id') == business_id:
            results.append(business)
        else:
            continue

    if not results:
        raise ValueError(f"ERROR: Cannot find business id: {business_id}")
    # Will be caught later and displayed in electron

    return results

def search_by_name(query:str) -> list[dict]:
    """
    Uses text searching function in ./backend/utils/search.py to search by name.

    Args:
        query (str): What the user is searching for.

    Returns:
        list[dict]: Contains all valid businesses.
    """
    return search.search_by_text(query=query)

def filter_by_category(target_category:str) -> list[dict]:
    """
    Filters through businesses by category using functions from ./backend/utils/search.py.

    Args:
        target_category (str): Category that is being searched for by the user, such as restaurant.
    """
    return search.filter_by_field('category', target_category)

def filter_by_radius(
        radius:int,
        lat1:float,
        lon1:float
        ) -> list[dict]:
    """
    Filters by location through shops with a custom radius, given the user's location.

    Args:
        radius (int): Radius within which the user is searching.
        lat1 (float): User's latitude.
        lon1 (float): User's longitude.

    Raises:
        ValueError: If there were no businesses found in the given radius.

    Returns:
        list[dict]: Contains all businesses found in the given radius.
    """

    businesses = get_all_businesses()
    results = []

    for business in businesses:
        lat2 = business['latitude']
        lon2 = business['longitude']
        if Haversine(lat1,lon1,lat2,lon2).final_distance() < radius:
            results.append(business)
        else:
            continue

    if not results:
        raise ValueError("ERROR: Could not find any businesses in the selected radius.")

    return results
