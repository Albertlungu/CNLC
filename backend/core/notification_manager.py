"""
./backend/core/notification_manager.py

Manages in-app notifications.
"""

import json
import random
from datetime import datetime
from typing import Optional

from config.config import NOTIFICATIONS_JSON


def _load_notifications() -> list[dict]:
    try:
        with open(str(NOTIFICATIONS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_notifications(notifications: list[dict]) -> None:
    with open(str(NOTIFICATIONS_JSON), "w") as f:
        json.dump(notifications, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def create_notification(
    user_id: int,
    notif_type: str,
    title: str,
    message: str,
    related_id: Optional[int] = None,
) -> dict:
    notifications = _load_notifications()

    notif = {
        "notificationId": _generate_id(),
        "userId": user_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "relatedId": related_id,
        "read": False,
        "createdAt": datetime.utcnow().isoformat(),
    }

    notifications.append(notif)
    _save_notifications(notifications)
    return notif


def get_user_notifications(user_id: int, unread_only: bool = False) -> list[dict]:
    notifications = _load_notifications()
    result = [n for n in notifications if n["userId"] == user_id]
    if unread_only:
        result = [n for n in result if not n.get("read", False)]
    result.sort(key=lambda n: n["createdAt"], reverse=True)
    return result


def mark_as_read(notification_id: int) -> dict:
    notifications = _load_notifications()
    for n in notifications:
        if n["notificationId"] == notification_id:
            n["read"] = True
            _save_notifications(notifications)
            return {"status": "success"}
    return {"status": "error", "message": "Notification not found"}


def mark_all_read(user_id: int) -> dict:
    notifications = _load_notifications()
    changed = False
    for n in notifications:
        if n["userId"] == user_id and not n.get("read", False):
            n["read"] = True
            changed = True
    if changed:
        _save_notifications(notifications)
    return {"status": "success"}
