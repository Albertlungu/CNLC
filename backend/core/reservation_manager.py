"""
./backend/core/reservation_manager.py

Manages reservations for businesses.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Optional

from config.config import RESERVATIONS_JSON


def _load_reservations() -> list[dict]:
    try:
        with open(str(RESERVATIONS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_reservations(reservations: list[dict]) -> None:
    with open(str(RESERVATIONS_JSON), "w") as f:
        json.dump(reservations, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def create_reservation(
    user_id: int,
    business_id: int,
    business_name: str,
    date: str,
    time: str,
    party_size: int,
    notes: Optional[str] = None,
) -> dict:
    reservations = _load_reservations()

    reservation = {
        "reservationId": _generate_id(),
        "userId": user_id,
        "businessId": business_id,
        "businessName": business_name,
        "date": date,
        "time": time,
        "partySize": party_size,
        "status": "confirmed",
        "notes": notes,
        "createdAt": datetime.utcnow().isoformat(),
        "reminderSent": False,
    }

    reservations.append(reservation)
    _save_reservations(reservations)
    return reservation


def get_user_reservations(user_id: int) -> list[dict]:
    reservations = _load_reservations()
    return [r for r in reservations if r["userId"] == user_id]


def get_business_reservations(business_id: int) -> list[dict]:
    reservations = _load_reservations()
    return [r for r in reservations if r["businessId"] == business_id]


def cancel_reservation(reservation_id: int, user_id: int) -> dict:
    reservations = _load_reservations()
    for r in reservations:
        if r["reservationId"] == reservation_id and r["userId"] == user_id:
            r["status"] = "cancelled"
            _save_reservations(reservations)
            return r
    raise ValueError("Reservation not found or not owned by user.")


def get_reservation_by_id(reservation_id: int) -> Optional[dict]:
    reservations = _load_reservations()
    for r in reservations:
        if r["reservationId"] == reservation_id:
            return r
    return None


def get_upcoming_reservations(user_id: int) -> list[dict]:
    reservations = _load_reservations()
    now = datetime.utcnow().isoformat()[:10]
    return [
        r for r in reservations
        if r["userId"] == user_id
        and r["status"] == "confirmed"
        and r["date"] >= now
    ]


def check_reminders(user_id: int) -> list[dict]:
    """Find reservations within 24 hours that haven't had reminders sent."""
    reservations = _load_reservations()
    now = datetime.utcnow()
    tomorrow = now + timedelta(hours=24)
    now_str = now.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    due = []

    for r in reservations:
        if (r["userId"] == user_id
                and r["status"] == "confirmed"
                and not r.get("reminderSent", False)
                and now_str <= r["date"] <= tomorrow_str):
            r["reminderSent"] = True
            due.append(r)

    if due:
        _save_reservations(reservations)

    return due


def generate_ics(reservation: dict) -> str:
    """Generate an ICS calendar file string for a reservation."""
    date_str = reservation["date"].replace("-", "")
    time_str = reservation["time"].replace(":", "")
    dtstart = f"{date_str}T{time_str}00"

    # Assume 1 hour duration
    try:
        start = datetime.strptime(f"{reservation['date']} {reservation['time']}", "%Y-%m-%d %H:%M")
        end = start + timedelta(hours=1)
        dtend = end.strftime("%Y%m%dT%H%M00")
    except ValueError:
        dtend = dtstart

    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//CNLC//Reservation//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"DTSTART:{dtstart}\r\n"
        f"DTEND:{dtend}\r\n"
        f"SUMMARY:Reservation at {reservation.get('businessName', 'Business')}\r\n"
        f"DESCRIPTION:Party size: {reservation.get('partySize', 1)}. {reservation.get('notes', '')}\r\n"
        f"UID:{reservation['reservationId']}@cnlc\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )
