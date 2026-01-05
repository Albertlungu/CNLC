import json
from pathlib import Path

def save_businesses(
        businesses:list[dict],
        output_filepath:str='../data/businesses.json'
        ) -> None:
    """
    Saves businesses taken from OverpassAPI to a JSON file.

    Args:
        businesses (list[dict]): List containing businesses info.
        output_filepath (str, optional): Output filepath. Defaults to '../data/businesses.json'.
    """
    with open(output_filepath, 'w') as f:
        json.dump(businesses, f, indent=2)

def load_businesses(
        input_filepath:str='../data/businesses.json',
        ) -> list[dict]:
    """
    Reads a JSON file and returns information about a businesses as a list.

    Args:
        input_filepath (str, optional): Input filepath. Defaults to '../data/businesses.json'.

    Returns:
        list[dict]: Information about the business.
    """
    with open(input_filepath, 'r') as f:
        return json.load(f)