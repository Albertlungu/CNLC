"""
./backend/api/routes/bookmarks.py

Bookmark-related API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request

import backend.core.bookmark_manager as book

bookmarks_bp = Blueprint("bookmarks", __name__, url_prefix="/api/bookmarks")


@bookmarks_bp.route("/add", methods=["POST"])
def add_bookmarks() -> Response:
    """
    RESTful API endpoint to add bookmarks to a user's account.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.args.get("username", type=str)
    bookmarks = request.args.get("bookmarks", type=str)

    try:
        if username and bookmarks:
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


@bookmarks_bp.route("/remove", methods=["POST"])
def remove_bookmarks_route() -> Response:
    """
    RESTful API endpoint to remove bookmarks from a user's account.

    Returns:
        Response: Status, being error or success, giving a message upon error.
    """
    username = request.args.get("username", type=str)
    bookmarks = request.args.get("bookmarks", type=str)

    try:
        if username and bookmarks:
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


@bookmarks_bp.route("/get", methods=["GET"])
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


@bookmarks_bp.route("/businesses", methods=["GET"])
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
