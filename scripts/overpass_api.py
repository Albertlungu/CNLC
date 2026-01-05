import requests
from typing import Any

def fetch_businesses(
        city:str,
        debug=False
        ) -> tuple[str, requests.Response, dict]:
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

def compose_json(
        data:dict
        ) -> list[dict]:
    """
    Uses the data from the fetch_businesses() function to display relevant information about the
    business.

    Args:
        data (dict): Data from fetch_businesses function.

    Returns:
        list[dict]: All business information as a list of dictionaries. To be compounded into a json
                    file.
    """

    businesses = []

    for element in data['elements']:
        tags = element.get('tags', {})

        if 'name' not in tags:
            continue

        business = {
            'id': element.get('id'),
            'name': tags.get('name'),
            'latitude': element.get('lat'),
            'longitude': element.get('lon'),
            'address': {
                'street': tags.get('addr:street'),
                'housenumber': tags.get('addr:housenumber'),
                'city': tags.get('addr:city'),
                'country': tags.get('addr:country'),
                'postcode': tags.get('addr:postcode')
            },
            'phone': tags.get('phone') or tags.get('contact:phone'),
            'website': tags.get('website') or tags.get('contact:website'),
            'opening_hours': tags.get('opening_hours'),
            'category': tags.get('shop') or tags.get('amenity') or tags.get('craft'),
            'cuisine': tags.get('cuisine')
        }

        businesses.append(business)

    return businesses
