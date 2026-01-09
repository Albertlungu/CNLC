"""
./backend/core/user_manager.py

Functions to manipulate the users on the platform.
"""

import sys
import os
from pathlib import Path
from typing import Union, Any

from pydantic import ValidationError

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.storage.json_handler as jh
from backend.models.user import User, UserProfile, UserLocation
from pydantic_extra_types.phone_numbers import PhoneNumber

def create_user(
        username:str,
        email:str,
        phone:str,
        first_name:str,
        last_name:str,
        city:str,
        country:str="Canada",
        users:list[dict]=jh.load_users()
        ) -> Union[str, None]:
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
        NameError: If the username already exists.

    Returns:
        Union[str, None]: Basically always returns str, unless an error is present.
    """

    for user in users:
        if user['username'] == username:
            raise  NameError("ERROR: Username is not available.")

    try:
        validated_user = User(
            id=9999999 + len(users),
            username=username,
            email=email,
            phone=PhoneNumber(phone),
            isActive=True,
            roles=["user"],
            bookmarks=[],
            profile=UserProfile(firstName=first_name, lastName=last_name),
            location=UserLocation(country=country, city=city)
        )

        new_user = [validated_user.model_dump()]

        jh.save_users(new_user)

    except ValidationError as e:
        return f"ERROR: User information invalid. {str(e)}"

def remove_user(username:str, users:list[dict]=jh.load_users()):
    """
    Removes a user by username.

    Args:
        username (str): Unique username.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().
    """
    for idx, user in enumerate(users):
        if user['username'] == username:
            del users[idx]

    jh.save_users(users=users, io_type='w')

def edit_user(
        username:str,
        field:str,
        new_value:Any,
        users:list[dict]=jh.load_users()
        ):
    """
    Edits a specific user.

    Args:
        username (str): Unique username.
        field (str): Field to be modified
        new_value (Any): Value to replace the old one.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().
    """
    for user in users:
        if user['username'] == username:
            if field == "firstName" or field == "lastName": # If in profile sub-dict
                user['profile'][field] = new_value
            elif field == "country" or field == "city": # If in location sub-dict
                user['location'][field] = new_value
            else:
                user[field] = new_value

    jh.save_users(users, io_type='w')

def get_user_by_username(
        username:str,
        users:list[dict]=jh.load_users()
        ) -> dict:
    """
    Iterates through a list of dicts to get a user given their username.

    Args:
        username (str): Unique username.
        users (list[dict], optional): Contains all users. Defaults to jh.load_users().

    Raises:
        NameError: If the username does not exist.

    Returns:
        dict: User that was found.
    """
    for user in users:
        if user['username'] == username:
            return user

    raise NameError("ERROR: Username not found.")
