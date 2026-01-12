"""
./backend/core/review_manager.py

CRUD operations for reviews
"""

from typing import Any, Optional, Union

from pydantic import ValidationError

import backend.storage.json_handler as jh
from backend.models.review import Review
