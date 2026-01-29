"""
./backend/api/routes/friends.py

API routes for friend relationships and social features.
"""

from flask import Blueprint, jsonify, request

from backend.core import friend_manager as fm
from backend.core import user_manager as um

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


@friends_bp.route("/request", methods=["POST"])
def send_request():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    from_user_id = data.get("fromUserId")
    to_user_id = data.get("toUserId")

    if not from_user_id or not to_user_id:
        return jsonify({"status": "error", "message": "fromUserId and toUserId are required"}), 400

    result = fm.send_friend_request(from_user_id, to_user_id)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result), 201


@friends_bp.route("/requests", methods=["GET"])
def get_requests():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    pending = fm.get_pending_requests(user_id)
    sent = fm.get_sent_requests(user_id)

    # Enrich with usernames
    for r in pending:
        user = um.get_user_by_id(r["fromUserId"])
        r["fromUsername"] = user.get("username", "Unknown") if user else "Unknown"

    for r in sent:
        user = um.get_user_by_id(r["toUserId"])
        r["toUsername"] = user.get("username", "Unknown") if user else "Unknown"

    return jsonify({"status": "success", "pending": pending, "sent": sent})


@friends_bp.route("/requests/<int:request_id>/accept", methods=["PUT"])
def accept_request(request_id):
    data = request.get_json()
    if not data or not data.get("userId"):
        return jsonify({"status": "error", "message": "userId is required"}), 400

    result = fm.accept_request(request_id, data["userId"])
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)


@friends_bp.route("/requests/<int:request_id>/reject", methods=["PUT"])
def reject_request(request_id):
    data = request.get_json()
    if not data or not data.get("userId"):
        return jsonify({"status": "error", "message": "userId is required"}), 400

    result = fm.reject_request(request_id, data["userId"])
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)


@friends_bp.route("", methods=["GET"])
def get_friends():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    friends = fm.get_friends(user_id)

    # Enrich with usernames
    for f in friends:
        user = um.get_user_by_id(f["friendUserId"])
        f["friendUsername"] = user.get("username", "Unknown") if user else "Unknown"

    return jsonify({"status": "success", "friends": friends})


@friends_bp.route("/<int:friendship_id>", methods=["DELETE"])
def remove_friend(friendship_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    result = fm.remove_friend(friendship_id, user_id)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)


@friends_bp.route("/activity", methods=["GET"])
def get_activity():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    activity = fm.get_friend_activity(user_id)
    return jsonify({"status": "success", "activity": activity})


@friends_bp.route("/search", methods=["GET"])
def search_users():
    query = request.args.get("q", "")
    user_id = request.args.get("user_id", type=int)

    if not query or len(query) < 2:
        return jsonify({"status": "error", "message": "Query must be at least 2 characters"}), 400

    users = um.search_users(query)

    # Filter out the requesting user
    if user_id:
        users = [u for u in users if u.get("id") != user_id]

    # Return only safe fields
    safe_users = [{"id": u["id"], "username": u["username"]} for u in users]
    return jsonify({"status": "success", "users": safe_users})
