"""
./backend/api/routes/users.py

User-related API endpoints.
"""

import random

from flask import Blueprint, Response, jsonify, make_response, request
from pydantic import ValidationError

import backend.core.user_manager as um
import backend.storage.json_handler as jh

users_bp = Blueprint("users", __name__, url_prefix="/api/user")


@users_bp.route("/<int:user_id>/upgrade-to-business", methods=["POST"])
def upgrade_to_business(user_id: int) -> Response:
    """Upgrade a normal user to a business owner with verification details."""
    data = request.json or {}
    business_id = data.get("businessId")
    business_name = data.get("businessName")
    business_address = data.get("businessAddress")
    business_phone = data.get("businessPhone")
    business_category = data.get("businessCategory")

    users = jh.load_users()
    user = um.get_user_by_id(user_id, users)
    if not user:
        return make_response(
            jsonify({"status": "error", "message": "User not found."}), 404
        )

    if "business" in user.get("roles", []):
        return make_response(
            jsonify({"status": "error", "message": "Already a business owner."}), 400
        )

    # Require at least business name for verification
    if not business_name:
        return make_response(
            jsonify(
                {
                    "status": "error",
                    "message": "Business name is required for verification.",
                }
            ),
            400,
        )

    businesses = jh.load_businesses()

    if business_id:
        # Validate that the business ID exists
        business_id = int(business_id)
        found = any(b.get("id") == business_id for b in businesses)
        if not found:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": f"Business ID {business_id} not found.",
                    }
                ),
                404,
            )
    else:
        # Create a new business entry
        new_id = random.randint(90000000, 99999999)
        while any(b.get("id") == new_id for b in businesses):
            new_id = random.randint(90000000, 99999999)

        new_business = {
            "id": new_id,
            "name": business_name,
            "address": business_address or "",
            "phone": business_phone or "",
            "category": business_category or "general",
            "latitude": 0.0,
            "longitude": 0.0,
            "opening_hours": None,
            "cuisine": None,
            "website": None,
            "image_url": None,
        }
        businesses.append(new_business)
        jh.save_businesses(businesses)
        business_id = new_id

    # Add business role
    roles = user.get("roles", ["user"])
    if "business" not in roles:
        roles.append("business")
    user["roles"] = roles
    user["businessId"] = business_id

    jh.save_users(users)
    return jsonify(
        {
            "status": "success",
            "user": {
                "id": user["id"],
                "roles": user["roles"],
                "businessId": user.get("businessId"),
            },
        }
    )


@users_bp.route("/create", methods=["POST"])
def create_user() -> Response:
    """
    RESTful API endpoint for creating a user.

    Returns:
        Response: Status.
    """
    username = request.args.get("username", type=str)
    email = request.args.get("email", type=str)
    phone = request.args.get("phone", type=str)
    password = request.args.get("password", type=str)
    first_name = request.args.get("firstName", type=str)
    last_name = request.args.get("lastName", type=str)
    city = request.args.get("city", type=str)
    country = request.args.get("country", "Canada", type=str)
    users = jh.load_users()

    try:
        if (
            username is not None
            and email is not None
            and phone is not None
            and password is not None
            and first_name is not None
            and last_name is not None
            and city is not None
        ):
            user = um.create_user(
                username,
                email,
                phone,
                password,
                first_name,
                last_name,
                city,
                country,
                users,
            )
            resp = jsonify({"status": "success", "user": user})
            return make_response(resp, 200)
        else:
            resp = jsonify(
                {"status": "error", "message": "One or more fields missing."}
            )
            return make_response(resp, 400)
    except ValidationError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)
