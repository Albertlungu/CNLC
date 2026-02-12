"""
./scripts/populate_images.py

Fetches an image URL for each business using DuckDuckGo image search.
Stores the URL in the 'image_url' field of each business in businesses.json.

Resumable: businesses that already have an 'image_url' are skipped.
Saves progress every 100 businesses so work is not lost on interruption.

Usage:
    python scripts/populate_images.py
"""

import os
import sys
import json
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from duckduckgo_search import DDGS
from backend.storage.json_handler import load_businesses

from config.config import BUSINESSES_JSON

SAVE_INTERVAL = 100
REQUEST_DELAY = 1.0


def get_city(business: dict) -> str:
    """Extract city name from a business dict."""
    address = business.get("address")
    if isinstance(address, dict):
        return address.get("city") or ""
    return ""


def search_image(name: str, city: str) -> str | None:
    """Search DuckDuckGo Images for a business and return the first result URL."""
    query = f'"{name}" {city} Canada'
    try:
        with DDGS() as ddgs:
            results = ddgs.images(query, max_results=1)
            if results:
                return results[0].get("image")
    except Exception as e:
        print(f"  [ERROR] Search failed for '{name}': {e}")
    return None


def save_progress(businesses: list[dict]) -> None:
    """Write the current businesses list back to businesses.json."""
    with open(str(BUSINESSES_JSON), "w") as f:
        json.dump(businesses, f, indent=4)


def main():
    businesses = load_businesses()
    total = len(businesses)
    already_done = sum(1 for b in businesses if b.get("image_url") is not None)
    remaining = total - already_done

    print("=" * 60)
    print(f"Total businesses: {total}")
    print(f"Already have images: {already_done}")
    print(f"Remaining to fetch: {remaining}")
    print("=" * 60)

    fetched = 0
    since_last_save = 0

    for i, business in enumerate(businesses):
        if business.get("image_url") is not None:
            continue

        name = business.get("name", "")
        city = get_city(business)

        url = search_image(name, city)
        business["image_url"] = url
        fetched += 1
        since_last_save += 1

        status = "OK" if url else "NO IMAGE"
        print(f"  [{already_done + fetched}/{total}] [{status}] {name} ({city})")

        if since_last_save >= SAVE_INTERVAL:
            save_progress(businesses)
            print(f"  -- Saved progress ({fetched} new images so far) --")
            since_last_save = 0

        time.sleep(REQUEST_DELAY)

    # Final save
    save_progress(businesses)

    print("=" * 60)
    print(f"Done. Fetched {fetched} new image URLs.")
    print("=" * 60)


if __name__ == "__main__":
    main()
