"""
./backend/api/routes/recommendations.py

AI recommendation API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request

import backend.core.ai_manager as ai

recommendations_bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


@recommendations_bp.route("/", methods=["GET"])
def get_recommendations() -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    search_history_str = request.args.get("search_history", "")
    search_history = search_history_str.split(",") if search_history_str else []

    result = ai.get_recommendations(user_id, search_history)
    status_code = 200 if result.get("status") == "success" else 500
    return make_response(jsonify(result), status_code)
