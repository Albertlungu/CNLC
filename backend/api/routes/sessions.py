"""
./backend/api/routes/sessions.py

Session management API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request

import backend.storage.json_handler as jh
from backend.utils.session import SessionManager

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/session")


@sessions_bp.route("/create", methods=["POST"])
def create_session() -> Response:
    username = request.args.get("username", type=str)

    if username:
        try:
            session_manager = SessionManager(username)
            session_info = session_manager.create_session()
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
