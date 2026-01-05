"""
./backend/utils/search.py

Helper functions for backend; DRY principle and modularity.
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

def search_by_text(
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

    results = []

    for business in businesses:
        business_name = business.get('name')
        if business_name is not None: # Check if None so that .lower() can be used without error
            partial_ratio = fuzz.partial_ratio(query.lower(), business_name.lower())
                # Partial ratio: partial matches within string
            token_set_ratio = fuzz.token_set_ratio(query.lower(), business_name.lower())
                # Token set ratio: For word order changes
            if partial_ratio > 85 and token_set_ratio > 85:
                results.append(business)
        else:
            continue

    if not results:
        raise ValueError("ERROR: Query did not match any businesses.")
        # Will be caught later and displayed in electron

    return results

def filter_by_field(
        field:str,
        value:str
        ) -> list[dict]:
    """
    Generic filtering by field for more reusability in other code.

    Args:
        field (str): Field searched for, such as category, or cuisine
        value (str): Value matched to field, for example, the category could be restaurant

    Raises:
        ValueError: If the field and/or value do not exist.

    Returns:
        list[dict]: Contains all valid businesses in field f with value v.
    """

    businesses = get_all_businesses()
    results = []

    for business in businesses:
        if business[field] == value:
            results.append(business)
        else:
            continue

    if not results:
        raise ValueError("ERROR: Field and/or value does not exist.")

    return results