"""
./backend/utils/session.py

This module provides utility functions for managing user sessions.
"""

import datetime
import os
import secrets
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.storage.json_handler as jh


class SessionManager:
    def __init__(self, username: str, users: list[dict] = jh.load_users()) -> None:
        self.username = username

        self.loaded_user = None
        for user in users:
            if user["username"] == username:
                self.loaded_user = user
                break

        if self.loaded_user is None:
            raise ValueError(f"ERROR: Username '{username}' does not exist.")

    def create_session(self) -> dict:
        session_id = secrets.token_urlsafe(32)
        created_at = datetime.datetime.now()
        expiration = datetime.datetime.now() + datetime.timedelta(hours=2)
        is_active = True

        session_info = {
            "username": self.username,
            "session_id": session_id,
            "created_at": created_at.isoformat(),
            "expiration": expiration.isoformat(),
            "is_active": is_active,
        }

        return session_info

    def validate_session(self, session_info: dict) -> bool:
        if not session_info:
            raise ValueError("ERROR: Session info is missing.")
        if not session_info.get("is_active"):
            raise ValueError("ERROR: Session is not active.")
        if datetime.datetime.now() > datetime.datetime.fromisoformat(
            session_info["expiration"]
        ):
            raise ValueError("ERROR: Session has expired.")
        return True

    def destroy_session(self, session_id: str) -> None:
        sessions = jh.load_sessions()

        target_index = None
        for i, session in enumerate(sessions):
            if (
                session.get("session_id") == session_id
                and session.get("username") == self.username
            ):
                target_index = i
                break

        if target_index is None:
            raise ValueError("ERROR: Session not found.")

        sessions[target_index]["is_active"] = False
        sessions[target_index]["expiration"] = datetime.datetime.now().isoformat()

        jh.delete_session(session_id)
        jh.save_session(sessions[target_index], io_type="a")
