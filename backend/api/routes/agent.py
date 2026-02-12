"""
./backend/api/routes/agent.py

Chat endpoint for the AI agent. Rate-limited, auth-required, input-validated.
"""

import re
import uuid

from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.core import agent_manager
from backend.storage.json_handler import load_sessions

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")

limiter = Limiter(key_func=get_remote_address)

_STRIP_HTML = re.compile(r"<[^>]+>")
_MAX_MESSAGE_LEN = 2000


def _validate_session(user_id: int) -> bool:
    """Check that the userId belongs to an active session."""
    sessions = load_sessions()
    for s in sessions:
        if s.get("userId") == user_id:
            return True
    return False


@agent_bp.route("/chat", methods=["POST"])
@limiter.limit("10/minute", key_func=lambda: str(request.get_json(silent=True, force=True).get("userId", get_remote_address())))
@limiter.limit("100/minute")
def chat():
    """
    POST /api/agent/chat
    Body: { userId: int, message: str, sessionId?: str }
    Returns: { status, message, cards, navigation }
    """
    data = request.get_json(silent=True, force=True)
    if not data:
        return jsonify({"status": "error", "error": "Invalid JSON body"}), 400

    user_id = data.get("userId")
    message = data.get("message", "")
    session_id = data.get("sessionId")

    # --- Validate userId ---
    if not isinstance(user_id, int):
        return jsonify({"status": "error", "error": "userId must be an integer"}), 400

    if not _validate_session(user_id):
        return jsonify({"status": "error", "error": "Unauthorized. Please log in."}), 401

    # --- Sanitize message ---
    message = str(message).strip()
    message = _STRIP_HTML.sub("", message)
    message = message[:_MAX_MESSAGE_LEN]

    if not message:
        return jsonify({"status": "error", "error": "Message cannot be empty"}), 400

    # --- Generate or validate sessionId ---
    if not session_id or not isinstance(session_id, str):
        session_id = str(uuid.uuid4())

    # Sanitize sessionId (alphanumeric + hyphens only)
    session_id = re.sub(r"[^a-zA-Z0-9\-]", "", session_id)[:64]

    # --- Call agent ---
    try:
        result = agent_manager.chat(user_id, session_id, message)
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "An unexpected error occurred. Please try again.",
        }), 500

    return jsonify({
        "status": "success",
        "sessionId": session_id,
        "message": result.get("message", ""),
        "cards": result.get("cards", []),
        "navigation": result.get("navigation", []),
    }), 200


@agent_bp.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({
        "status": "error",
        "error": "Rate limit exceeded. Please wait before sending another message.",
        "retryAfter": 60,
    }), 429
