"""
./backend/api/routes/auth.py

Authentication-related API endpoints.
"""

import time

from flask import Blueprint, Response, jsonify, make_response, request
from pydantic import ValidationError

import backend.core.user_manager as um
import backend.storage.json_handler as jh
from backend.utils.session import SessionManager

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
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
    first_name = request.json.get("firstName")
    last_name = request.json.get("lastName")
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
            password,  # Already hashed, look at user_manager.py
            first_name,
            last_name,
            city,
            country,
            users,
        )

        time.sleep(0.5)

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


@auth_bp.route("/login", methods=["POST"])
def login() -> Response:
    username = request.json.get("username") if request.json else None
    password = request.json.get("password") if request.json else None

    try:
        if username and password:
            um.authenticate_user(username, password)

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


@auth_bp.route("/logout", methods=["POST"])
def logout() -> Response:
    username = request.json.get("username") if request.json else None

    if username:
        try:
            session_manager = SessionManager(username)
            session_manager.destroy_session()
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


@auth_bp.route("/profile", methods=["GET"])
def get_profile() -> Response:
    username = request.args.get("username", type=str)

    try:
        if username:
            user = um.get_user_by_username(username)
            resp = jsonify({"status": "success", "user": user})
            return make_response(resp, 200)
        else:
            resp = jsonify({"status": "error", "message": "Username was not given."})
            return make_response(resp, 400)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
    except Exception as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 500)


@auth_bp.route("/profile", methods=["POST"])
def update_profile() -> Response:
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
            resp = jsonify({"status": "error", "message": str(e)})
            return make_response(resp, 500)
    else:
        resp = jsonify(
            {"status": "error", "message": "Username/field/value were not provided."}
        )
        return make_response(resp, 400)


@auth_bp.route("/delete", methods=["POST"])
def delete_profile() -> Response:
    """
    RESTful API endpoint to remove user.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.args.get("username", type=str)

    if not username:
        resp = jsonify({"status": "error", "message": "No username given."})
        return make_response(resp, 400)

    try:
        um.remove_user(username)
        resp = jsonify({"status": "success"})
        return make_response(resp, 200)
    except ValueError as e:
        resp = jsonify({"status": "error", "message": str(e)})
        return make_response(resp, 404)
