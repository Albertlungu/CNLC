"""
./backend/core/review_manager.py

CRUD operations for reviews
"""

import os
import sys
from typing import Any, Optional, Union

from pydantic import ValidationError

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import backend.storage.json_handler as jh
from backend.models.review import Review
