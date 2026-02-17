"""
./backend/api/routes/calendar.py

Google Calendar integration API endpoints.
Server-side OAuth flow with refresh token storage.
"""

from flask import Blueprint, Response, jsonify, make_response, redirect, request

from backend.core import calendar_manager
from backend.core.reservation_manager import get_user_reservations

calendar_bp = Blueprint("calendar", __name__, url_prefix="/api/calendar")


@calendar_bp.route("/auth-url", methods=["GET"])
def get_auth_url() -> Response:
    """Generate Google OAuth authorization URL for a user."""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "user_id required."}), 400
        )

    if not calendar_manager.GOOGLE_CLIENT_ID:
        return make_response(
            jsonify(
                {
                    "status": "error",
                    "message": "Google Calendar not configured. Set GOOGLE_CALENDAR_CLIENT_ID environment variable.",
                }
            ),
            500,
        )

    try:
        auth_url = calendar_manager.start_oauth_flow(user_id)
        return jsonify({"status": "success", "authUrl": auth_url})
    except Exception as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 500)


@calendar_bp.route("/callback", methods=["GET"])
def oauth_callback() -> Response:
    """Handle Google OAuth callback. Exchanges code for tokens and redirects to calendar page."""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        return redirect("/calendar.html?error=auth_denied")

    if not code or not state:
        return redirect("/calendar.html?error=missing_params")

    try:
        calendar_manager.handle_oauth_callback(code, state)
        return redirect("/calendar.html?connected=true")
    except ValueError as e:
        return redirect(f"/calendar.html?error={str(e)}")
    except Exception:
        return redirect("/calendar.html?error=server_error")


@calendar_bp.route("/events", methods=["GET"])
def get_events() -> Response:
    """Get merged Google Calendar events + CNLC reservations for a month."""
    user_id = request.args.get("user_id", type=int)
    month = request.args.get("month")  # Format: YYYY-MM

    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "user_id required."}), 400
        )

    events = []

    # Fetch Google Calendar events if connected
    try:
        if month:
            parts = month.split("-")
            year = int(parts[0])
            m = int(parts[1])
            from datetime import datetime

            time_min = datetime(year, m, 1).isoformat() + "Z"
            if m == 12:
                time_max = datetime(year + 1, 1, 1).isoformat() + "Z"
            else:
                time_max = datetime(year, m + 1, 1).isoformat() + "Z"
        else:
            from datetime import datetime, timedelta

            now = datetime.utcnow()
            time_min = datetime(now.year, now.month, 1).isoformat() + "Z"
            if now.month == 12:
                time_max = datetime(now.year + 1, 1, 1).isoformat() + "Z"
            else:
                time_max = datetime(now.year, now.month + 1, 1).isoformat() + "Z"

        google_events = calendar_manager.get_events(user_id, time_min, time_max)
        events.extend(google_events)
    except ValueError:
        # Not connected or token issues - continue with just reservations
        pass
    except Exception:
        pass

    # Fetch CNLC reservations
    try:
        reservations = get_user_reservations(user_id)
        for r in reservations:
            events.append(
                {
                    "id": r.get("reservationId"),
                    "title": f"{r.get('businessName', 'Reservation')} - {r.get('partySize', '?')} guests",
                    "start": f"{r.get('date')}T{r.get('time')}",
                    "end": None,
                    "allDay": False,
                    "source": "cnlc",
                    "status": r.get("status"),
                    "reservationData": r,
                }
            )
    except Exception:
        pass

    return jsonify({"status": "success", "events": events, "count": len(events)})


@calendar_bp.route("/events", methods=["POST"])
def create_event() -> Response:
    """Create a new Google Calendar event."""
    data = request.json or {}
    user_id = data.get("userId")

    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "userId required."}), 400
        )

    required = ["title", "date", "startTime", "endTime"]
    for field in required:
        if not data.get(field):
            return make_response(
                jsonify({"status": "error", "message": f"{field} required."}), 400
            )

    try:
        event = calendar_manager.create_event(user_id, data)
        return make_response(jsonify({"status": "success", "event": event}), 201)
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 500)


@calendar_bp.route("/events/<event_id>", methods=["PUT"])
def update_event(event_id: str) -> Response:
    """Update a Google Calendar event."""
    data = request.json or {}
    user_id = data.get("userId")

    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "userId required."}), 400
        )

    try:
        event = calendar_manager.update_event(user_id, event_id, data)
        return jsonify({"status": "success", "event": event})
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 400)


@calendar_bp.route("/events/<event_id>", methods=["DELETE"])
def delete_event(event_id: str) -> Response:
    """Delete a Google Calendar event."""
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "user_id required."}), 400
        )

    try:
        calendar_manager.delete_event(user_id, event_id)
        return jsonify({"status": "success"})
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 400)


@calendar_bp.route("/status", methods=["GET"])
def get_status() -> Response:
    """Check if user has Google Calendar connected."""
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "user_id required."}), 400
        )

    status = calendar_manager.get_connection_status(user_id)
    return jsonify({"status": "success", **status})


@calendar_bp.route("/disconnect", methods=["POST"])
def disconnect() -> Response:
    """Disconnect Google Calendar for a user."""
    data = request.json or {}
    user_id = data.get("userId")

    if not user_id:
        return make_response(
            jsonify({"status": "error", "message": "userId required."}), 400
        )

    calendar_manager.disconnect(user_id)
    return jsonify({"status": "success"})
