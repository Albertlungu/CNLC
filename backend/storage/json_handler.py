"""
./backend/storage/json_handler.py

Handles saving and loading JSON files from their pipelines.
"""

import json
from pathlib import Path
from tarfile import TarError
from typing import Optional, Union

from config.config import BUSINESSES_JSON, REVIEWS_JSON, SESSIONS_JSON, USERS_JSON


def load_businesses(
    input_filepath: Optional[str] = None,
) -> list[dict]:
    """
    Reads a JSON file and returns information about a businesses as a list.

    Args:
        input_filepath (str, optional): Input filepath. Defaults to config BUSINESSES_JSON.

    Returns:
        list[dict]: Information about the business.
    """
    if input_filepath is None:
        input_filepath = str(BUSINESSES_JSON)

    with open(input_filepath, "r") as f:
        return json.load(f)


def save_businesses(
    businesses: list[dict],
    output_filepath: Optional[str] = None,
    io_type: str = "a",
) -> None:
    """
    Saves businesses taken from OverpassAPI to a JSON file.

    Args:
        businesses (list[dict]): List containing businesses info.
        output_filepath (str, optional): Output filepath. Defaults to config BUSINESSES_JSON.
        io_type (str, optional): Whether to rewrite, delete, or append to file. Defaults to 'a'.
    """
    if output_filepath is None:
        output_filepath = str(BUSINESSES_JSON)

    with open(output_filepath, io_type) as f:
        json.dump(businesses, f, indent=4)


def load_users(input_filepath: Optional[str] = None) -> list[dict]:
    """
    Loads a JSON file that contains all users.

    Args:
        input_filepath (str, optional): Filepath to user JSON file. Defaults to config USERS_JSON.

    Returns:
        list[dict]: List containing the dictionaries with all users and their data.
    """
    if input_filepath is None:
        input_filepath = str(USERS_JSON)

    with open(input_filepath, "r") as f:
        return json.load(f)


def save_users(
    users: list[dict], output_filepath: Optional[str] = None, io_type: str = "a"
) -> None:
    """
    Saves users to a JSON file.

    Args:
        users (list[dict]): List containing user dictionaries to append.
        output_filepath (str, optional): Filepath to output JSON file. Defaults to config USERS_JSON.
        io_type (str, optional): Whether to rewrite, delete, or append to file. Defaults to "a".
    """
    if output_filepath is None:
        output_filepath = str(USERS_JSON)

    if io_type == "a":
        existing_users = load_users(output_filepath)
        existing_users.extend(users)
        all_users = existing_users
    else:
        all_users = users

    with open(output_filepath, "w") as f:
        json.dump(all_users, f, indent=4)


def load_sessions(input_filepath: Optional[str] = None) -> list[dict]:
    """
    Loads a JSON file that contains all active sessions.

    Args:
        input_filepath (str, optional): Filepath to sessions JSON file. Defaults to config SESSIONS_JSON.

    Returns:
        list[dict]: List containing session dictionaries.
    """
    if input_filepath is None:
        input_filepath = str(SESSIONS_JSON)

    try:
        with open(input_filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_session(
    session_info: dict,
    output_filepath: Optional[str] = None,
    io_type: str = "a",
) -> None:
    """
    Saves a session to the sessions JSON file.

    Args:
        session_info (dict): Dictionary containing session data with 'session_id' key.
        output_filepath (str, optional): Filepath to output JSON file. Defaults to config SESSIONS_JSON.
        io_type (str, optional): Whether to append or overwrite. Defaults to "a".
    """
    if "session_id" not in session_info:
        raise ValueError("ERROR: session_info must contain 'session_id' key.")

    if output_filepath is None:
        output_filepath = str(SESSIONS_JSON)

    if io_type == "a":
        sessions = load_sessions(output_filepath)
        sessions.append(session_info)
    else:
        sessions = [session_info]

    with open(output_filepath, "w") as f:
        json.dump(sessions, f, indent=4)


def delete_session(session_id: str, output_filepath: Optional[str] = None) -> None:
    """
    Deletes a session from the sessions JSON file.

    Args:
        session_id (str): The session ID to delete.
        output_filepath (str, optional): Filepath to sessions JSON file. Defaults to config SESSIONS_JSON.
    """
    if output_filepath is None:
        output_filepath = str(SESSIONS_JSON)

    sessions = load_sessions(output_filepath)

    session_found = False
    for i, session in enumerate(sessions):
        if session.get("session_id") == session_id:
            sessions.pop(i)
            session_found = True
            break

    if not session_found:
        raise ValueError(f"ERROR: Session {session_id} does not exist.")

    with open(output_filepath, "w") as f:
        json.dump(sessions, f, indent=4)


def load_reviews(input_filepath: Optional[str] = None) -> list[dict]:
    """
    Loads a JSON file that contains all reviews.

    Args:
        input_filepath (str, optional): Filepath to reviews JSON file. Defaults to config REVIEWS_JSON.

    Returns:
        list[dict]: List containing review dictionaries.
    """
    if input_filepath is None:
        input_filepath = str(REVIEWS_JSON)

    with open(input_filepath, "r") as f:
        return json.load(f)


def save_reviews(
    new_reviews: list[dict],
    output_filepath: Optional[str] = None,
    io_type: str = "a",
) -> None:
    """
    Function to save new reviews to JSON file

    Args:
        new_reviews (list[dict]): List of review dictionaries to save.
        output_filepath (str, optional): Filepath to output JSON file. Defaults to config REVIEWS_JSON.
        io_type (str, optional): Whether to append or overwrite. Defaults to "a".
    """
    if output_filepath is None:
        output_filepath = str(REVIEWS_JSON)

    if io_type == "a":
        existing_reviews = load_reviews(output_filepath)
        existing_reviews.extend(new_reviews)
        all_reviews = existing_reviews
    else:
        all_reviews = new_reviews

    with open(output_filepath, "w") as f:
        json.dump(all_reviews, f, indent=4)
