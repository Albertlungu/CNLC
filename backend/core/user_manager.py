"""
./backend/core/user_manager.py

Functions to manipulate the users on the platform.
"""

from typing import Any, Optional, Union

from pydantic import ValidationError
from pydantic_extra_types.phone_numbers import PhoneNumber

import backend.storage.json_handler as jh
import backend.utils.password as pw
from backend.models.user import User, UserLocation, UserProfile


def create_user(
    username: str,
    email: str,
    phone: str,
    password: str,
    first_name: str,
    last_name: str,
    city: str,
    country: str = "Canada",
    users: Optional[list[dict]] = None,
) -> Union[str, dict]:
    """
    Creates a user validated by model.

    Args:
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().
        username (str): Unique username.
        email (str): User's email.
        phone (str): User phone number.
        first_name (str): User's first name.
        last_name (str): User's last name.
        city (str): User's city of residence.
        country (str, optional): User's country of residence. Defaults to "Canada".

    Raises:
        ValueError: If the username already exists.
        ValidationError: If the user info is invalid (Pydantic validation).

    Returns:
        Union[str, dict]: Returns the new user as a dictionary. If an error is present, returns an error message.
    """
    if not users:
        users = jh.load_users()

    for user in users:
        if user["username"] == username:
            raise ValueError("ERROR: Username is not available.")

    try:
        validated_user = User(
            id=9999999 + len(users),
            username=username,
            email=email,
            phone=PhoneNumber(phone),
            password_hash=pw.hash_password(password),
            isActive=True,
            roles=["user"],
            bookmarks=[],
            profile=UserProfile(firstName=first_name, lastName=last_name),
            location=UserLocation(country=country, city=city),
        )

        new_user = [validated_user.model_dump()]

        jh.save_users(new_user)

        return new_user[0]

    except ValidationError as e:
        return f"ERROR: User information invalid. {str(e)}"


def remove_user(username: str, users: Optional[list[dict]] = None):
    """
    Removes a user by username.

    Args:
        username (str): Unique username.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Raises:
        ValueError: When the user does not exist.
    """
    if not users:
        users = jh.load_users()

    user_exists = False
    for idx, user in enumerate(users):
        if user["username"] == username:
            user_exists = True
            del users[idx]
            break
    if user_exists:
        jh.save_users(users=users, io_type="w")
    else:
        raise ValueError("ERROR: User does not exist.")


def edit_user(
    username: str, field: str, new_value: Any, users: Optional[list[dict]] = None
):
    """
    Edits a specific user.

    Args:
        username (str): Unique username.
        field (str): Field to be modified
        new_value (Any): Value to replace the old one.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Raises:
        ValueError: When user does not exist.
    """
    if not users:
        users = jh.load_users()

    user_exists = False
    for user in users:
        if user["username"] == username:
            user_exists = True
            if field == "firstName" or field == "lastName":  # If in profile sub-dict
                user["profile"][field] = new_value
            elif field == "country" or field == "city":  # If in location sub-dict
                user["location"][field] = new_value
            elif field == "password_hash":  # If modifying password, must encrypt first
                user["password_hash"] = pw.hash_password(new_value)
            else:
                user[field] = new_value
            break

    if user_exists:
        jh.save_users(users, io_type="w")
    else:
        raise ValueError("ERROR: User does not exist.")


def get_user_by_username(username: str, users: Optional[list[dict]] = None) -> dict:
    """
    Iterates through a list of dicts to get a user given their username.

    Args:
        username (str): Unique username.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Raises:
        ValueError: If the username does not exist.

    Returns:
        dict: User that was found.
    """
    if not users:
        users = jh.load_users()

    for user in users:
        if user["username"] == username:
            return user

    raise ValueError("ERROR: Username not found.")


def authenticate_user(
    username: str, password: str, users: Optional[list[dict]] = None
) -> bool:
    """
    Verifies if password matches hashed value (for logging back in).

    Args:
        username (str): Unique username.
        password (str): Password in words.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Raises:
        ValueError: If user does not exist or password is incorrect.

    Returns:
        bool: If passwords match or not.
    """
    if not users:
        users = jh.load_users()

    for user in users:
        if user["username"] == username:
            if pw.verify_password(password, user["password_hash"]):
                return True
            else:
                raise ValueError("ERROR: Incorrect password.")

    raise ValueError("ERROR: Could not find user.")


def get_user_by_id(user_id: int, users: Optional[list[dict]] = None) -> Optional[dict]:
    """
    Gets a user by their ID.

    Args:
        user_id (int): The user's ID.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Returns:
        Optional[dict]: User dict if found, None otherwise.
    """
    if not users:
        users = jh.load_users()

    for user in users:
        if user["id"] == user_id:
            return user
    return None


def search_users(query: str, users: Optional[list[dict]] = None) -> list[dict]:
    """
    Searches users by username (case-insensitive partial match).

    Args:
        query (str): Search string.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Returns:
        list[dict]: Matching users.
    """
    if not users:
        users = jh.load_users()

    query_lower = query.lower()
    return [u for u in users if query_lower in u["username"].lower()]


# TODO: (Maybe: Implement a "Forgot Password" feature)
