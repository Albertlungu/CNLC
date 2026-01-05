"""
./backend/storage/json_handler.py

Handles saving and loading JSON files from their pipelines.
"""

import json
from pathlib import Path

def save_businesses(
        businesses:list[dict],
        output_filepath:str|None=None,
        io_type:str='a'
        ) -> None:
    """
    Saves businesses taken from OverpassAPI to a JSON file.

    Args:
        businesses (list[dict]): List containing businesses info.
        output_filepath (str, optional): Output filepath. Defaults to 'data/businesses.json'.
        io_type (str, optional): Whether to rewrite, delete, or append to file.
    """
    if output_filepath is None:
        # Get the project root (2 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        output_filepath = str(project_root / 'data' / 'businesses.json')

    with open(output_filepath, io_type) as f:
        json.dump(businesses, f, indent=1)

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
