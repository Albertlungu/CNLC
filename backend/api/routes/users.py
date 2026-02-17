"""
./backend/api/routes/users.py

User-related API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request
from pydantic import ValidationError

import backend.core.user_manager as um
import backend.storage.json_handler as jh

users_bp = Blueprint("users", __name__, url_prefix="/api/user")


@users_bp.route("/<int:user_id>/upgrade-to-business", methods=["POST"])
def upgrade_to_business(user_id: int) -> Response:
    """Upgrade a normal user to a business owner."""
    data = request.json or {}
    business_id = data.get("businessId")
    business_name = data.get("businessName")

    users = jh.load_users()
    user = um.get_user_by_id(user_id, users)
    if not user:
        return make_response(jsonify({"status": "error", "message": "User not found."}), 404)

    if "business" in user.get("roles", []):
        return make_response(jsonify({"status": "error", "message": "Already a business owner."}), 400)

    # Add business role
    roles = user.get("roles", ["user"])
    if "business" not in roles:
        roles.append("business")
    user["roles"] = roles

    if business_id:
        user["businessId"] = int(business_id)

    jh.save_users(users)
    return jsonify({"status": "success", "user": {"id": user["id"], "roles": user["roles"], "businessId": user.get("businessId")}})


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
