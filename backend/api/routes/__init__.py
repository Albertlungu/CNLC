"""
./backend/api/routes/__init__.py

Route blueprints for the Flask application.
"""

from backend.api.routes.agent import agent_bp
from backend.api.routes.auth import auth_bp
from backend.api.routes.blogs import blogs_bp
from backend.api.routes.bookmarks import bookmarks_bp
from backend.api.routes.businesses import businesses_bp
from backend.api.routes.calendar import calendar_bp
from backend.api.routes.deals import deals_bp
from backend.api.routes.friends import friends_bp
from backend.api.routes.media import media_bp
from backend.api.routes.notifications import notifications_bp
from backend.api.routes.recommendations import recommendations_bp
from backend.api.routes.reservations import reservations_bp
from backend.api.routes.reviews import reviews_bp
from backend.api.routes.saved import saved_bp
from backend.api.routes.scans import scans_bp
from backend.api.routes.sessions import sessions_bp
from backend.api.routes.trending import trending_bp
from backend.api.routes.users import users_bp
from backend.api.routes.verification import verification_bp

__all__ = [
    "agent_bp",
    "auth_bp",
    "blogs_bp",
    "bookmarks_bp",
    "businesses_bp",
    "calendar_bp",
    "deals_bp",
    "friends_bp",
    "media_bp",
    "notifications_bp",
    "reservations_bp",
    "reviews_bp",
    "saved_bp",
    "scans_bp",
    "sessions_bp",
    "trending_bp",
    "users_bp",
    "recommendations_bp",
    "verification_bp",
]
