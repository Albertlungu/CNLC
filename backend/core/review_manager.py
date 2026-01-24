"""
./backend/core/review_manager.py

CRUD operations for reviews
"""

from datetime import datetime
from typing import Optional, List

from pydantic import ValidationError

import backend.storage.json_handler as jh
from backend.models.review import Review, Reply
from config.config import REVIEWS_JSON


def get_reviews_for_business(business_id: int) -> List[dict]:
    """
    Get all reviews for a specific business.
    """
    reviews = jh.load_reviews()
    return [r for r in reviews if r.get("businessID") == business_id]


def get_review_by_id(review_id: int) -> Optional[dict]:
    """
    Get a specific review by its ID.
    """
    reviews = jh.load_reviews()
    for review in reviews:
        if review.get("reviewId") == review_id:
            return review
    return None


def user_has_reviewed_business(user_id: int, business_id: int) -> bool:
    """
    Check if a user has already reviewed a business.
    Returns True if the user has an existing review.
    """
    reviews = jh.load_reviews()
    for review in reviews:
        if review.get("userID") == user_id and review.get("businessID") == business_id:
            return True
    return False


def create_review(
    business_id: int,
    user_id: int,
    username: str,
    rating: int,
    review_text: str,
    photos: Optional[List[str]] = None,
) -> dict:
    """
    Creates a new review for a business.
    Enforces one review per user per business.
    """
    reviews = jh.load_reviews()

    if user_has_reviewed_business(user_id, business_id):
        raise ValueError(f"User {username} has already reviewed this business")

    review_id = 10000000 + len(reviews)

    try:
        validated_review = Review(
            businessID=business_id,
            userID=user_id,
            username=username,
            rating=rating,
            review=review_text,
            helpful=0,
            reviewId=review_id,
            photos=photos or [],
            replies=[],
            createdAt=datetime.utcnow().isoformat() + "Z",
        )

        new_review = validated_review.model_dump()
        jh.save_reviews([new_review])

        return new_review

    except ValidationError as e:
        raise ValueError(f"Review validation failed: {str(e)}")


def update_review(
    review_id: int,
    username: str,
    rating: Optional[int] = None,
    review_text: Optional[str] = None,
    photos: Optional[List[str]] = None,
) -> dict:
    """
    Updates an existing review. Only the owner can update.
    """
    reviews = jh.load_reviews()

    target_idx = None
    for idx, review in enumerate(reviews):
        if review.get("reviewId") == review_id:
            if review.get("username") != username:
                raise ValueError("You can only update your own reviews")
            target_idx = idx
            break

    if target_idx is None:
        raise ValueError(f"Review {review_id} not found")

    if rating is not None:
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        reviews[target_idx]["rating"] = rating

    if review_text is not None:
        if len(review_text) > 1000:
            raise ValueError("Review must be 1000 characters or less")
        reviews[target_idx]["review"] = review_text

    if photos is not None:
        reviews[target_idx]["photos"] = photos

    jh.save_reviews(reviews, io_type="w")

    return reviews[target_idx]


def delete_review(review_id: int, username: str) -> None:
    """
    Deletes a specific review. Only the owner can delete.
    """
    reviews = jh.load_reviews()

    target_idx = None
    for idx, review in enumerate(reviews):
        if review.get("reviewId") == review_id:
            if review.get("username") != username:
                raise ValueError("You can only delete your own reviews")
            target_idx = idx
            break

    if target_idx is None:
        raise ValueError(f"Review {review_id} not found")

    del reviews[target_idx]
    jh.save_reviews(reviews, io_type="w")


def add_reply_to_review(
    review_id: int,
    user_id: int,
    username: str,
    content: str,
) -> dict:
    """
    Adds a reply to an existing review.
    Users can reply multiple times to the same review.
    """
    reviews = jh.load_reviews()

    target_idx = None
    for idx, review in enumerate(reviews):
        if review.get("reviewId") == review_id:
            target_idx = idx
            break

    if target_idx is None:
        raise ValueError(f"Review {review_id} not found")

    if "replies" not in reviews[target_idx]:
        reviews[target_idx]["replies"] = []

    reply_id = 20000000 + sum(len(r.get("replies", [])) for r in reviews)

    try:
        validated_reply = Reply(
            replyId=reply_id,
            reviewId=review_id,
            userID=user_id,
            username=username,
            content=content,
            createdAt=datetime.utcnow().isoformat() + "Z",
        )

        reviews[target_idx]["replies"].append(validated_reply.model_dump())
        jh.save_reviews(reviews, io_type="w")

        return validated_reply.model_dump()

    except ValidationError as e:
        raise ValueError(f"Reply validation failed: {str(e)}")


def delete_reply(review_id: int, reply_id: int, username: str) -> None:
    """
    Deletes a reply from a review. Only the reply owner can delete.
    """
    reviews = jh.load_reviews()

    for review in reviews:
        if review.get("reviewId") == review_id:
            replies = review.get("replies", [])
            for idx, reply in enumerate(replies):
                if reply.get("replyId") == reply_id:
                    if reply.get("username") != username:
                        raise ValueError("You can only delete your own replies")
                    del replies[idx]
                    jh.save_reviews(reviews, io_type="w")
                    return

    raise ValueError(f"Reply {reply_id} not found in review {review_id}")


def vote_helpful(review_id: int) -> dict:
    """
    Increments the helpful vote count for a review.
    """
    reviews = jh.load_reviews()

    for idx, review in enumerate(reviews):
        if review.get("reviewId") == review_id:
            reviews[idx]["helpful"] = reviews[idx].get("helpful", 0) + 1
            jh.save_reviews(reviews, io_type="w")
            return reviews[idx]

    raise ValueError(f"Review {review_id} not found")


def calculate_average_rating(business_id: int) -> Optional[float]:
    """
    Calculate the average rating for a business based on its reviews.
    Returns None if no reviews exist.
    """
    reviews = get_reviews_for_business(business_id)
    if not reviews:
        return None

    total = sum(r.get("rating", 0) for r in reviews)
    return round(total / len(reviews), 1)
