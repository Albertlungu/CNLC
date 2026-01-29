"""
./backend/core/deal_manager.py

Manages deals and coupons for businesses.
"""

import json
import random
import re
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config.config import DEALS_JSON


def _load_deals() -> list[dict]:
    try:
        with open(str(DEALS_JSON), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_deals(deals: list[dict]) -> None:
    with open(str(DEALS_JSON), "w") as f:
        json.dump(deals, f, indent=4)


def _generate_deal_id() -> int:
    return random.randint(10000000, 99999999)


def create_deal(
    business_id: int,
    title: str,
    description: str,
    discount_type: str,
    discount_value: Optional[float] = None,
    expires_at: Optional[str] = None,
    created_by_user_id: Optional[int] = None,
    source: str = "manual",
    source_url: Optional[str] = None,
) -> dict:
    deals = _load_deals()

    deal = {
        "dealId": _generate_deal_id(),
        "businessId": business_id,
        "createdByUserId": created_by_user_id,
        "title": title,
        "description": description,
        "discountType": discount_type,
        "discountValue": discount_value,
        "expiresAt": expires_at,
        "createdAt": datetime.utcnow().isoformat(),
        "isActive": True,
        "source": source,
        "sourceUrl": source_url,
    }

    deals.append(deal)
    _save_deals(deals)
    return deal


def get_deals(
    business_id: Optional[int] = None,
    category: Optional[str] = None,
    active_only: bool = True,
) -> list[dict]:
    deals = _load_deals()

    if active_only:
        now = datetime.utcnow().isoformat()
        deals = [
            d for d in deals
            if d.get("isActive", True)
            and (d.get("expiresAt") is None or d.get("expiresAt") > now)
        ]

    if business_id is not None:
        deals = [d for d in deals if d["businessId"] == business_id]

    return deals


def get_deal_by_id(deal_id: int) -> Optional[dict]:
    deals = _load_deals()
    for deal in deals:
        if deal["dealId"] == deal_id:
            return deal
    return None


def delete_deal(deal_id: int) -> bool:
    deals = _load_deals()
    for i, deal in enumerate(deals):
        if deal["dealId"] == deal_id:
            deals.pop(i)
            _save_deals(deals)
            return True
    return False


def cleanup_expired_deals() -> int:
    deals = _load_deals()
    now = datetime.utcnow().isoformat()
    original_count = len(deals)

    deals = [
        d for d in deals
        if d.get("expiresAt") is None or d.get("expiresAt") > now
    ]

    _save_deals(deals)
    return original_count - len(deals)


def save_deal_for_user(user_id: int, deal_id: int) -> dict:
    deals = _load_deals()
    deal = None
    for d in deals:
        if d["dealId"] == deal_id:
            deal = d
            break

    if deal is None:
        return {"status": "error", "message": "Deal not found"}

    saved_deals_path = str(DEALS_JSON).replace("deals.json", "saved_deals.json")
    try:
        with open(saved_deals_path, "r") as f:
            saved = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        saved = []

    for s in saved:
        if s["userId"] == user_id and s["dealId"] == deal_id:
            return {"status": "error", "message": "Deal already saved"}

    saved.append({
        "savedDealId": _generate_deal_id(),
        "userId": user_id,
        "dealId": deal_id,
        "savedAt": datetime.utcnow().isoformat(),
    })

    with open(saved_deals_path, "w") as f:
        json.dump(saved, f, indent=4)

    return {"status": "success"}


def unsave_deal_for_user(user_id: int, deal_id: int) -> dict:
    saved_deals_path = str(DEALS_JSON).replace("deals.json", "saved_deals.json")
    try:
        with open(saved_deals_path, "r") as f:
            saved = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"status": "error", "message": "No saved deals found"}

    for i, s in enumerate(saved):
        if s["userId"] == user_id and s["dealId"] == deal_id:
            saved.pop(i)
            with open(saved_deals_path, "w") as f:
                json.dump(saved, f, indent=4)
            return {"status": "success"}

    return {"status": "error", "message": "Saved deal not found"}


def scrape_deals(business_name: str, city: str = "Ottawa") -> list[dict]:
    """
    Scrape deals from the web for a given business.
    Uses DuckDuckGo HTML search (no API key needed) and parses results.
    """
    scraped_deals = []
    query = f"{business_name} {city} coupons deals discounts"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    try:
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return scraped_deals

        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.select(".result__body")

        for result in results[:5]:
            title_el = result.select_one(".result__title a")
            snippet_el = result.select_one(".result__snippet")

            if not title_el:
                continue

            title_text = title_el.get_text(strip=True)
            snippet = snippet_el.get_text(strip=True) if snippet_el else ""
            link = title_el.get("href", "")

            # Check if the result looks like an actual deal
            deal_keywords = ["off", "coupon", "deal", "discount", "save", "free", "%", "$"]
            combined_text = (title_text + " " + snippet).lower()
            if not any(kw in combined_text for kw in deal_keywords):
                continue

            # Try to extract discount info
            discount_type = "other"
            discount_value = None

            percent_match = re.search(r"(\d+)\s*%\s*off", combined_text)
            dollar_match = re.search(r"\$\s*(\d+(?:\.\d+)?)\s*off", combined_text)

            if percent_match:
                discount_type = "percentage"
                discount_value = float(percent_match.group(1))
            elif dollar_match:
                discount_type = "fixed"
                discount_value = float(dollar_match.group(1))

            scraped_deals.append({
                "title": title_text[:200],
                "description": snippet[:1000],
                "discountType": discount_type,
                "discountValue": discount_value,
                "source": "scraped",
                "sourceUrl": link,
            })

    except Exception as e:
        print(f"Error scraping deals: {e}")

    return scraped_deals
