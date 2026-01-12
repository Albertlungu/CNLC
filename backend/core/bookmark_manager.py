"""
./backend/core/bookmark_manager.py

Functions to manipulate the bookmarks for the users.
"""

import os
import sys
from pathlib import Path
from typing import Optional

from typing_extensions import Any

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.storage.json_handler as jh


def create_bookmarks(
    username: str,
    bookmarks: Any,
    output_filepath: str = "../data/users.json",
) -> None:
    """
    Adds bookmarks to a user's data.

    Args:
        username (str): The user's unique username.
        bookmarks (list): The bookmarks they want to add.
        output_filepath (str, optional): _description_. Defaults to "../data/users.json".
    """
    if output_filepath == "../data/users.json":
        project_root = Path(__file__).parent.parent.parent
        output_filepath = str(project_root / "data" / "users.json")

    if isinstance(bookmarks, int):
        bookmarks = [bookmarks]

    users = jh.load_users()  # Loading all users in memory
    for user in users:
        if user["username"] == username:
            user["bookmarks"].extend(bookmarks)
            break
    else:
        raise ValueError("ERROR: Username does not exist.")

    jh.save_users(users, output_filepath, io_type="w")


def remove_bookmarks(
    username: str,
    bookmarks: Any,
    output_filepath: str = "../data/users.json",
) -> None:
    """
    Removes bookmarks from a user's data.

    Args:
        username (str): The user's unique username.
        bookmarks (list): The bookmarks they want to add.
        output_filepath (str, optional): _description_. Defaults to "../data/users.json".
    """
    if output_filepath == "../data/users.json":
        project_root = Path(__file__).parent.parent.parent
        output_filepath = str(project_root / "data" / "users.json")

    if isinstance(bookmarks, int):
        bookmarks = [bookmarks]

    users = jh.load_users()  # Loading all users in memory
    user_found = False
    for user in users:
        if user["username"] == username:
            user_found = True
            for bookmark in bookmarks:
                if bookmark not in user["bookmarks"]:
                    raise ValueError(f"ERROR: Bookmark {bookmark} does not exist.")
                user["bookmarks"].remove(bookmark)
            break

    if not user_found:
        raise ValueError("ERROR: Username does not exist.")

    jh.save_users(users, output_filepath, io_type="w")


def get_user_bookmarks(username: str, users: Optional[list[dict]] = None) -> list:
    """
    Returns a list of bookmarks for a given user.

    Args:
        username (str): The user's unique username.
        users (list[dict], optional): A list of user dictionaries. Defaults to jh.load_users().

    Returns:
        list: A list of bookmarks for the user.
    """
    if not users:
        users = jh.load_users()

    loaded_user = None
    for user in users:
        if user["username"] == username:
            loaded_user = user
            break

    if loaded_user is None:
        raise ValueError("ERROR: Username does not exist.")

    del users  # Deleting everything but keeping the selected user
    return loaded_user["bookmarks"]


def get_bookmarked_businesses(
    username: str,
    users: Optional[list[dict]] = None,
    businesses: Optional[list[dict]] = None,
) -> list:
    """
    Returns a list of businesses that have been bookmarked by a user.

    Args:
            username (str): The user's unique username.
            users (list[dict], optional): A list of user dictionaries. Defaults to jh.load_users().
            businesses (list[dict], optional): A list of business dictionaries. Defaults to jh.load_businesses().

    Returns:
            list: A list of businesses that have been bookmarked by the user.
    """
    if not users:
        users = jh.load_users()
    if not businesses:
        businesses = jh.load_businesses()

    loaded_user = None
    for user in users:
        if user["username"] == username:
            loaded_user = user
            break

    if loaded_user is None:
        raise ValueError("ERROR: Username does not exist.")

    business_map = {business["id"]: business for business in businesses}
    loaded_businesses = [
        business_map[bookmark]
        for bookmark in loaded_user["bookmarks"]
        if bookmark in business_map
    ]

    return loaded_businesses
