"""
./backend/core/blog_manager.py

Manages blog posts created by business owners.
"""

import json
import random
from datetime import datetime
from typing import Optional

from config.config import DATA_DIR

BLOGS_JSON = DATA_DIR / "blogs.json"


def _load_posts() -> list[dict]:
    try:
        with open(str(BLOGS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_posts(posts: list[dict]) -> None:
    with open(str(BLOGS_JSON), "w") as f:
        json.dump(posts, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def create_post(
    business_id: int,
    author_user_id: int,
    title: str,
    content: str,
    tags: Optional[list[str]] = None,
    cover_image: Optional[str] = None,
) -> dict:
    posts = _load_posts()
    now = datetime.utcnow().isoformat()

    post = {
        "postId": _generate_id(),
        "businessId": business_id,
        "authorUserId": author_user_id,
        "title": title,
        "content": content,
        "coverImage": cover_image,
        "tags": tags or [],
        "createdAt": now,
        "updatedAt": now,
    }

    posts.append(post)
    _save_posts(posts)
    return post


def get_posts(business_id: Optional[int] = None, limit: int = 20) -> list[dict]:
    posts = _load_posts()
    if business_id is not None:
        posts = [p for p in posts if p["businessId"] == business_id]
    posts.sort(key=lambda p: p.get("createdAt", ""), reverse=True)
    return posts[:limit]


def get_post_by_id(post_id: int) -> Optional[dict]:
    posts = _load_posts()
    for p in posts:
        if p["postId"] == post_id:
            return p
    return None


def update_post(post_id: int, user_id: int, title: str = None, content: str = None, tags: list[str] = None) -> dict:
    posts = _load_posts()
    for p in posts:
        if p["postId"] == post_id:
            if p["authorUserId"] != user_id:
                raise ValueError("Not authorized to edit this post.")
            if title is not None:
                p["title"] = title
            if content is not None:
                p["content"] = content
            if tags is not None:
                p["tags"] = tags
            p["updatedAt"] = datetime.utcnow().isoformat()
            _save_posts(posts)
            return p
    raise ValueError("Post not found.")


def delete_post(post_id: int, user_id: int) -> dict:
    posts = _load_posts()
    for i, p in enumerate(posts):
        if p["postId"] == post_id:
            if p["authorUserId"] != user_id:
                raise ValueError("Not authorized to delete this post.")
            deleted = posts.pop(i)
            _save_posts(posts)
            return deleted
    raise ValueError("Post not found.")
