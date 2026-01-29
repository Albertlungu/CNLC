"""
./backend/api/routes/deals.py

API routes for deals and coupons.
"""

from flask import Blueprint, jsonify, request

from backend.core import deal_manager as dm

deals_bp = Blueprint("deals", __name__, url_prefix="/api/deals")


@deals_bp.route("", methods=["POST"])
def create_deal():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    business_id = data.get("businessId")
    title = data.get("title")
    discount_type = data.get("discountType")

    if not all([business_id, title, discount_type]):
        return jsonify({"status": "error", "message": "businessId, title, and discountType are required"}), 400

    deal = dm.create_deal(
        business_id=business_id,
        title=title,
        description=data.get("description", ""),
        discount_type=discount_type,
        discount_value=data.get("discountValue"),
        expires_at=data.get("expiresAt"),
        created_by_user_id=data.get("createdByUserId"),
    )

    return jsonify({"status": "success", "deal": deal}), 201


@deals_bp.route("", methods=["GET"])
def get_deals():
    business_id = request.args.get("business_id", type=int)
    active_only = request.args.get("active_only", "true").lower() == "true"

    deals = dm.get_deals(business_id=business_id, active_only=active_only)
    return jsonify({"status": "success", "deals": deals})


@deals_bp.route("/<int:deal_id>", methods=["GET"])
def get_deal(deal_id):
    deal = dm.get_deal_by_id(deal_id)
    if deal is None:
        return jsonify({"status": "error", "message": "Deal not found"}), 404
    return jsonify({"status": "success", "deal": deal})


@deals_bp.route("/<int:deal_id>", methods=["DELETE"])
def delete_deal(deal_id):
    if dm.delete_deal(deal_id):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Deal not found"}), 404


@deals_bp.route("/<int:deal_id>/save", methods=["POST"])
def save_deal(deal_id):
    data = request.get_json()
    if not data or not data.get("userId"):
        return jsonify({"status": "error", "message": "userId is required"}), 400

    result = dm.save_deal_for_user(data["userId"], deal_id)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)


@deals_bp.route("/<int:deal_id>/unsave", methods=["DELETE"])
def unsave_deal(deal_id):
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id is required"}), 400

    result = dm.unsave_deal_for_user(user_id, deal_id)
    if result["status"] == "error":
        return jsonify(result), 400
    return jsonify(result)


@deals_bp.route("/scrape", methods=["POST"])
def scrape_deals():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    business_name = data.get("businessName")
    business_id = data.get("businessId")
    city = data.get("city", "Ottawa")

    if not business_name or not business_id:
        return jsonify({"status": "error", "message": "businessName and businessId are required"}), 400

    scraped = dm.scrape_deals(business_name, city)

    # Save scraped deals
    created_deals = []
    for s in scraped:
        deal = dm.create_deal(
            business_id=business_id,
            title=s["title"],
            description=s.get("description", ""),
            discount_type=s.get("discountType", "other"),
            discount_value=s.get("discountValue"),
            source="scraped",
            source_url=s.get("sourceUrl"),
        )
        created_deals.append(deal)

    return jsonify({"status": "success", "deals": created_deals, "count": len(created_deals)})
