"""
./backend/api/server.py

Entry point for web API. The main file that ties everything together.
"""

import os
import sys
from optparse import make_option
from typing import Any, Literal, Tuple, Union

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, make_response, request
from flask.sessions import SessionInterface, session_json_serializer
from flask_cors import CORS
from pydantic import ValidationError
from pydantic.json_schema import JsonSchemaWarningKind
from pydantic.type_adapter import TypeAdapterT

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
from backend.utils.session import SessionManager

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
        resp = jsonify({"error": str(e)})
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


@app.route("/api/user/create", methods=["POST"])
def create_user() -> Response:
    """
    RESTful API endpoint for creating a user.

    Returns:
        Response: Status.
    """
    username = request.json.get("username", type=str)
    email = request.json.get("email", type=str)
    phone = request.json.get("phone", type=str)
    password = request.json.get("password", type=str)
    first_name = request.json.get("first-name", type=str)
    last_name = request.json.get("last-name", type=str)
    city = request.json.get("city", type=str)
    country = request.json.get("country", "Canada", type=str)
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


# ========= Bookmarks ===========
@app.route("/api/bookmarks/add", methods=["POST"])
def add_bookmarks() -> Response:
    """
    RESTful API endpoint to add bookmarks to a user's account.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.json.get("username", type=str)
    bookmarks = request.json.get("bookmarks", type=str)

    try:
        if username and bookmarks:
            # Convert comma-separated string to list of integers
            bookmark_list = [int(b.strip()) for b in bookmarks.split(",")]
            book.create_bookmarks(username, bookmark_list)
            resp = jsonify({"status": "success"})
            return make_response(resp, 200)
        else:
            resp = jsonify(
                {"status": "error", "message": "Username or bookmarks not provided."}
            )
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@app.route("/api/bookmarks/remove", methods=["POST"])
def remove_bookmarks_route() -> Response:
    """
    RESTful API endpoint to remove bookmarks from a user's account.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.json.get("username", type=str)
    bookmarks = request.json.get("bookmarks", type=str)

    try:
        if username and bookmarks:
            # Convert comma-separated string to list of integers
            bookmark_list = [int(b.strip()) for b in bookmarks.split(",")]
            book.remove_bookmarks(username, bookmark_list)
            resp = jsonify({"status": "success"})
            return make_response(resp, 200)
        else:
            resp = jsonify(
                {"status": "error", "message": "Username or bookmarks not provided."}
            )
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@app.route("/api/bookmarks/get", methods=["GET"])
def get_bookmarks() -> Response:
    """
    RESTful API endpoint to get a user's bookmarks.

    Returns:
        Response: Status, being error or success, giving bookmark list upon success.
    """
    username = request.args.get("username", type=str)

    try:
        if username:
            bookmarks = book.get_user_bookmarks(username)
            resp = jsonify({"status": "success", "bookmarks": bookmarks})
            return make_response(resp, 200)
        else:
            resp = jsonify({"status": "error", "message": "Username not provided."})
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@app.route("/api/bookmarks/businesses", methods=["GET"])
def get_bookmarked_businesses() -> Response:
    """
    RESTful API endpoint to get all businesses bookmarked by a user.

    Returns:
        Response: Status, being error or success, giving business list upon success.
    """
    username = request.args.get("username", type=str)

    try:
        if username:
            businesses = book.get_bookmarked_businesses(username)
            resp = jsonify(
                {
                    "status": "success",
                    "businesses": businesses,
                    "count": len(businesses),
                }
            )
            return make_response(resp, 200)
        else:
            resp = jsonify({"status": "error", "message": "Username not provided."})
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


# ========= Session Management ===========
@app.route("/api/session/create", methods=["POST"])
def create_session() -> Response:
    username = request.json.get("username", type=str)

    if username:
        try:
            sm = SessionManager(username)
            session_info = sm.create_session()
            jh.save_session(session_info)
            resp = jsonify({"status": "success", "session_info": session_info})
            return make_response(resp, 200)
        except ValueError as e:
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 400)
        except Exception as e:
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 500)
    else:
        resp = jsonify({"status": "error", "message": "Username not given."})
        return make_response(resp, 400)


# ========= Auth ==========
@app.route("/api/auth/register", methods=["POST"])
def register() -> Response:
    """
    RESTful API endpoint for registering a user and creating a session.
    """
    if not request.json:
        resp = jsonify({"status": "error", "message": "No data provided."})
        return make_response(resp, 400)

    username = request.json.get("username")
    email = request.json.get("email")
    phone = request.json.get("phone")
    password = request.json.get("password")
    first_name = request.json.get("first-name")
    last_name = request.json.get("last-name")
    city = request.json.get("city")
    country = request.json.get("country", "Canada")

    try:
        if not all([username, email, phone, password, first_name, last_name, city]):
            resp = jsonify(
                {"status": "error", "message": "One or more fields missing."}
            )
            return make_response(resp, 400)

        users = jh.load_users()
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

        # Create session immediately after registration
        session_manager = SessionManager(username)
        session_info = session_manager.create_session()
        jh.save_session(session_info)

        resp = jsonify(
            {"status": "success", "user": user, "session_info": session_info}
        )
        return make_response(resp, 201)
    except ValidationError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 400)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@app.route("/api/auth/login", methods=["POST"])
def login() -> Response:
    username = request.json.get("username") if request.json else None
    password = request.json.get("password") if request.json else None

    try:
        if username and password:
            um.authenticate_user(username, password)

            # Create session on successful login
            session_manager = SessionManager(username)
            session_info = session_manager.create_session()
            jh.save_session(session_info)

            resp = jsonify({"status": "success", "session_info": session_info})
            return make_response(resp, 200)
        else:
            resp = jsonify(
                {"status": "error", "message": "Username and password not given."}
            )
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 401)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@app.route("/api/auth/logout", methods=["POST"])
def logout() -> Response:
    username = request.json.get("username", type=str)

    if username:
        try:
            sm = SessionManager(username)
            sm.destroy_session()
            resp = jsonify({"status": "success"})
            return make_response(resp, 200)
        except ValueError as e:
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 400)
        except Exception as e:
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 500)
    else:
        resp = jsonify({"status": "error", "message": "Username not given."})
        return make_response(resp, 400)


@app.route("/api/auth/profile", methods=["GET"])
def get_profile() -> Response:
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


@app.route("/api/auth/profile", methods=["POST"])
def update_profile() -> Response:
    username = request.json.get("username", type=str)
    field = request.json.get("field", type=str)
    new_value = request.json.get("new-value", type=str)

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


@app.route("/api/auth/delete", methods=["POST"])
def delete_profile() -> Response:
    """
    RESTful API endpoint to remove user.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.json.get("username", type=str)
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
