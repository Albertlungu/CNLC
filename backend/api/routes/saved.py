from flask import Blueprint, request, jsonify
from backend.core import saved_manager

saved_bp = Blueprint("saved", __name__, url_prefix="/api/saved")


# Collection Routes
@saved_bp.route("/collections", methods=["GET"])
def get_collections():
    """Get all collections for a user."""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id required"}), 400

    try:
        collections = saved_manager.get_user_collections(user_id)
        return jsonify({"status": "success", "collections": collections})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/collections/stats", methods=["GET"])
def get_collection_stats():
    """Get collection statistics for a user."""
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify({"status": "error", "message": "user_id required"}), 400

    try:
        stats = saved_manager.get_collection_stats(user_id)
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/collections", methods=["POST"])
def create_collection():
    """Create a new collection."""
    data = request.get_json()
    user_id = data.get("userId")
    name = data.get("name")

    if not user_id or not name:
        return jsonify({"status": "error", "message": "userId and name required"}), 400

    try:
        collection = saved_manager.create_collection(user_id, name)
        return jsonify({"status": "success", "collection": collection}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/collections/<int:collection_id>", methods=["PUT"])
def rename_collection(collection_id):
    """Rename a collection."""
    data = request.get_json()
    user_id = data.get("userId")
    new_name = data.get("name")

    if not user_id or not new_name:
        return jsonify({"status": "error", "message": "userId and name required"}), 400

    try:
        success = saved_manager.rename_collection(user_id, collection_id, new_name)
        if success:
            return jsonify({"status": "success", "message": "Collection renamed"})
        else:
            return jsonify({"status": "error", "message": "Collection not found"}), 404
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/collections/<int:collection_id>", methods=["DELETE"])
def delete_collection(collection_id):
    """Delete a collection."""
    data = request.get_json()
    user_id = data.get("userId")

    if not user_id:
        return jsonify({"status": "error", "message": "userId required"}), 400

    try:
        success = saved_manager.delete_collection(user_id, collection_id)
        if success:
            return jsonify({"status": "success", "message": "Collection deleted"})
        else:
            return jsonify({"status": "error", "message": "Collection not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# Saved Business Routes
@saved_bp.route("/businesses", methods=["GET"])
def get_saved_businesses():
    """Get saved businesses for a user, optionally filtered by collection."""
    user_id = request.args.get("user_id", type=int)
    collection_id = request.args.get("collection_id", type=int)

    if not user_id:
        return jsonify({"status": "error", "message": "user_id required"}), 400

    try:
        saved_businesses = saved_manager.get_saved_businesses(user_id, collection_id)
        return jsonify({"status": "success", "savedBusinesses": saved_businesses})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/businesses", methods=["POST"])
def save_business():
    """Save a business to a collection."""
    data = request.get_json()
    user_id = data.get("userId")
    business_id = data.get("businessId")
    collection_id = data.get("collectionId")

    if not user_id or not business_id or not collection_id:
        return jsonify({"status": "error", "message": "userId, businessId, and collectionId required"}), 400

    try:
        saved = saved_manager.save_business(user_id, business_id, collection_id)
        return jsonify({"status": "success", "saved": saved}), 201
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/businesses/<int:business_id>", methods=["DELETE"])
def unsave_business(business_id):
    """Remove a business from saved (optionally from specific collection)."""
    data = request.get_json()
    user_id = data.get("userId")
    collection_id = data.get("collectionId")  # Optional

    if not user_id:
        return jsonify({"status": "error", "message": "userId required"}), 400

    try:
        success = saved_manager.unsave_business(user_id, business_id, collection_id)
        if success:
            return jsonify({"status": "success", "message": "Business removed from saved"})
        else:
            return jsonify({"status": "error", "message": "Business not found in saved"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/businesses/<int:business_id>/check", methods=["GET"])
def check_business_saved(business_id):
    """Check if a business is saved by the user."""
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({"status": "error", "message": "user_id required"}), 400

    try:
        result = saved_manager.is_business_saved(user_id, business_id)
        return jsonify({"status": "success", **result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@saved_bp.route("/businesses/<int:business_id>/move", methods=["PUT"])
def move_business(business_id):
    """Move a business from one collection to another."""
    data = request.get_json()
    user_id = data.get("userId")
    old_collection_id = data.get("oldCollectionId")
    new_collection_id = data.get("newCollectionId")

    if not user_id or not old_collection_id or not new_collection_id:
        return jsonify({"status": "error", "message": "userId, oldCollectionId, and newCollectionId required"}), 400

    try:
        success = saved_manager.move_business_to_collection(user_id, business_id, old_collection_id, new_collection_id)
        if success:
            return jsonify({"status": "success", "message": "Business moved to new collection"})
        else:
            return jsonify({"status": "error", "message": "Business not found in source collection"}), 404
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
