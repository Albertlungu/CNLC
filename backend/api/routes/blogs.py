"""
./backend/api/routes/blogs.py

Blog post endpoints for business owners.
"""

import os
import uuid

from flask import Blueprint, Response, jsonify, make_response, request

from backend.core import blog_manager, user_manager
from config.config import PROJECT_ROOT

blogs_bp = Blueprint("blogs", __name__, url_prefix="/api/blogs")

BLOG_UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads" / "blogs"
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def _check_business_owner(user_id, business_id):
    """Return True if user is authorized to manage this business's blog."""
    return user_manager.is_business_owner(user_id, business_id)


@blogs_bp.route("", methods=["POST"])
def create_post() -> Response:
    data = request.json or {}
    user_id = data.get("userId")
    business_id = data.get("businessId")
    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    tags = data.get("tags", [])
    cover_image = data.get("coverImage")

    if not all([user_id, business_id, title, content]):
        return make_response(jsonify({"status": "error", "message": "Missing required fields."}), 400)

    if not _check_business_owner(user_id, business_id):
        return make_response(jsonify({"status": "error", "message": "Not authorized to post for this business."}), 403)

    post = blog_manager.create_post(business_id, user_id, title, content, tags, cover_image)
    return make_response(jsonify({"status": "success", "post": post}), 201)


@blogs_bp.route("", methods=["GET"])
def get_posts() -> Response:
    business_id = request.args.get("business_id", type=int)
    limit = request.args.get("limit", 20, type=int)
    posts = blog_manager.get_posts(business_id=business_id, limit=limit)
    return jsonify({"posts": posts, "count": len(posts)})


@blogs_bp.route("/<int:post_id>", methods=["GET"])
def get_post(post_id: int) -> Response:
    post = blog_manager.get_post_by_id(post_id)
    if not post:
        return make_response(jsonify({"status": "error", "message": "Post not found."}), 404)
    return jsonify({"post": post})


@blogs_bp.route("/<int:post_id>", methods=["PUT"])
def update_post(post_id: int) -> Response:
    data = request.json or {}
    user_id = data.get("userId")
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "userId required."}), 400)

    try:
        post = blog_manager.update_post(
            post_id, user_id,
            title=data.get("title"),
            content=data.get("content"),
            tags=data.get("tags"),
        )
        return jsonify({"status": "success", "post": post})
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 403)


@blogs_bp.route("/<int:post_id>", methods=["DELETE"])
def delete_post(post_id: int) -> Response:
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return make_response(jsonify({"status": "error", "message": "user_id required."}), 400)

    try:
        blog_manager.delete_post(post_id, user_id)
        return jsonify({"status": "success"})
    except ValueError as e:
        return make_response(jsonify({"status": "error", "message": str(e)}), 403)


@blogs_bp.route("/feed", methods=["GET"])
def get_feed() -> Response:
    """Get global blog feed across all businesses."""
    limit = request.args.get("limit", 20, type=int)
    offset = request.args.get("offset", 0, type=int)
    tag = request.args.get("tag", type=str)
    posts = blog_manager.get_posts(business_id=None, limit=limit + offset)
    if tag:
        posts = [p for p in posts if tag.lower() in [t.lower() for t in p.get("tags", [])]]
    posts = posts[offset:offset + limit]

    # Enrich with business names
    import backend.storage.json_handler as jh
    businesses = {b["id"]: b["name"] for b in jh.load_businesses()}
    for p in posts:
        p["businessName"] = businesses.get(p.get("businessId"), "Unknown")

    return jsonify({"status": "success", "posts": posts, "count": len(posts)})


@blogs_bp.route("/upload-image", methods=["POST"])
def upload_image() -> Response:
    if "file" not in request.files:
        return make_response(jsonify({"status": "error", "message": "No file provided."}), 400)

    file = request.files["file"]
    if not file.filename:
        return make_response(jsonify({"status": "error", "message": "No file selected."}), 400)

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return make_response(jsonify({"status": "error", "message": f"File type not allowed."}), 400)

    os.makedirs(str(BLOG_UPLOAD_DIR), exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = BLOG_UPLOAD_DIR / filename
    file.save(str(filepath))

    photo_url = f"/uploads/blogs/{filename}"
    return jsonify({"status": "success", "imageUrl": photo_url})
