"""
./backend/storage/json_handler.py

Handles saving and loading JSON files from their pipelines.
"""

import json
from pathlib import Path

from typing import Union

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

def save_businesses(
        businesses:list[dict],
        output_filepath:str="../data/businesses.json",
        io_type:str='a'
        ) -> None:
    """
    Saves businesses taken from OverpassAPI to a JSON file.

    Args:
        businesses (list[dict]): List containing businesses info.
        output_filepath (str, optional): Output filepath. Defaults to 'data/businesses.json'.
        io_type (str, optional): Whether to rewrite, delete, or append to file. Defaults to 'a'.
    """
    if output_filepath is None:
        # Get the project root (2 levels up from this file)
        project_root = Path(__file__).parent.parent.parent
        output_filepath = str(project_root / 'data' / 'businesses.json')

    with open(output_filepath, io_type) as f:
        json.dump(businesses, f, indent=1)

def load_users(
        input_filepath:str="../data/users.json"
        ) -> list[dict]:
    """
    Loads a JSON file that contains all users.

    Args:
        input_filepath (str, optional): Filepath to user JSON file. Defaults to "data/users.json".

    Returns:
        list[dict]: List containing the dictionaries with all users and their data.
    """
    with open(input_filepath, 'r') as f:
        return json.load(f)

def save_users(
        users:list[dict],
        output_filepath:str="../data/users.json",
        io_type:str="a"
        ) -> None:
    """
    Saves users to a JSON file.

    Args:
        users (list[dict]): List containing user dictionaries to append.
        output_filepath (str, optional): Filepath to output JSON file. Defaults to "../data/users.json".
        io_type (str, optional): Whether to rewrite, delete, or append to file. Defaults to "a".
    """
    if output_filepath != "":
        project_root = Path(__file__).parent.parent.parent
        output_filepath = str(project_root / 'data' / 'businesses.json')

    with open(output_filepath, io_type) as f:
        json.dump(users, f, indent=1)

def save_bookmarks(
        username:str,
        bookmarks:int | list[int],
        output_filepath:str="../data/users.json",
        ) -> None:
    """
    Adds bookmarks to a user's data.

    Args:
        username (str): The user's unique username.
        bookmarks (list): The bookmarks they want to add.
        output_filepath (str, optional): _description_. Defaults to "../data/users.json".
    """
    if output_filepath != "":
        project_root = Path(__file__).parent.parent.parent
        output_filepath = str(project_root / 'data' / 'businesses.json')

    if isinstance(bookmarks, int):
        bookmarks = [bookmarks]


    users = load_users() # Loading all users in memory
    loaded_user = None
    for user in users:
        if user['username'] == username:
            loaded_user = user
            break

    if loaded_user is None:
        raise ValueError(f"ERROR: Username does not exist.")

    del users # Deleting everything but keeping the selected user
    loaded_user['bookmarks'].extend(bookmarks)
