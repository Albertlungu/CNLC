"""
./backend/models/review.py

Pydantic model for review JSON files.
"""

from pydantic import BaseModel, Field, field_validator


class Review(BaseModel):
    """
    Main review validation model.

    - businessID
    - user_id
    - username
    - rating
    - review
    - helpful
    - review_id
    """

    business_id: int = Field(..., description="Unique business ID")
    user_id: int = Field(..., description="Unique user ID")
    username: str = Field(..., description="Unique username")
    rating: int = Field(..., description="User's rating (1-5 stars)")
    review: str = Field(..., description="User's review/comment on this business")
    helpful: int = Field(
        default=0, description="How helpful this review is (vote count)"
    )
    review_id: int = Field(..., description="The unique review ID")

    @field_validator("userID")
    @classmethod
    def validate_user_id(cls, value: int):
        """
        Field validator for userID (must be 8 digits)
        """
        if len(str(value)) != 8:
            raise ValueError("User ID must be exactly 8 digits")
        return value

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int):
        """
        Field validator for rating (must be 1-5 stars)
        """
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5 stars")
        return value

    @field_validator("review")
    @classmethod
    def validate_review(cls, value: str):
        """
        Field validator for review text (max 1000 characters)
        """
        if len(value) > 1000:
            raise ValueError("Review must be 1000 characters or less")
        return value

    @field_validator("helpful")
    @classmethod
    def validate_helpful(cls, value: int):
        """
        Field validator for helpful count (must be non-negative)
        """
        if value < 0:
            raise ValueError("Helpful count cannot be negative")
        return value

    @field_validator("review_id")
    @classmethod
    def validate_review_id(cls, value: int):
        """
        Field validator for unique review ID (must be 8 digits)
        """
        if len(str(value)) != 8:
            raise ValueError("Unique review ID must be exactly 8 digits")
        return value
