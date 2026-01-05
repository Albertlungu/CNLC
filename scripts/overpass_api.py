import requests
from typing import Any

def fetch_businesses(
        city:str,
        debug=False
        ) -> tuple[str, requests.Response, Any]:
    """
    Gets businesses using requests library and OverpassAPI.

    Args:
        city (str): City in which to search
        debug (bool, optional): Whether to print debug messages. Defaults to False.

    Returns:
        tuple[str, requests.Response, Any]: Contains the query, response from Overpass, and the data
    """

    query = f"""
    [out:json];
    area[name="{city}"]->.searchArea;
    (
    node["shop"](area.searchArea);
    node["amenity"="restaurant"](area.searchArea);
    node["amenity"="cafe"](area.searchArea);
    );
    out body;
    """

    url = "https://overpass-api.de/api/interpreter"
    response = requests.post(url, data=query)

    data = response.json()

    if debug:
        print(f"DEBUG: Status Code: {response.status_code}")
        print(f"DEBUG: Response Text\n{"="*60}\n: {response.text[:500]}")
        # First 500 chars

    return query, response, data
