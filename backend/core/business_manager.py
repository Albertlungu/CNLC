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
    Searches businesses by name using fuzzy matching to account for user typos.

    Args:
        query (str): User query (the name of the business searched for).

    Raises:
        ValueError: If the business was never found.

    Returns:
        list[dict]: Contains the info for all businesses that were matched to the query.
    """

    businesses = get_all_businesses() # Fetch all businesses

    valid_businesses = []

    for business in businesses:
        business_name = business.get('name')
        if business_name is not None: # Check if None so that .lower() can be used without error
            partial_ratio = fuzz.partial_ratio(query.lower(), business_name.lower())
                # Partial ratio: partial matches within string
            token_set_ratio = fuzz.token_set_ratio(query.lower(), business_name.lower())
                # Token set ratio: For word order changes
            if partial_ratio > 85 and token_set_ratio > 85:
                valid_businesses.append(business)
        else:
            continue

    if valid_businesses == []:
        raise ValueError("ERROR: Query did not match any businesses.")
        # Will be caught later and displayed in electron

    return valid_businesses

def filter_by_category(
        category:str
        ) -> list[dict]:
    """
    Filters through businesses by category.

    Args:
        category (str): Business category (e.g. restaurant, convenience, bakery)

    Raises:
        ValueError: If no shops with the given category were found.

    Returns:
        list[dict]: All businesses that were found within the given category.
    """
    businesses = get_all_businesses() # Fetch all businesses

    valid_businesses = []

    for business in businesses:
        if category == business['category']:
            valid_businesses.append(business)
        else:
            continue

    if valid_businesses == []:
        raise ValueError("ERROR: Category not found. Please check your input.")

    return valid_businesses
