"""
./backend/core/ai_manager.py

AI-powered recommendation engine using Google Gemini Flash.
Collects user activity and generates personalized business recommendations.
"""

import json
import os
import time
from datetime import datetime
from typing import Optional

from config.config import (
    RECOMMENDATIONS_CACHE_JSON,
    RECEIPTS_JSON,
    SAVED_BUSINESSES_JSON,
    REVIEWS_JSON,
    FRIENDS_JSON,
    BUSINESSES_JSON,
)

CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _load_json(path) -> list:
    try:
        with open(str(path), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _load_cache() -> dict:
    try:
        with open(str(RECOMMENDATIONS_CACHE_JSON), "r") as f:
            data = json.load(f)
            return {item["userId"]: item for item in data} if isinstance(data, list) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict) -> None:
    with open(str(RECOMMENDATIONS_CACHE_JSON), "w") as f:
        json.dump(list(cache.values()), f, indent=4)


def _build_user_context(user_id: int, search_history: list = None) -> str:
    """Collect all user activity into a text summary for Gemini."""
    parts = []

    # Receipts
    receipts = _load_json(RECEIPTS_JSON)
    user_receipts = [r for r in receipts if r.get("userId") == user_id]
    if user_receipts:
        businesses_spent = {}
        for r in user_receipts:
            bid = r.get("businessId")
            businesses_spent[bid] = businesses_spent.get(bid, 0) + r.get("amount", 0)
        parts.append(f"User has spent money at these businesses (businessId: amount): {businesses_spent}")

    # Saved businesses
    saved = _load_json(SAVED_BUSINESSES_JSON)
    user_saved = [s for s in saved if s.get("userId") == user_id]
    if user_saved:
        saved_ids = [s.get("businessId") for s in user_saved]
        parts.append(f"User has saved these business IDs: {saved_ids}")

    # Reviews
    reviews = _load_json(REVIEWS_JSON)
    user_reviews = [r for r in reviews if r.get("userID") == user_id]
    if user_reviews:
        review_summaries = [
            {"businessId": r.get("businessID"), "rating": r.get("rating"), "text": (r.get("review", ""))[:100]}
            for r in user_reviews
        ]
        parts.append(f"User reviews: {review_summaries}")

    # Friend activity
    friends = _load_json(FRIENDS_JSON)
    friend_ids = []
    for f in friends:
        if f.get("user1Id") == user_id:
            friend_ids.append(f.get("user2Id"))
        elif f.get("user2Id") == user_id:
            friend_ids.append(f.get("user1Id"))

    if friend_ids:
        friend_receipts = [r for r in receipts if r.get("userId") in friend_ids]
        if friend_receipts:
            friend_businesses = list(set(r.get("businessId") for r in friend_receipts))[:10]
            parts.append(f"User's friends visited these business IDs: {friend_businesses}")

    # Search history
    if search_history:
        parts.append(f"Recent searches: {search_history[:10]}")

    if not parts:
        return ""

    return " | ".join(parts)


def _get_business_sample() -> list[dict]:
    """Get a sample of businesses for Gemini to recommend from."""
    businesses = _load_json(BUSINESSES_JSON)
    # Take a random sample to keep prompt small
    import random
    sample = random.sample(businesses, min(100, len(businesses)))
    return [
        {"id": b.get("id"), "name": b.get("name"), "category": b.get("category", "")}
        for b in sample
    ]


def get_recommendations(user_id: int, search_history: list = None) -> dict:
    """Get AI-powered recommendations for a user."""
    # Check cache
    cache = _load_cache()
    cached = cache.get(user_id)
    if cached:
        cached_time = cached.get("cachedAt", 0)
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            return {"status": "success", "recommendations": cached.get("recommendations", []), "cached": True}

    # Build context
    context = _build_user_context(user_id, search_history)
    if not context:
        return {"status": "success", "recommendations": [], "message": "No activity found for recommendations."}

    # Get business sample
    business_sample = _get_business_sample()
    if not business_sample:
        return {"status": "success", "recommendations": [], "message": "No businesses available."}

    business_list = json.dumps(business_sample[:50])

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "Gemini API key not configured."}

    prompt = (
        f"Based on this user activity at local businesses: {context}\n\n"
        f"From the following businesses, recommend the top 5 that this user would most likely enjoy. "
        f"Available businesses: {business_list}\n\n"
        f"Return ONLY a valid JSON array of objects with 'businessId' (number) and 'reason' (string, max 50 words). "
        f"Do not include any other text or markdown formatting, just the raw JSON array."
    )

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Parse JSON from response (handle potential markdown wrapping)
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rsplit("```", 1)[0] if "```" in text else text

        recommendations = json.loads(text)

        if not isinstance(recommendations, list):
            recommendations = []

        # Enrich with business names
        businesses = _load_json(BUSINESSES_JSON)
        biz_map = {b.get("id"): b for b in businesses}
        for rec in recommendations:
            biz = biz_map.get(rec.get("businessId"))
            if biz:
                rec["businessName"] = biz.get("name", "")
                rec["category"] = biz.get("category", "")

        # Cache results
        cache[user_id] = {
            "userId": user_id,
            "recommendations": recommendations,
            "cachedAt": time.time(),
        }
        _save_cache(cache)

        return {"status": "success", "recommendations": recommendations, "cached": False}

    except json.JSONDecodeError:
        return {"status": "error", "message": "Failed to parse AI response."}
    except Exception as e:
        return {"status": "error", "message": f"AI recommendation error: {str(e)}"}
