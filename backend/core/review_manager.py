"""
./backend/core/review_manager.py

CRUD operations for reviews
"""

from typing import Any, Optional, Union

from pydantic import ValidationError

import backend.storage.json_handler as jh
from backend.models import user
from backend.models.review import Review
from config.config import REVIEWS_JSON


def create_review(
    business_id: int,
    user_id: int,
    username: str,
    rating: int,
    review: str,
    helpful: int = 0,
    reviews: Optional[list[dict]] = None,
):
    if not reviews:
        reviews = jh.load_reviews()

    try:
        validated_review = Review(
            business_id=business_id,
            user_id=user_id,
            username=username,
            rating=rating,
            review=review,
            helpful=helpful,
            review_id=9999999 + len(reviews),
        )

        new_review = [validated_review.model_dump()]

        jh.save_reviews(new_review)

        return new_review[0]

    except ValidationError as e:
        return f"ERROR: Review information invalid. {str(e)}"


def delete_reviews(
    reviews: list[dict],
    review_id: int,
    username: str,
    output_filepath: Optional[str] = None,
) -> None:
    """
    Deletes a specific review from the reviews list.

    Args:
        reviews (list[dict]): List of all review dictionaries.
        review_id (int): The ID of the review to delete.
        username (str): Username of the review author (for verification).
        output_filepath (str, optional): Filepath to output JSON file. Defaults to config REVIEWS_JSON.

    Raises:
        ValueError: If no matching review is found (target_review remains uninitialized).

    Note:
        Users can only delete their own reviews (username must match).
    """
    if output_filepath is None:
        output_filepath = str(REVIEWS_JSON)

    target_review = None
    for idx, review in enumerate(reviews):
        if review_id == review["reviewId"] and username == review["username"]:
            target_review = idx

    if not target_review:
        raise ValueError(
            f"ERROR: Review {review_id} not found or does not belong to {username}"
        )

    del reviews[target_review]

    jh.save_reviews(reviews, io_type="w")
