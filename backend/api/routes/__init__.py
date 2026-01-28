"""
./backend/api/routes/__init__.py

Route blueprints for the Flask application.
"""

from backend.api.routes.auth import auth_bp
from backend.api.routes.bookmarks import bookmarks_bp
from backend.api.routes.businesses import businesses_bp
from backend.api.routes.reviews import reviews_bp
from backend.api.routes.saved import saved_bp
from backend.api.routes.sessions import sessions_bp
from backend.api.routes.users import users_bp
from backend.api.routes.verification import verification_bp

__all__ = [
    "auth_bp",
    "bookmarks_bp",
    "businesses_bp",
    "reviews_bp",
    "saved_bp",
    "sessions_bp",
    "users_bp",
    "verification_bp",
]
