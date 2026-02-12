"""
./backend/api/routes/agent.py

Chat endpoint for the AI agent. Rate-limited, auth-required, input-validated.
"""

import re
import time
import uuid

from flask import Blueprint, jsonify, request

from backend.core import agent_manager
from backend.core.user_manager import get_user_by_id
from backend.storage.json_handler import load_sessions

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")

_STRIP_HTML = re.compile(r"<[^>]+>")
_MAX_MESSAGE_LEN = 2000

# Simple in-memory rate limiter
_rate_limits: dict = {}
_RATE_LIMIT_PER_USER = 10   # max requests per window
_RATE_LIMIT_GLOBAL = 100
_RATE_LIMIT_WINDOW = 60     # seconds
_global_timestamps: list = []


def _check_rate_limit(user_id: int) -> bool:
    """Return True if request is allowed, False if rate-limited."""
    now = time.time()
    cutoff = now - _RATE_LIMIT_WINDOW

    # Global rate limit
    global _global_timestamps
    _global_timestamps = [t for t in _global_timestamps if t > cutoff]
    if len(_global_timestamps) >= _RATE_LIMIT_GLOBAL:
        return False
    _global_timestamps.append(now)

    # Per-user rate limit
    key = str(user_id)
    if key not in _rate_limits:
        _rate_limits[key] = []
    _rate_limits[key] = [t for t in _rate_limits[key] if t > cutoff]
    if len(_rate_limits[key]) >= _RATE_LIMIT_PER_USER:
        return False
    _rate_limits[key].append(now)

    return True


def _validate_session(user_id: int) -> bool:
    """Check that the userId belongs to a user with an active session."""
    user = get_user_by_id(user_id)
    if not user:
        return False
    username = user.get("username")
    if not username:
        return False
    sessions = load_sessions()
    for s in sessions:
        if s.get("username") == username and s.get("is_active"):
            return True
    return False


@agent_bp.route("/chat", methods=["POST"])
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

    # --- Rate limit ---
    if not _check_rate_limit(user_id):
        return jsonify({
            "status": "error",
            "error": "Rate limit exceeded. Please wait before sending another message.",
            "retryAfter": 60,
        }), 429

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
        "businessMap": {str(k): v for k, v in result.get("business_map", {}).items()},
    }), 200
