"""
./backend/api/routes/reservations.py

Reservation-related API endpoints.
"""

from flask import Blueprint, Response, jsonify, make_response, request

import backend.core.reservation_manager as rm
import backend.core.notification_manager as nm

reservations_bp = Blueprint("reservations", __name__, url_prefix="/api/reservations")


@reservations_bp.route("/", methods=["POST"])
def create_reservation() -> Response:
    if not request.json:
        return make_response(jsonify({"status": "error", "message": "No data provided."}), 400)

    user_id = request.json.get("userId")
    business_id = request.json.get("businessId")
    business_name = request.json.get("businessName", "")
    date = request.json.get("date")
    time_str = request.json.get("time")
    party_size = request.json.get("partySize")
    notes = request.json.get("notes")

    if not all([user_id, business_id, date, time_str, party_size]):
        return make_response(jsonify({"status": "error", "message": "Missing required fields."}), 400)

    try:
        reservation = rm.create_reservation(
            user_id=user_id,
            business_id=business_id,
            business_name=business_name,
            date=date,
            time=time_str,
            party_size=party_size,
            notes=notes,
        )

        nm.create_notification(
            user_id=user_id,
            notif_type="reservation_confirmed",
            title="Reservation Confirmed",
            message=f"Your reservation at {business_name} on {date} at {time_str} for {party_size} has been confirmed.",
            related_id=reservation["reservationId"],
        )

        return make_response(jsonify({"status": "success", "reservation": reservation}), 201)
    except Exception as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 500)


@reservations_bp.route("/", methods=["GET"])
def get_reservations() -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    status_filter = request.args.get("status")
    reservations = rm.get_user_reservations(user_id)
    if status_filter:
        reservations = [r for r in reservations if r.get("status") == status_filter]

    reservations.sort(key=lambda r: (r["date"], r["time"]))
    return make_response(jsonify({"status": "success", "reservations": reservations}), 200)


@reservations_bp.route("/<int:reservation_id>/cancel", methods=["PUT"])
def cancel_reservation(reservation_id: int) -> Response:
    user_id = request.json.get("userId") if request.json else None
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "userId required."}), 400)

    try:
        result = rm.cancel_reservation(reservation_id, user_id)
        if isinstance(result, dict) and result.get("status") == "error":
            return make_response(jsonify(result), 404)

        reservation = result if not isinstance(result, dict) or "reservation" not in result else result["reservation"]

        nm.create_notification(
            user_id=user_id,
            notif_type="reservation_cancelled",
            title="Reservation Cancelled",
            message=f"Your reservation has been cancelled.",
            related_id=reservation_id,
        )

        return make_response(jsonify({"status": "success", "reservation": reservation}), 200)
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 404)
    except Exception as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 500)


@reservations_bp.route("/<int:reservation_id>/ics", methods=["GET"])
def download_ics(reservation_id: int) -> Response:
    reservation = rm.get_reservation_by_id(reservation_id)
    if not reservation:
        return make_response(jsonify({"status": "error", "message": "Reservation not found."}), 404)

    ics_content = rm.generate_ics(reservation)
    response = make_response(ics_content)
    response.headers["Content-Type"] = "text/calendar; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=reservation-{reservation_id}.ics"
    return response


@reservations_bp.route("/reminders/check", methods=["GET"])
def check_reminders() -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    due_reservations = rm.check_reminders(user_id)

    for r in due_reservations:
        nm.create_notification(
            user_id=user_id,
            notif_type="reservation_reminder",
            title="Upcoming Reservation",
            message=f"Reminder: You have a reservation at {r.get('businessName', 'a business')} on {r['date']} at {r['time']}.",
            related_id=r["reservationId"],
        )

    return make_response(jsonify({"status": "success", "reminders": len(due_reservations)}), 200)
