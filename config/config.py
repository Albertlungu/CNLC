"""
./config/config.py

Central configuration file for all paths and settings.
"""

from pathlib import Path

# Get project root (one level up from config directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Data directory
DATA_DIR = PROJECT_ROOT / "data"

# All data file paths
BUSINESSES_JSON = DATA_DIR / "businesses.json"
USERS_JSON = DATA_DIR / "users.json"
REVIEWS_JSON = DATA_DIR / "reviews.json"
SESSIONS_JSON = DATA_DIR / "sessions.json"
BOOKMARKS_JSON = DATA_DIR / "bookmarks.json"  # If you add this later
DEALS_JSON = DATA_DIR / "deals.json"
FRIENDS_JSON = DATA_DIR / "friends.json"
FRIEND_REQUESTS_JSON = DATA_DIR / "friend_requests.json"
RECEIPTS_JSON = DATA_DIR / "receipts.json"
TRENDING_POINTS_JSON = DATA_DIR / "trending_points.json"
COLLECTIONS_JSON = DATA_DIR / "collections.json"
SAVED_BUSINESSES_JSON = DATA_DIR / "saved_businesses.json"

# Backend directories
BACKEND_DIR = PROJECT_ROOT / "backend"
MODELS_DIR = BACKEND_DIR / "models"
CORE_DIR = BACKEND_DIR / "core"
API_DIR = BACKEND_DIR / "api"
UTILS_DIR = BACKEND_DIR / "utils"
STORAGE_DIR = BACKEND_DIR / "storage"

# Frontend directories
FRONTEND_DIR = PROJECT_ROOT / "frontend"
FRONTEND_SRC_DIR = FRONTEND_DIR / "src"

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5000
DEBUG_MODE = True

# API Configuration
API_PREFIX = "/api"
CORS_ORIGINS = "*"  # Change to specific origins in production

# Session configuration
SESSION_EXPIRY_DAYS = 7

# Review configuration
MAX_REVIEW_LENGTH = 1000
MIN_RATING = 1
MAX_RATING = 5


# Helper function to convert Path to string (for compatibility)
def get_path(path: Path) -> str:
    """Convert Path object to string for compatibility with older code."""
    return str(path)
