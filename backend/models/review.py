"""
./backend/models/review.py

Pydantic model for review JSON files.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Reply(BaseModel):
    """
    Model for replies to reviews.
    """
    replyId: int = Field(..., description="Unique reply ID")
    reviewId: int = Field(..., description="ID of the review being replied to")
    userID: int = Field(..., description="User ID of the replier")
    username: str = Field(..., description="Username of the replier")
    content: str = Field(..., description="Reply text content")
    createdAt: str = Field(..., description="ISO timestamp of reply creation")

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str):
        if len(value) > 500:
            raise ValueError("Reply must be 500 characters or less")
        return value


class Review(BaseModel):
    """
    Main review validation model.
    Field names use camelCase to match JSON storage format.
    """
    businessID: int = Field(..., description="Unique business ID")
    userID: int = Field(..., description="Unique user ID")
    username: str = Field(..., description="Username of reviewer")
    rating: int = Field(..., description="User's rating (1-5 stars)")
    review: str = Field(..., description="User's review/comment on this business")
    helpful: int = Field(default=0, description="How helpful this review is (vote count)")
    reviewId: int = Field(..., description="The unique review ID")
    photos: List[str] = Field(default_factory=list, description="List of photo URLs/paths")
    replies: List[dict] = Field(default_factory=list, description="Replies to this review")
    createdAt: Optional[str] = Field(default=None, description="ISO timestamp of review creation")

    @field_validator("userID")
    @classmethod
    def validate_user_id(cls, value: int):
        if len(str(value)) != 8:
            raise ValueError("User ID must be exactly 8 digits")
        return value

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5 stars")
        return value

    @field_validator("review")
    @classmethod
    def validate_review(cls, value: str):
        if len(value) > 1000:
            raise ValueError("Review must be 1000 characters or less")
        return value

    @field_validator("helpful")
    @classmethod
    def validate_helpful(cls, value: int):
        if value < 0:
            raise ValueError("Helpful count cannot be negative")
        return value

    @field_validator("reviewId")
    @classmethod
    def validate_review_id(cls, value: int):
        if len(str(value)) != 8:
            raise ValueError("Unique review ID must be exactly 8 digits")
        return value
