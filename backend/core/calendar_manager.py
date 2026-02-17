"""
./backend/core/calendar_manager.py

Manages Google Calendar integration with server-side OAuth.
Stores refresh tokens per-user for persistent calendar access.
"""

import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from config.config import DATA_DIR

CALENDAR_TOKENS_JSON = DATA_DIR / "calendar_tokens.json"
OAUTH_STATES_JSON = DATA_DIR / "calendar_oauth_states.json"

# Google OAuth configuration - set via environment variables
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_CALENDAR_REDIRECT_URI", "http://127.0.0.1:5001/api/calendar/callback"
)
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _load_tokens() -> list[dict]:
    try:
        with open(str(CALENDAR_TOKENS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_tokens(tokens: list[dict]) -> None:
    with open(str(CALENDAR_TOKENS_JSON), "w") as f:
        json.dump(tokens, f, indent=4)


def _load_states() -> list[dict]:
    try:
        with open(str(OAUTH_STATES_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_states(states: list[dict]) -> None:
    with open(str(OAUTH_STATES_JSON), "w") as f:
        json.dump(states, f, indent=4)


def get_user_token(user_id: int) -> Optional[dict]:
    """Get stored token data for a user."""
    tokens = _load_tokens()
    for t in tokens:
        if t["userId"] == user_id:
            return t
    return None


def save_user_token(
    user_id: int,
    access_token: str,
    refresh_token: str,
    expires_at: str,
    email: str = "",
) -> dict:
    """Save or update token data for a user."""
    tokens = _load_tokens()
    entry = {
        "userId": user_id,
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresAt": expires_at,
        "email": email,
        "connectedAt": datetime.utcnow().isoformat(),
    }

    # Update existing or append new
    for i, t in enumerate(tokens):
        if t["userId"] == user_id:
            tokens[i] = entry
            _save_tokens(tokens)
            return entry

    tokens.append(entry)
    _save_tokens(tokens)
    return entry


def remove_user_token(user_id: int) -> bool:
    """Remove stored token for a user (disconnect)."""
    tokens = _load_tokens()
    for i, t in enumerate(tokens):
        if t["userId"] == user_id:
            tokens.pop(i)
            _save_tokens(tokens)
            return True
    return False


def start_oauth_flow(user_id: int) -> str:
    """
    Generate an OAuth authorization URL for the user.
    Returns the full URL to redirect the user to Google's consent screen.
    """
    import urllib.parse

    state = secrets.token_urlsafe(32)

    # Store state -> user_id mapping
    states = _load_states()
    # Clean old states (older than 10 minutes)
    cutoff = (datetime.utcnow() - timedelta(minutes=10)).isoformat()
    states = [s for s in states if s.get("createdAt", "") > cutoff]
    states.append(
        {
            "state": state,
            "userId": user_id,
            "createdAt": datetime.utcnow().isoformat(),
        }
    )
    _save_states(states)

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    )
    return auth_url


def handle_oauth_callback(code: str, state: str) -> dict:
    """
    Exchange the authorization code for access + refresh tokens.
    Returns the token entry stored for the user.
    """
    import requests as http_requests

    # Validate state
    states = _load_states()
    user_id = None
    for s in states:
        if s["state"] == state:
            user_id = s["userId"]
            break

    if user_id is None:
        raise ValueError("Invalid or expired OAuth state.")

    # Remove used state
    states = [s for s in states if s["state"] != state]
    _save_states(states)

    # Exchange code for tokens
    token_response = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )

    if token_response.status_code != 200:
        raise ValueError(
            f"Failed to exchange code: {token_response.json().get('error_description', 'Unknown error')}"
        )

    token_data = token_response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token", "")
    expires_in = token_data.get("expires_in", 3600)
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

    # Get user email from Google
    email = ""
    try:
        userinfo = http_requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo.status_code == 200:
            email = userinfo.json().get("email", "")
    except Exception:
        pass

    return save_user_token(user_id, access_token, refresh_token, expires_at, email)


def _refresh_access_token(token_entry: dict) -> dict:
    """Refresh an expired access token using the refresh token."""
    import requests as http_requests

    refresh_token = token_entry.get("refreshToken", "")
    if not refresh_token:
        raise ValueError("No refresh token available. User needs to reconnect.")

    response = http_requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )

    if response.status_code != 200:
        # Refresh token may be revoked
        remove_user_token(token_entry["userId"])
        raise ValueError("Refresh token expired. Please reconnect Google Calendar.")

    data = response.json()
    new_access = data["access_token"]
    expires_in = data.get("expires_in", 3600)
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

    return save_user_token(
        token_entry["userId"],
        new_access,
        refresh_token,
        expires_at,
        token_entry.get("email", ""),
    )


def _get_valid_token(user_id: int) -> str:
    """Get a valid access token for the user, refreshing if needed."""
    token_entry = get_user_token(user_id)
    if not token_entry:
        raise ValueError("Google Calendar not connected.")

    # Check if token is expired (with 5 min buffer)
    expires_at = datetime.fromisoformat(token_entry["expiresAt"])
    if datetime.utcnow() >= expires_at - timedelta(minutes=5):
        token_entry = _refresh_access_token(token_entry)

    return token_entry["accessToken"]


def get_events(user_id: int, time_min: str, time_max: str) -> list[dict]:
    """
    Fetch Google Calendar events for a user within a time range.
    time_min and time_max should be ISO format datetime strings.
    """
    import requests as http_requests

    access_token = _get_valid_token(user_id)

    import urllib.parse

    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "250",
    }

    response = http_requests.get(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{urllib.parse.urlencode(params)}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code == 401:
        # Try refreshing
        token_entry = get_user_token(user_id)
        if token_entry:
            token_entry = _refresh_access_token(token_entry)
            response = http_requests.get(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events?{urllib.parse.urlencode(params)}",
                headers={"Authorization": f"Bearer {token_entry['accessToken']}"},
            )

    if response.status_code != 200:
        raise ValueError(f"Failed to fetch events: {response.status_code}")

    data = response.json()
    events = []
    for item in data.get("items", []):
        events.append(
            {
                "id": item.get("id"),
                "title": item.get("summary", "(No title)"),
                "start": item.get("start", {}).get("dateTime")
                or item.get("start", {}).get("date"),
                "end": item.get("end", {}).get("dateTime")
                or item.get("end", {}).get("date"),
                "allDay": not bool(item.get("start", {}).get("dateTime")),
                "description": item.get("description", ""),
                "location": item.get("location", ""),
                "source": "google",
            }
        )

    return events


def create_event(user_id: int, event_data: dict) -> dict:
    """
    Create a new event on the user's Google Calendar.
    event_data should contain: title, date, startTime, endTime, description (optional).
    """
    import requests as http_requests

    access_token = _get_valid_token(user_id)

    # Build event body
    timezone = event_data.get("timezone", "America/Toronto")
    start_dt = f"{event_data['date']}T{event_data['startTime']}:00"
    end_dt = f"{event_data['date']}T{event_data['endTime']}:00"

    event_body = {
        "summary": event_data.get("title", ""),
        "description": event_data.get("description", ""),
        "start": {"dateTime": start_dt, "timeZone": timezone},
        "end": {"dateTime": end_dt, "timeZone": timezone},
    }

    if event_data.get("location"):
        event_body["location"] = event_data["location"]

    response = http_requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=event_body,
    )

    if response.status_code not in (200, 201):
        raise ValueError(f"Failed to create event: {response.status_code}")

    created = response.json()
    return {
        "id": created.get("id"),
        "title": created.get("summary"),
        "start": created.get("start", {}).get("dateTime")
        or created.get("start", {}).get("date"),
        "end": created.get("end", {}).get("dateTime")
        or created.get("end", {}).get("date"),
        "source": "google",
    }


def update_event(user_id: int, event_id: str, event_data: dict) -> dict:
    """Update an existing Google Calendar event."""
    import requests as http_requests

    access_token = _get_valid_token(user_id)

    timezone = event_data.get("timezone", "America/Toronto")
    update_body = {}

    if "title" in event_data:
        update_body["summary"] = event_data["title"]
    if "description" in event_data:
        update_body["description"] = event_data["description"]
    if "date" in event_data and "startTime" in event_data:
        update_body["start"] = {
            "dateTime": f"{event_data['date']}T{event_data['startTime']}:00",
            "timeZone": timezone,
        }
    if "date" in event_data and "endTime" in event_data:
        update_body["end"] = {
            "dateTime": f"{event_data['date']}T{event_data['endTime']}:00",
            "timeZone": timezone,
        }

    response = http_requests.patch(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=update_body,
    )

    if response.status_code != 200:
        raise ValueError(f"Failed to update event: {response.status_code}")

    updated = response.json()
    return {
        "id": updated.get("id"),
        "title": updated.get("summary"),
        "start": updated.get("start", {}).get("dateTime")
        or updated.get("start", {}).get("date"),
        "end": updated.get("end", {}).get("dateTime")
        or updated.get("end", {}).get("date"),
        "source": "google",
    }


def delete_event(user_id: int, event_id: str) -> bool:
    """Delete a Google Calendar event."""
    import requests as http_requests

    access_token = _get_valid_token(user_id)

    response = http_requests.delete(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code not in (200, 204):
        raise ValueError(f"Failed to delete event: {response.status_code}")

    return True


def disconnect(user_id: int) -> bool:
    """Revoke the token and remove stored credentials."""
    import requests as http_requests

    token_entry = get_user_token(user_id)
    if token_entry:
        # Try to revoke the token with Google
        try:
            http_requests.post(
                "https://oauth2.googleapis.com/revoke",
                params={"token": token_entry["accessToken"]},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except Exception:
            pass  # Best effort revocation

    return remove_user_token(user_id)


def get_connection_status(user_id: int) -> dict:
    """Check if user has Google Calendar connected and return status."""
    token_entry = get_user_token(user_id)
    if not token_entry:
        return {"connected": False}

    return {
        "connected": True,
        "email": token_entry.get("email", ""),
        "connectedAt": token_entry.get("connectedAt", ""),
    }
