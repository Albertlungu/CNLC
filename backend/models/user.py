"""
./backend/models/user.py

Pydantic user model. Email validation, password strength requirements, etc.
"""

from pydantic import BaseModel, Field, field_validator, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional

class UserProfile(BaseModel):
    firstName: str = Field(..., description="User's First Name")
    lastName: str = Field(..., description="User's Last Name")

class UserLocation(BaseModel):
    country: str = "Canada"
    city: str = Field(..., description="User City")

class User(BaseModel):
    id: int = Field(..., description="Unique User ID")
    username: str = Field(..., description="Unique Username")
    email: EmailStr
    phone: PhoneNumber
    isActive: bool
    roles: list[str] = Field(..., description="User Roles")
    bookmarks: list[int] = Field(..., description="Containing Bookmarked Business IDs")

    @field_validator('id')
    @classmethod
    def validate_id(
        cls,
        id_num:int
    ) -> int:
        """
        Validates the user ID to be exactly 4 digits.

        Args:
            id_num (int): The user's numerical ID

        Raises:
            ValueError: If the ID is not 4 digits

        Returns:
            int: The ID otherwise
        """
        if len(str(id_num)) == 4:
            return id_num
        raise ValueError("ERROR: ID must be exactly 4 digits long")

    @field_validator('username')
    @classmethod
    def validate_username(
        cls,
        username:str
    ) -> str:
        """
        Ensuring that the username does not have any disallowed characters.

        Args:
            username (str): The user's unique username.

        Raises:
            ValueError: If the user entered disallowed characters.

        Returns:
            str: The user's unique username.
        """
        disallowed_chars = [
        " ", "\t", "\n", "\r",
        "/", "\\", "?", "#", "%", "&", "=", "+", ":", ";", ",",
        "'", '"', "`",
        "(", ")", "{", "}", "[", "]", "<", ">",
        "*", "^", "|", "~", "!",
        ".", "@"
        ]

        if any(disallowed_chars) in list(username):
            raise ValueError("""ERROR: Username must contain only:
                             lowercase letters (a-z), digits (0-9), _, and -.""")
        return username
