"""
./backend/utils/session.py

This module provides utility functions for managing user sessions.
"""

import datetime
import os
import secrets
import sys
from multiprocessing import Value

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.storage.json_handler as jh


class SessionManager:
    def __init__(self, username: str, users: list[dict] = jh.load_users()) -> None:
        """
        Initializes a session manager for a specific user.

        Args:
            username (str): Unique username.
            users (list[dict], optional): Contains all users. Defaults to jh.load_users().

        Raises:
            ValueError: If the username does not exist.
        """
        self.username = username

        self.loaded_user = None
        for user in users:
            if user["username"] == username:
                self.loaded_user = user
                break

        if self.loaded_user is None:
            raise ValueError(f"ERROR: Username '{username}' does not exist.")

    def validate_session(self, session_info: dict) -> bool:
        """
        Validates if a session is active and not expired.

        Args:
            session_info (dict): Session data containing is_active and expiration fields.

        Raises:
            ValueError: If session info is missing, session is inactive, or session has expired.

        Returns:
            bool: True if session is valid.
        """
        if not session_info:
            raise ValueError("ERROR: Session info is missing.")
        if not session_info.get("is_active"):
            raise ValueError("ERROR: Session is not active.")
        if datetime.datetime.now() > datetime.datetime.fromisoformat(
            session_info["expiration"]
        ):
            raise ValueError("ERROR: Session has expired.")
        return True

    def create_session(self) -> dict:
        """
        Creates a new session for the user with a 7-day expiration.

        Returns:
            dict: Session information including session_id, timestamps, and active status.
        """
        session_id = secrets.token_urlsafe(32)
        created_at = datetime.datetime.now()
        expiration = datetime.datetime.now() + datetime.timedelta(days=7)
        is_active = True

        session_info = {
            "username": self.username,
            "session_id": session_id,
            "created_at": created_at.isoformat(),
            "expiration": expiration.isoformat(),
            "is_active": is_active,
        }

        if not self.validate_session(session_info):
            raise ValueError("ERROR: Invalid session information.")

        return session_info

    def destroy_session(self) -> None:
        """
        Deactivates a session and marks it as expired immediately.

        Raises:
            ValueError: If the session is not found for this user.
        """
        sessions = jh.load_sessions()

        target_index = None
        session_id = None
        for i, session in enumerate(sessions):
            if session.get("username") == self.username:
                target_index = i
                session_id = session.get("session_id")
                break

        if target_index is None or session_id is None:
            raise ValueError("ERROR: Session not found.")

        sessions[target_index]["is_active"] = False
        sessions[target_index]["expiration"] = datetime.datetime.now().isoformat()

        jh.delete_session(session_id)
        jh.save_session(sessions[target_index], io_type="a")

    @staticmethod
    def cleanup_expired_sessions(days_to_keep: int = 5) -> int:
        """
        Removes inactive sessions older than the specified number of days.

        Args:
            days_to_keep (int): Number of days to keep inactive sessions. Defaults to 5.

        Returns:
            int: Number of sessions cleaned up.
        """
        sessions = jh.load_sessions()
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)

        sessions_to_keep = []
        cleanup_count = 0

        for session in sessions:
            created_at = datetime.datetime.fromisoformat(session["created_at"])
            is_active = session.get("is_active", True)

            if is_active or created_at >= cutoff_date:
                sessions_to_keep.append(session)
            else:
                cleanup_count += 1

        if cleanup_count > 0:
            with open(
                jh.Path(__file__).parent.parent.parent / "data" / "sessions.json", "w"
            ) as f:
                jh.json.dump(sessions_to_keep, f, indent=1)

        return cleanup_count
