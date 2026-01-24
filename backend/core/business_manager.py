"""
./backend/core/business_manager.py

Brain of business logic, including fetching businesses from JSON file, searching with fuzzy
matching, and geolocation.
"""

from fuzzywuzzy import fuzz, process

import backend.utils.search as search
from backend.storage.json_handler import load_businesses
from backend.utils.geo import Haversine


def search_by_id(businesses: list[dict], business_id: int) -> list:
    """
    Fetches a business given its ID and returns it.

    Args:
        businesses (list[dict]): Businesses being searched through.
        business_id (int): Numerical identification of business.

    Raises:
        ValueError: Is raised if the business is not found.

    Returns:
        list: Contains the dict containing business information (normally only one result).
    """
    results = []
    for business in businesses:
        if business.get("id") == business_id:
            results.append(business)
        else:
            continue

    if not results:
        raise ValueError(f"ERROR: Cannot find business id: {business_id}")
    # Will be caught later and displayed in electron

    return results


def search_by_name(businesses: list[dict], query: str) -> list[dict]:
    """
    Uses text searching function in ./backend/utils/search.py to search by name.

    Args:
        businesses (dict): Businesses being searched through.
        query (str): What the user is searching for.

    Returns:
        list[dict]: Contains all valid businesses.
    """
    return search.search_by_text(businesses, query=query)


def filter_by_category(businesses: list[dict], target_category: str) -> list[dict]:
    """
    Filters through businesses by category using functions from ./backend/utils/search.py.

    Args:
        businesses (dict): Businesses being searched through.
        target_category (str): Category that is being searched for by the user, such as restaurant.
    """
    return search.filter_by_field(businesses, "category", target_category)


def filter_by_min_rating(businesses: list[dict], min_rating: int) -> list[dict]:
    """
    Filters businesses to only include those with a rating >= min_rating.

    Args:
        businesses (list[dict]): Businesses being filtered.
        min_rating (int): Minimum rating threshold (1-5).

    Returns:
        list[dict]: Businesses with rating >= min_rating.
    """
    return [b for b in businesses if b.get("rating") and b.get("rating") >= min_rating]


def filter_by_radius(
    businesses: list[dict], radius: int, lat1: float, lon1: float
) -> list[dict]:
    """
    Filters by location through shops with a custom radius, given the user's location.

    Args:
        businesses (list[dict]): Businesses being searched through.
        radius (int): Radius within which the user is searching.
        lat1 (float): User's latitude.
        lon1 (float): User's longitude.

    Raises:
        ValueError: If there were no businesses found in the given radius.

    Returns:
        list[dict]: Contains all businesses found in the given radius.
    """
    results = []

    for business in businesses:
        lat2 = business["latitude"]
        lon2 = business["longitude"]
        if Haversine(lat1, lon1, lat2, lon2).final_distance() < radius:
            results.append(business)
        else:
            continue

    if not results:
        raise ValueError("ERROR: Could not find any businesses in the selected radius.")

    return results
