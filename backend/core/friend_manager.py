"""
./backend/core/friend_manager.py

Manages friend relationships and social features.
"""

import json
import random
from datetime import datetime
from typing import Optional

from config.config import FRIENDS_JSON, FRIEND_REQUESTS_JSON, REVIEWS_JSON


def _load_friends() -> list[dict]:
    try:
        with open(str(FRIENDS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_friends(friends: list[dict]) -> None:
    with open(str(FRIENDS_JSON), "w") as f:
        json.dump(friends, f, indent=4)


def _load_requests() -> list[dict]:
    try:
        with open(str(FRIEND_REQUESTS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_requests(requests: list[dict]) -> None:
    with open(str(FRIEND_REQUESTS_JSON), "w") as f:
        json.dump(requests, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def send_friend_request(from_user_id: int, to_user_id: int) -> dict:
    if from_user_id == to_user_id:
        return {"status": "error", "message": "Cannot send request to yourself"}

    # Check if already friends
    friends = _load_friends()
    for f in friends:
        if (f["user1Id"] == from_user_id and f["user2Id"] == to_user_id) or \
           (f["user1Id"] == to_user_id and f["user2Id"] == from_user_id):
            return {"status": "error", "message": "Already friends"}

    # Check for existing pending request
    requests = _load_requests()
    for r in requests:
        if r["status"] == "pending":
            if r["fromUserId"] == from_user_id and r["toUserId"] == to_user_id:
                return {"status": "error", "message": "Request already sent"}
            if r["fromUserId"] == to_user_id and r["toUserId"] == from_user_id:
                return {"status": "error", "message": "This user already sent you a request"}

    request = {
        "requestId": _generate_id(),
        "fromUserId": from_user_id,
        "toUserId": to_user_id,
        "status": "pending",
        "createdAt": datetime.utcnow().isoformat(),
    }

    requests.append(request)
    _save_requests(requests)
    return {"status": "success", "request": request}


def accept_request(request_id: int, user_id: int) -> dict:
    requests = _load_requests()

    for r in requests:
        if r["requestId"] == request_id:
            if r["toUserId"] != user_id:
                return {"status": "error", "message": "Not authorized"}
            if r["status"] != "pending":
                return {"status": "error", "message": "Request already processed"}

            r["status"] = "accepted"
            _save_requests(requests)

            # Create friendship
            friends = _load_friends()
            friendship = {
                "friendshipId": _generate_id(),
                "user1Id": r["fromUserId"],
                "user2Id": r["toUserId"],
                "since": datetime.utcnow().isoformat(),
            }
            friends.append(friendship)
            _save_friends(friends)

            return {"status": "success", "friendship": friendship}

    return {"status": "error", "message": "Request not found"}


def reject_request(request_id: int, user_id: int) -> dict:
    requests = _load_requests()

    for r in requests:
        if r["requestId"] == request_id:
            if r["toUserId"] != user_id:
                return {"status": "error", "message": "Not authorized"}
            if r["status"] != "pending":
                return {"status": "error", "message": "Request already processed"}

            r["status"] = "rejected"
            _save_requests(requests)
            return {"status": "success"}

    return {"status": "error", "message": "Request not found"}


def get_pending_requests(user_id: int) -> list[dict]:
    requests = _load_requests()
    return [r for r in requests if r["toUserId"] == user_id and r["status"] == "pending"]


def get_sent_requests(user_id: int) -> list[dict]:
    requests = _load_requests()
    return [r for r in requests if r["fromUserId"] == user_id and r["status"] == "pending"]


def get_friends(user_id: int) -> list[dict]:
    friends = _load_friends()
    result = []
    for f in friends:
        if f["user1Id"] == user_id:
            result.append({"friendshipId": f["friendshipId"], "friendUserId": f["user2Id"], "since": f["since"]})
        elif f["user2Id"] == user_id:
            result.append({"friendshipId": f["friendshipId"], "friendUserId": f["user1Id"], "since": f["since"]})
    return result


def remove_friend(friendship_id: int, user_id: int) -> dict:
    friends = _load_friends()
    for i, f in enumerate(friends):
        if f["friendshipId"] == friendship_id:
            if f["user1Id"] != user_id and f["user2Id"] != user_id:
                return {"status": "error", "message": "Not authorized"}
            friends.pop(i)
            _save_friends(friends)
            return {"status": "success"}
    return {"status": "error", "message": "Friendship not found"}


def get_friend_activity(user_id: int, limit: int = 20) -> list[dict]:
    """Get recent reviews from friends."""
    friend_list = get_friends(user_id)
    friend_ids = [f["friendUserId"] for f in friend_list]

    if not friend_ids:
        return []

    try:
        with open(str(REVIEWS_JSON), "r") as f:
            reviews = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    friend_reviews = [r for r in reviews if r.get("userId") in friend_ids]
    friend_reviews.sort(key=lambda r: r.get("createdAt", ""), reverse=True)

    return friend_reviews[:limit]
