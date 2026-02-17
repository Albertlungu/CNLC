"""
./backend/api/routes/media.py

Media upload endpoints (3D models and videos) for businesses.
"""

from flask import Blueprint, Response, jsonify, make_response, request

from backend.core import media_manager, user_manager

media_bp = Blueprint("media", __name__, url_prefix="/api")


def _check_business_owner(user_id, business_id):
    """Return True if user is authorized to manage this business's media."""
    return user_manager.is_business_owner(user_id, business_id)


@media_bp.route("/businesses/<int:business_id>/media", methods=["POST"])
def upload_media(business_id: int) -> Response:
    if "file" not in request.files:
        return make_response(jsonify({"status": "error", "message": "No file provided."}), 400)

    user_id = request.form.get("userId", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "userId required."}), 400)

    if not _check_business_owner(user_id, business_id):
        return make_response(jsonify({"status": "error", "message": "Not authorized to upload media for this business."}), 403)

    file = request.files["file"]
    if not file.filename:
        return make_response(jsonify({"status": "error", "message": "No file selected."}), 400)

    try:
        entry = media_manager.save_media(business_id, user_id, file)
        entry["url"] = f"/uploads/media/{entry['filename']}"
        return make_response(jsonify({"status": "success", "media": entry}), 201)
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 400)


@media_bp.route("/businesses/<int:business_id>/media", methods=["GET"])
def get_media(business_id: int) -> Response:
    media = media_manager.get_media(business_id)
    for m in media:
        m["url"] = f"/uploads/media/{m['filename']}"
    return jsonify({"media": media, "count": len(media)})


@media_bp.route("/media/<int:media_id>", methods=["DELETE"])
def delete_media(media_id: int) -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    try:
        media_manager.delete_media(media_id, user_id)
        return jsonify({"status": "success"})
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 403)
