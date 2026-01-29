"""
./backend/core/trending_manager.py

Manages receipt uploads and trending points calculation.

Points formula: points = A * ln(1 + (x / T)^n)
Where:
  x = total dollars spent at business
  T = 400 (transition threshold)
  n = 2 (steepness - makes low values exponential, high values logarithmic)
  A = 100 (scaling constant)

Behavior:
  - $20 total -> ~0.25 points (negligible)
  - $100 total -> ~6 points (still small)
  - $400 total -> ~69 points (transition point, "ln(2)" zone)
  - $1000 total -> ~174 points (slowing growth)
  - $5000 total -> ~326 points (slow logarithmic growth)
"""

import json
import math
import random
from datetime import datetime
from typing import Optional

from config.config import RECEIPTS_JSON, TRENDING_POINTS_JSON

# Points formula constants
POINTS_SCALE = 100       # A - scaling factor
POINTS_THRESHOLD = 400   # T - transition point in dollars
POINTS_STEEPNESS = 2     # n - exponent controlling curve shape


def _load_receipts() -> list[dict]:
    try:
        with open(str(RECEIPTS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_receipts(receipts: list[dict]) -> None:
    with open(str(RECEIPTS_JSON), "w") as f:
        json.dump(receipts, f, indent=4)


def _load_trending() -> list[dict]:
    try:
        with open(str(TRENDING_POINTS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_trending(trending: list[dict]) -> None:
    with open(str(TRENDING_POINTS_JSON), "w") as f:
        json.dump(trending, f, indent=4)


def _generate_id() -> int:
    return random.randint(10000000, 99999999)


def calculate_points(total_spent: float) -> float:
    """
    Calculate trending points from total dollars spent.
    Uses: points = A * ln(1 + (x / T)^n)
    """
    if total_spent <= 0:
        return 0.0
    ratio = total_spent / POINTS_THRESHOLD
    return POINTS_SCALE * math.log(1 + ratio ** POINTS_STEEPNESS)


def submit_receipt(user_id: int, business_id: int, amount: float, image_path: str) -> dict:
    if amount <= 0:
        return {"status": "error", "message": "Amount must be positive"}

    receipts = _load_receipts()

    receipt = {
        "receiptId": _generate_id(),
        "userId": user_id,
        "businessId": business_id,
        "amount": amount,
        "receiptImagePath": image_path,
        "submittedAt": datetime.utcnow().isoformat(),
        "verified": False,
    }

    receipts.append(receipt)
    _save_receipts(receipts)

    # Recalculate points for this business
    _update_business_points(business_id, receipts)

    return {"status": "success", "receipt": receipt}


def _update_business_points(business_id: int, receipts: Optional[list] = None) -> None:
    if receipts is None:
        receipts = _load_receipts()

    business_receipts = [r for r in receipts if r["businessId"] == business_id]
    total_spent = sum(r["amount"] for r in business_receipts)
    points = calculate_points(total_spent)

    trending = _load_trending()

    found = False
    for t in trending:
        if t["businessId"] == business_id:
            t["totalSpent"] = total_spent
            t["points"] = round(points, 2)
            t["receiptCount"] = len(business_receipts)
            found = True
            break

    if not found:
        trending.append({
            "businessId": business_id,
            "totalSpent": total_spent,
            "points": round(points, 2),
            "receiptCount": len(business_receipts),
        })

    _save_trending(trending)


def get_trending(limit: int = 50) -> list[dict]:
    trending = _load_trending()
    trending.sort(key=lambda t: t["points"], reverse=True)
    return trending[:limit]


def get_business_trending_stats(business_id: int) -> Optional[dict]:
    trending = _load_trending()
    for t in trending:
        if t["businessId"] == business_id:
            return t
    return None


def get_user_receipts(user_id: int) -> list[dict]:
    receipts = _load_receipts()
    return [r for r in receipts if r["userId"] == user_id]


def recalculate_all_points() -> None:
    receipts = _load_receipts()
    business_ids = set(r["businessId"] for r in receipts)

    trending = []
    for bid in business_ids:
        business_receipts = [r for r in receipts if r["businessId"] == bid]
        total_spent = sum(r["amount"] for r in business_receipts)
        points = calculate_points(total_spent)
        trending.append({
            "businessId": bid,
            "totalSpent": total_spent,
            "points": round(points, 2),
            "receiptCount": len(business_receipts),
        })

    _save_trending(trending)
