"""
./backend/api/routes/trending.py

API routes for trending businesses and receipt uploads.
"""

import os
import uuid

from flask import Blueprint, jsonify, request

from backend.core import trending_manager as tm
from config.config import PROJECT_ROOT

trending_bp = Blueprint("trending", __name__, url_prefix="/api/trending")

RECEIPT_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "receipts"


@trending_bp.route("/receipts", methods=["POST"])
def upload_receipt():
    user_id = request.form.get("userId", type=int)
    business_id = request.form.get("businessId", type=int)
    amount = request.form.get("amount", type=float)

    if not all([user_id, business_id, amount]):
        return jsonify({"status": "error", "message": "userId, businessId, and amount are required"}), 400

    if amount <= 0:
        return jsonify({"status": "error", "message": "Amount must be positive"}), 400

    # Handle image upload
    image = request.files.get("receiptImage")
    if not image:
        return jsonify({"status": "error", "message": "Receipt image is required"}), 400

    os.makedirs(str(RECEIPT_UPLOAD_DIR), exist_ok=True)

    ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    image_path = str(RECEIPT_UPLOAD_DIR / filename)
    image.save(image_path)

    relative_path = f"receipts/{filename}"

    result = tm.submit_receipt(user_id, business_id, amount, relative_path)
    return jsonify(result), 201 if result["status"] == "success" else 400


@trending_bp.route("", methods=["GET"])
def get_trending():
    limit = request.args.get("limit", 50, type=int)
    trending = tm.get_trending(limit)
    return jsonify({"status": "success", "trending": trending})


@trending_bp.route("/<int:business_id>/stats", methods=["GET"])
def get_stats(business_id):
    stats = tm.get_business_trending_stats(business_id)
    if stats is None:
        return jsonify({"status": "success", "stats": {"businessId": business_id, "totalSpent": 0, "points": 0, "receiptCount": 0}})
    return jsonify({"status": "success", "stats": stats})


@trending_bp.route("/receipts", methods=["GET"])
def get_user_receipts():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    receipts = tm.get_user_receipts(user_id)
    return jsonify({"status": "success", "receipts": receipts})
