"""
./backend/api/routes/scans.py

3D video scan upload and processing endpoints.
"""

import os
import uuid

from flask import (
    Blueprint,
    Response,
    jsonify,
    make_response,
    request,
    send_from_directory,
)

from backend.core import scan_processor, user_manager
from config.config import PROJECT_ROOT

scans_bp = Blueprint("scans", __name__, url_prefix="/api/scans")

TEMP_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "scans" / "temp"
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


def _check_business_owner(user_id, business_id):
    """Return True if user is authorized to manage this business."""
    return user_manager.is_business_owner(user_id, business_id)


@scans_bp.route("/upload", methods=["POST"])
def upload_scan() -> Response:
    """Upload a video file for 3D scan processing."""
    if "file" not in request.files:
        return make_response(
            jsonify({"status": "error", "message": "No file provided."}), 400
        )

    user_id = request.form.get("userId", type=int)
    business_id = request.form.get("businessId", type=int)

    if not user_id or not business_id:
        return make_response(
            jsonify({"status": "error", "message": "userId and businessId required."}),
            400,
        )

    if not _check_business_owner(user_id, business_id):
        return make_response(
            jsonify(
                {
                    "status": "error",
                    "message": "Not authorized to upload scans for this business.",
                }
            ),
            403,
        )

    file = request.files["file"]
    if not file.filename:
        return make_response(
            jsonify({"status": "error", "message": "No file selected."}), 400
        )

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return make_response(
            jsonify(
                {
                    "status": "error",
                    "message": f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
                }
            ),
            400,
        )

    # Save to temp location
    os.makedirs(str(TEMP_UPLOAD_DIR), exist_ok=True)
    temp_name = f"{uuid.uuid4().hex}{ext}"
    temp_path = TEMP_UPLOAD_DIR / temp_name
    file.save(str(temp_path))

    try:
        scan_entry = scan_processor.submit_scan(
            str(temp_path), user_id, business_id, file.filename
        )
        return make_response(
            jsonify(
                {
                    "status": "success",
                    "scan": {
                        "scanId": scan_entry["scanId"],
                        "status": scan_entry["status"],
                        "progress": scan_entry["progress"],
                    },
                }
            ),
            201,
        )
    except Exception as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 500)


@scans_bp.route("/<int:scan_id>/status", methods=["GET"])
def get_scan_status(scan_id: int) -> Response:
    """Get the processing status of a scan."""
    status = scan_processor.get_scan_status(scan_id)
    if not status:
        return make_response(
            jsonify({"status": "error", "message": "Scan not found."}), 404
        )
    return jsonify({"status": "success", "scan": status})


@scans_bp.route("", methods=["GET"])
def list_scans() -> Response:
    """List all scans for a business."""
    business_id = request.args.get("business_id", type=int)
    if not business_id:
        return make_response(
            jsonify({"status": "error", "message": "business_id required."}), 400
        )

    scans = scan_processor.list_scans(business_id)
    return jsonify({"status": "success", "scans": scans, "count": len(scans)})


@scans_bp.route("/<int:scan_id>/download", methods=["GET"])
def download_scan(scan_id: int) -> Response:
    """Download the resulting GLB file from a completed scan."""
    status = scan_processor.get_scan_status(scan_id)
    if not status:
        return make_response(
            jsonify({"status": "error", "message": "Scan not found."}), 404
        )

    if status["status"] != "completed":
        return make_response(
            jsonify({"status": "error", "message": "Scan not yet completed."}), 400
        )

    # Find the media entry to get the filename
    from backend.core.media_manager import MEDIA_UPLOAD_DIR, _load_media

    media_id = status.get("mediaId")
    if media_id:
        media = _load_media()
        for m in media:
            if m["mediaId"] == media_id:
                return send_from_directory(
                    str(MEDIA_UPLOAD_DIR), m["filename"], as_attachment=True
                )

    return make_response(
        jsonify({"status": "error", "message": "Output file not found."}), 404
    )
