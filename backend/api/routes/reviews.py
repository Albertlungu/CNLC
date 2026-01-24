"""
./backend/api/routes/reviews.py

Review-related API endpoints.
"""

import os
import uuid
from flask import Blueprint, Response, jsonify, make_response, request
from werkzeug.utils import secure_filename

import backend.core.review_manager as rm
from config.config import PROJECT_ROOT

reviews_bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")

UPLOAD_FOLDER = PROJECT_ROOT / "data" / "uploads" / "reviews"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@reviews_bp.route("", methods=["GET"])
def get_reviews() -> Response:
    """
    GET /api/reviews?business_id=X
    Returns all reviews for a specific business.
    """
    business_id = request.args.get("business_id", type=int)

    if not business_id:
        resp = jsonify({"status": "error", "message": "business_id is required"})
        return make_response(resp, 400)

    try:
        reviews = rm.get_reviews_for_business(business_id)
        avg_rating = rm.calculate_average_rating(business_id)

        resp = jsonify({
            "status": "success",
            "reviews": reviews,
            "count": len(reviews),
            "averageRating": avg_rating,
        })
        return make_response(resp, 200)

    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/<int:review_id>", methods=["GET"])
def get_review(review_id: int) -> Response:
    """
    GET /api/reviews/<review_id>
    Returns a specific review by ID.
    """
    try:
        review = rm.get_review_by_id(review_id)

        if not review:
            resp = jsonify({"status": "error", "message": "Review not found"})
            return make_response(resp, 404)

        resp = jsonify({
            "status": "success",
            "review": review,
        })
        return make_response(resp, 200)

    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("", methods=["POST"])
def create_review() -> Response:
    """
    POST /api/reviews
    Creates a new review for a business.

    Request body:
    {
        "businessID": int,
        "userID": int,
        "username": str,
        "rating": int (1-5),
        "review": str,
        "photos": [str] (optional, list of photo URLs)
    }
    """
    data = request.get_json()

    if not data:
        resp = jsonify({"status": "error", "message": "Request body is required"})
        return make_response(resp, 400)

    required_fields = ["businessID", "userID", "username", "rating", "review"]
    for field in required_fields:
        if field not in data:
            resp = jsonify({"status": "error", "message": f"Missing required field: {field}"})
            return make_response(resp, 400)

    try:
        review = rm.create_review(
            business_id=data["businessID"],
            user_id=data["userID"],
            username=data["username"],
            rating=data["rating"],
            review_text=data["review"],
            photos=data.get("photos", []),
        )

        resp = jsonify({
            "status": "success",
            "message": "Review created successfully",
            "review": review,
        })
        return make_response(resp, 201)

    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/<int:review_id>", methods=["PUT"])
def update_review(review_id: int) -> Response:
    """
    PUT /api/reviews/<review_id>
    Updates an existing review.

    Request body:
    {
        "username": str (required for verification),
        "rating": int (optional),
        "review": str (optional),
        "photos": [str] (optional)
    }
    """
    data = request.get_json()

    if not data:
        resp = jsonify({"status": "error", "message": "Request body is required"})
        return make_response(resp, 400)

    if "username" not in data:
        resp = jsonify({"status": "error", "message": "Username is required for verification"})
        return make_response(resp, 400)

    try:
        review = rm.update_review(
            review_id=review_id,
            username=data["username"],
            rating=data.get("rating"),
            review_text=data.get("review"),
            photos=data.get("photos"),
        )

        resp = jsonify({
            "status": "success",
            "message": "Review updated successfully",
            "review": review,
        })
        return make_response(resp, 200)

    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/<int:review_id>", methods=["DELETE"])
def delete_review(review_id: int) -> Response:
    """
    DELETE /api/reviews/<review_id>
    Deletes a review.

    Request body:
    {
        "username": str (required for verification)
    }
    """
    data = request.get_json()

    if not data or "username" not in data:
        resp = jsonify({"status": "error", "message": "Username is required for verification"})
        return make_response(resp, 400)

    try:
        rm.delete_review(review_id=review_id, username=data["username"])

        resp = jsonify({
            "status": "success",
            "message": "Review deleted successfully",
        })
        return make_response(resp, 200)

    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/<int:review_id>/replies", methods=["POST"])
def add_reply(review_id: int) -> Response:
    """
    POST /api/reviews/<review_id>/replies
    Adds a reply to a review.

    Request body:
    {
        "userID": int,
        "username": str,
        "content": str
    }
    """
    data = request.get_json()

    if not data:
        resp = jsonify({"status": "error", "message": "Request body is required"})
        return make_response(resp, 400)

    required_fields = ["userID", "username", "content"]
    for field in required_fields:
        if field not in data:
            resp = jsonify({"status": "error", "message": f"Missing required field: {field}"})
            return make_response(resp, 400)

    try:
        reply = rm.add_reply_to_review(
            review_id=review_id,
            user_id=data["userID"],
            username=data["username"],
            content=data["content"],
        )

        resp = jsonify({
            "status": "success",
            "message": "Reply added successfully",
            "reply": reply,
        })
        return make_response(resp, 201)

    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/<int:review_id>/replies/<int:reply_id>", methods=["DELETE"])
def delete_reply(review_id: int, reply_id: int) -> Response:
    """
    DELETE /api/reviews/<review_id>/replies/<reply_id>
    Deletes a reply from a review.

    Request body:
    {
        "username": str (required for verification)
    }
    """
    data = request.get_json()

    if not data or "username" not in data:
        resp = jsonify({"status": "error", "message": "Username is required for verification"})
        return make_response(resp, 400)

    try:
        rm.delete_reply(
            review_id=review_id,
            reply_id=reply_id,
            username=data["username"],
        )

        resp = jsonify({
            "status": "success",
            "message": "Reply deleted successfully",
        })
        return make_response(resp, 200)

    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/<int:review_id>/helpful", methods=["POST"])
def vote_helpful(review_id: int) -> Response:
    """
    POST /api/reviews/<review_id>/helpful
    Increments the helpful vote count for a review.
    """
    try:
        review = rm.vote_helpful(review_id)

        resp = jsonify({
            "status": "success",
            "message": "Vote recorded",
            "helpful": review["helpful"],
        })
        return make_response(resp, 200)

    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/upload", methods=["POST"])
def upload_photo() -> Response:
    """
    POST /api/reviews/upload
    Uploads a photo for a review.
    Returns the URL path to the uploaded photo.
    """
    if "photo" not in request.files:
        resp = jsonify({"status": "error", "message": "No photo file provided"})
        return make_response(resp, 400)

    file = request.files["photo"]

    if file.filename == "":
        resp = jsonify({"status": "error", "message": "No file selected"})
        return make_response(resp, 400)

    if not allowed_file(file.filename):
        resp = jsonify({"status": "error", "message": "File type not allowed"})
        return make_response(resp, 400)

    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = UPLOAD_FOLDER / filename

        file.save(str(filepath))

        photo_url = f"/uploads/reviews/{filename}"

        resp = jsonify({
            "status": "success",
            "message": "Photo uploaded successfully",
            "photoUrl": photo_url,
        })
        return make_response(resp, 201)

    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@reviews_bp.route("/check", methods=["GET"])
def check_user_review() -> Response:
    """
    GET /api/reviews/check?business_id=X&user_id=Y
    Checks if a user has already reviewed a business.
    """
    business_id = request.args.get("business_id", type=int)
    user_id = request.args.get("user_id", type=int)

    if not business_id or not user_id:
        resp = jsonify({"status": "error", "message": "business_id and user_id are required"})
        return make_response(resp, 400)

    try:
        has_reviewed = rm.user_has_reviewed_business(user_id, business_id)

        resp = jsonify({
            "status": "success",
            "hasReviewed": has_reviewed,
        })
        return make_response(resp, 200)

    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)
