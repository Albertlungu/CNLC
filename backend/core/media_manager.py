"""
./backend/core/media_manager.py

Manages 3D model and video uploads for businesses.
"""

import json
import os
import random
import uuid
from datetime import datetime
from typing import Optional

from config.config import DATA_DIR, PROJECT_ROOT

MEDIA_JSON = DATA_DIR / "media.json"
MEDIA_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "media"

ALLOWED_3D = {".glb", ".gltf"}
ALLOWED_VIDEO = {".mp4", ".webm"}
ALLOWED_EXTENSIONS = ALLOWED_3D | ALLOWED_VIDEO
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def _ensure_upload_dir():
    os.makedirs(str(MEDIA_UPLOAD_DIR), exist_ok=True)


def _load_media() -> list[dict]:
    try:
        with open(str(MEDIA_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_media(media: list[dict]) -> None:
    with open(str(MEDIA_JSON), "w") as f:
        json.dump(media, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def _get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def save_media(business_id: int, user_id: int, file) -> dict:
    """Save an uploaded media file and record it."""
    _ensure_upload_dir()

    original_name = file.filename or "upload"
    ext = _get_extension(original_name)

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")

    unique_name = f"{uuid.uuid4().hex}{ext}"
    filepath = MEDIA_UPLOAD_DIR / unique_name
    file.save(str(filepath))

    # Determine media type
    if ext in ALLOWED_3D:
        media_type = "3d"
        mime = "model/gltf-binary" if ext == ".glb" else "model/gltf+json"
    else:
        media_type = "video"
        mime = "video/mp4" if ext == ".mp4" else "video/webm"

    entry = {
        "mediaId": _generate_id(),
        "businessId": business_id,
        "uploadedByUserId": user_id,
        "filename": unique_name,
        "originalName": original_name,
        "mediaType": media_type,
        "mimeType": mime,
        "createdAt": datetime.utcnow().isoformat(),
    }

    media = _load_media()
    media.append(entry)
    _save_media(media)
    return entry


def get_media(business_id: int) -> list[dict]:
    """Get all media entries for a business."""
    media = _load_media()
    return [m for m in media if m["businessId"] == business_id]


def delete_media(media_id: int, user_id: int) -> dict:
    """Delete a media entry (owner check)."""
    media = _load_media()
    for i, m in enumerate(media):
        if m["mediaId"] == media_id:
            if m["uploadedByUserId"] != user_id:
                raise ValueError("Not authorized to delete this media.")
            # Delete the file
            filepath = MEDIA_UPLOAD_DIR / m["filename"]
            if os.path.exists(str(filepath)):
                os.remove(str(filepath))
            deleted = media.pop(i)
            _save_media(media)
            return deleted
    raise ValueError("Media not found.")
