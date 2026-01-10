"""
./backend/api/server.py

Entry point for web API. The main file that ties everything together.
"""

import os
import sys
from typing import Any, Literal, Tuple, Union

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, request
from flask_cors import CORS
from pydantic import ValidationError

# Load environment variables from .env file
load_dotenv()

project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

import backend.core.bookmark_manager as book
import backend.core.business_manager as buis
import backend.core.user_manager as um
import backend.storage.json_handler as jh
from backend.core.verification import verify_recaptcha

app = Flask(__name__)  # Creating the flask application

CORS(app, origins="*")  # Allow all origins to interact with webpage

app.config["JSON_SORT_KEYS"] = False  # Preserves original JSON mappings
app.config["JSON_AS_ASCII"] = False
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

# ================== Error handling ================


@app.errorhandler(404)
def not_found(error):
    """
    Handling 404 errors with a JSON response (resource not found)
    """
    return jsonify({"error": "Resource not found."}), 404


@app.errorhandler(400)
def bad_request(error):
    """
    Handle 400 errors with a JSON response (Pydantic validation)
    """
    return jsonify({"error": "Invalid request."}), 400


@app.errorhandler(500)
def server_error(error):
    """
    Handle 500 errors with a JSON response (internal server error)
    """
    return jsonify({"error": "Internal server error."}), 500


@app.errorhandler(403)
def forbidden(error):
    """
    Handle 403 errors with JSON response (access forbidden)
    """
    return jsonify({"error": "Forbidden"}), 403


# ======================= Health check ======================


@app.route("/health", methods=["GET"])
def health_check():
    """
    Simple health check to ensure that server is running
    """
    return jsonify({"status": "healthy"}), 200


# ======================= API Routes ====================


# ========= Businesses =========


@app.route("/api/businesses", methods=["GET"])
def get_businesses() -> Response:
    """
    RESTful endpoint: GET /api/businesses
    """
    # Extract query parameters
    search_query = request.args.get("search", type=str)
    category = request.args.get("category", type=str)
    filepath = request.args.get("filepath", "data/businesses.json", type=str)
    radius = request.args.get("radius", 10, type=int)
    lat1 = request.args.get("lat1", type=float)
    lon1 = request.args.get("lon1", type=float)

    try:
        # Start with all businesses
        results = jh.load_businesses(input_filepath=filepath)

        # Apply radius filter first if provided
        if lat1 and lon1:
            if radius != 0:
                results = buis.filter_by_radius(results, radius, lat1, lon1)
            else:
                resp = jsonify({"error": "Radius must be nonzero"})
                return make_response(resp, 400)

        # Apply category filter if provided
        if category:
            results = buis.filter_by_category(results, category)

        # Apply search filter if provided (fuzzy matching)
        if search_query:
            results = buis.search_by_name(results, search_query)

        resp = jsonify(
            {"status": "success", "businesses": results, "count": len(results)}
        )
        return make_response(resp, 200)

    except ValueError as e:
        # Handle not found errors from business_manager
        resp = jsonify({"error": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        # Handle unexpected errors
        resp = jsonify({"error": "Internal server error"})
        return make_response(resp, 500)


@app.route("/api/businesses/<int:business_id>", methods=["GET"])
def get_business_by_id(business_id: int) -> Response:
    """
    RESTful endpoint: GET /api/businesses/<id>

    Returns a single business by its ID.

    Example:
    - /api/businesses/123456
    """
    results = jh.load_businesses()
    try:
        results = buis.search_by_id(results, business_id=business_id)

        # Return the first (and should be only) result
        resp = jsonify(
            {
                "business": results[0] if results else None,
            }
        )
        return make_response(resp, 200)

    except ValueError as e:
        # Business not found
        resp = jsonify({"error": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        # Unexpected error
        resp = jsonify({"error": str(e)})
        return make_response(resp, 500)


@app.route("/api/users/create", methods=["POST"])
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
    first_name = request.args.get("first-name", type=str)
    last_name = request.args.get("last-name", type=str)
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
            user = um.create_user(  # noqa
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
            resp = jsonify({"status": "success"})
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


@app.route("/api/user/remove", methods=["POST"])
def remove_user() -> Response:
    """
    RESTful API endpoint to remove user.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.args.get("username", type=str)
    try:
        if username:
            um.remove_user(username)
            resp = jsonify({"status": "success"})
            return make_response(resp, 200)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)  # User not found

    resp = jsonify({"status": "error", "message": "No username given."})
    return make_response(resp, 400)  # Bad request


@app.route("/api/user/edit", methods=["POST"])
def edit_user() -> Response:
    username = request.args.get("username", type=str)
    field = request.args.get("field", type=str)
    new_value = request.args.get("new-value", type=str)

    if username and field and new_value:
        try:
            um.edit_user(username, field, new_value)
            resp = jsonify({"status": "success"})
            return make_response(resp, 200)
        except ValueError as e:
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 404)
        except Exception as e:
            # Unexpected error
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 500)
    else:
        resp = jsonify(
            {"status": "error", "message": "Username/field/value were not provided."}
        )
        return make_response(resp, 400)  # Bad request


@app.route("/api/user/get-by-username", methods=["GET"])
def get_by_username() -> Response:
    username = request.args.get("username", type=str)

    try:
        if username:
            user = um.get_user_by_username(username)
            resp = jsonify({"status": "success", "user": user})
            return make_response(resp, 200)
        else:
            resp = jsonify({"status": "error", "message": "Username was not given."})
            return make_response(resp, 400)  # Bad request
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@app.route("/api/user/auth", methods=["GET"])
def authenticate_user() -> Response:
    username = request.args.get("username", type=str)
    password = request.args.get("password", type=str)

    try:
        if username and password:
            um.authenticate_user(username, password)
            resp = jsonify({"status": "success"})
            return make_response(resp, 200)
        else:
            resp = jsonify(
                {"status": "error", "message": "Username and password not given."}
            )
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)


# ========= Verification ===========
@app.route("/api/submit-form", methods=["POST"])
def submit_form() -> Response:
    # Get token from form
    token = request.form.get("g-recaptcha-response")
    user_ip = request.remote_addr

    success, message = verify_recaptcha(
        response_token=token,
        secret_key=os.environ.get("RECAPTCHA_SECRET_KEY"),
        user_ip=user_ip,
    )

    if success:
        resp = jsonify({"status": "success"})
        return make_response(resp, 200)
    else:
        resp = jsonify({"status": "error", "message": message})
        return make_response(resp, 403)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
