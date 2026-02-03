"""
./backend/api/routes/notifications.py

Notification-related API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request

import backend.core.notification_manager as nm

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.route("/", methods=["GET"])
def get_notifications() -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    unread_only = request.args.get("unread_only", "false").lower() == "true"
    notifications = nm.get_user_notifications(user_id, unread_only=unread_only)
    return make_response(jsonify({"status": "success", "notifications": notifications}), 200)


@notifications_bp.route("/<int:notification_id>/read", methods=["PUT"])
def mark_read(notification_id: int) -> Response:
    result = nm.mark_as_read(notification_id)
    if result["status"] == "error":
        return make_response(jsonify(result), 404)
    return make_response(jsonify(result), 200)


@notifications_bp.route("/read-all", methods=["PUT"])
def mark_all_read() -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    result = nm.mark_all_read(user_id)
    return make_response(jsonify(result), 200)
