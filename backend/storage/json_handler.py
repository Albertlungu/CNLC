"""
./backend/storage/json_handler.py

Handles saving and loading JSON files from their pipelines.
"""

import json
from pathlib import Path
from typing import Union


def load_businesses(
    input_filepath: str = "../data/businesses.json",
) -> list[dict]:
    """
    Reads a JSON file and returns information about a businesses as a list.

    Args:
        input_filepath (str, optional): Input filepath. Defaults to '../data/businesses.json'.

    Returns:
        list[dict]: Information about the business.
    """
    with open(input_filepath, "r") as f:
        return json.load(f)


def save_businesses(
    businesses: list[dict],
    output_filepath: str = "../data/businesses.json",
    io_type: str = "a",
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
        output_filepath = str(project_root / "data" / "businesses.json")

    with open(output_filepath, io_type) as f:
        json.dump(businesses, f, indent=1)


def load_users(input_filepath: str = "../data/users.json") -> list[dict]:
    """
    Loads a JSON file that contains all users.

    Args:
        input_filepath (str, optional): Filepath to user JSON file. Defaults to "data/users.json".

    Returns:
        list[dict]: List containing the dictionaries with all users and their data.
    """
    with open(input_filepath, "r") as f:
        return json.load(f)


def save_users(
    users: list[dict], output_filepath: str = "../data/users.json", io_type: str = "a"
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
        output_filepath = str(project_root / "data" / "businesses.json")

    with open(output_filepath, io_type) as f:
        json.dump(users, f, indent=1)


def load_sessions(input_filepath: str = "../data/sessions.json") -> list[dict]:
    """
    Loads a JSON file that contains all active sessions.

    Args:
        input_filepath (str, optional): Filepath to sessions JSON file. Defaults to "../data/sessions.json".

    Returns:
        list[dict]: List containing session dictionaries.
    """
    project_root = Path(__file__).parent.parent.parent
    filepath = str(project_root / "data" / "sessions.json")

    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_session(
    session_info: dict,
    output_filepath: str = "../data/sessions.json",
    io_type: str = "a",
) -> None:
    """
    Saves a session to the sessions JSON file.

    Args:
        session_info (dict): Dictionary containing session data with 'session_id' key.
        output_filepath (str, optional): Filepath to output JSON file. Defaults to "../data/sessions.json".
        io_type (str, optional): Whether to append or overwrite. Defaults to "a".
    """
    if "session_id" not in session_info:
        raise ValueError("ERROR: session_info must contain 'session_id' key.")

    project_root = Path(__file__).parent.parent.parent
    output_filepath = str(project_root / "data" / "sessions.json")

    if io_type == "a":
        sessions = load_sessions(output_filepath)
        sessions.append(session_info)
    else:
        sessions = [session_info]

    with open(output_filepath, "w") as f:
        json.dump(sessions, f, indent=1)


def delete_session(
    session_id: str, output_filepath: str = "../data/sessions.json"
) -> None:
    """
    Deletes a session from the sessions JSON file.

    Args:
        session_id (str): The session ID to delete.
        output_filepath (str, optional): Filepath to sessions JSON file. Defaults to "../data/sessions.json".
    """
    project_root = Path(__file__).parent.parent.parent
    output_filepath = str(project_root / "data" / "sessions.json")

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
        json.dump(sessions, f, indent=1)
