"""
./backend/core/bookmark_manager.py

Functions to manipulate the bookmarks for the users.
"""

import sys
import os
from pathlib import Path

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.storage.json_handler as jh

def create_bookmarks(
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


    users = jh.load_users() # Loading all users in memory
    loaded_user = None
    for user in users:
        if user['username'] == username:
            loaded_user = user
            break

    if loaded_user is None:
        raise ValueError(f"ERROR: Username does not exist.")

    del users # Deleting everything but keeping the selected user
    loaded_user['bookmarks'].extend(bookmarks)

def remove_bookmarks(
        username:str,
        bookmarks:int | list[int],
        output_filepath:str="../data/users.json",
        ) -> None:
    """
    Removes bookmarks from a user's data.

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


    users = jh.load_users() # Loading all users in memory
    loaded_user = None
    for user in users:
        if user['username'] == username:
            loaded_user = user
            break

    if loaded_user is None:
        raise ValueError(f"ERROR: Username does not exist.")

    del users # Deleting everything but keeping the selected user

    for bookmark in bookmarks:
        if bookmark not in loaded_user['bookmarks']:
            raise ValueError(f"ERROR: Bookmark {bookmark} does not exist.")
        loaded_user['bookmarks'].remove(bookmark)
