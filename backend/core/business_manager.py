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

def get_all_businesses(
        filepath:str='./data/businesses.json'
        ) -> list[dict]:
    """
    Gets all businesses without any other processing.

    Args:
        filepath (str, optional): Filepath to businesses JSON file.
                                  Defaults to './data/businesses.json'.

    Returns:
        list[dict]: Information about the business.
    """
    return load_businesses(filepath)

def search_by_id(
        business_id:int
        ) -> list:
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

    if results == []:
        raise ValueError(f"ERROR: Cannot find business id: {business_id}")
    # Will be caught later and displayed in electron

    return results

def search_by_name(
        query:str
        ) -> list[dict]:
    """
    Uses text searching function in ./backend/utils/search.py to search by name.

    Args:
        query (str): What the user is searching for.

    Returns:
        list[dict]: Contains all valid businesses.
    """
    return search.search_by_text(query=query)

def filter_by_category(
        target_category:str
        ) -> list[dict]:
    """
    Filters through businesses by category using functions from ./backend/utils/search.py.

    Args:
        target_category (str): Category that is being searched for by the user, such as restaurant.
    """
    return search.filter_by_field('category', target_category)
