"""
./backend/models/business.py

Serves as a blueprint for what the data should look like.
Automatic validation according to this blueprint.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional

class Address(BaseModel):
    """
    Validator model for address data.

    Args:
        BaseModel (class): BaseModel class from Pydantic.
    """
    street: Optional[str] = None
    housenumber: Optional[str] = None
    city: Optional[str] = 'Ottawa'
    country: Optional[str] = 'Canada'
    postcode: Optional[str] = None

class Business(BaseModel):
    """
    Main business validation model
    """
    id: int = Field(..., description="Unique ID")
    name: str = Field(..., min_length=1)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    opening_hours: Optional[str] = None
    category: str
    cuisine: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None

    tlds = [
        '.ca',
        '.com',
        '.biz',
        '.net',
        '.org',
        '.co',
        '.shop',
        '.store',
        '.coffee',
        '.restaurant'
    ]

    @field_validator('phone')
    @classmethod
    def validate_phone(
        cls,
        value:Optional[str]
    ) -> Optional[str]:
        """
        Custom validation logic for phone number.

        Args:
            value (Optional[str]): Phone number value (str to account for characters like '+')

        Returns:
            Optional[str]: Validated value
        """
        if value is None:
            return value

        if not value.startswith('+'):
            value = '+' + value
        try:
            digits = value[1:]

            digits = digits.replace('-', '')
            digits = digits.replace('(', '')
            digits = digits.replace(')', '')
            digits = digits.replace(' ', '')

            digits = int(digits)
            return value
        except TypeError:
            return None

    @field_validator('website')
    @classmethod
    def validate_website(
        cls,
        link:Optional[str],
    ) -> Optional[str]:

        if link is None:
            return link

        if not link.startswith('http://') and link.startswith('https://'):
            return 'http://' + link

        return link