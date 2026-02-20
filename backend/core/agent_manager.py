"""
./backend/core/agent_manager.py

AI agent powered by Gemini with function calling.
Orchestrates tool calls to existing core managers, manages conversation
state server-side, and returns structured responses for the frontend.
"""

import json
import logging
import os
import time
import traceback
import threading
from datetime import datetime

log = logging.getLogger(__name__)

from google import genai
from google.genai import types

from backend.core import business_manager, reservation_manager, review_manager, deal_manager, saved_manager, friend_manager, user_manager
from backend.storage.json_handler import load_businesses

# ---------------------------------------------------------------------------
# Server-side conversation store  (userId -> {history, lastAccess})
# ---------------------------------------------------------------------------
_conversations: dict = {}
_conv_lock = threading.Lock()
_CONV_TTL = 3600        # 1 hour
_MAX_HISTORY = 50       # messages kept per conversation
_MAX_TOOL_ITERS = 15
_MAX_TOOL_RESULT = 5000  # chars

SYSTEM_PROMPT = """You are the CNLC assistant -- a fully autonomous AI concierge for discovering and interacting with local businesses across Canada.

You have access to tools that let you search businesses, read reviews, make reservations, find deals, save favorites, look up friends, and search the web. Use them proactively and chain multiple tool calls to accomplish complex tasks without asking the user unnecessary questions.

You are an AGENT -- think step-by-step and use as many tool calls as needed to fully answer the user's request. For example, if asked "find me the best restaurant deals in Ottawa", you should: (1) search for restaurants in Ottawa, (2) call find_deals for each promising result, (3) compare the deals, and (4) present the best ones. Do not stop at one tool call when more are needed.

Guidelines:
- Always CONFIRM with the user before making a reservation or saving a business. State the details and ask "Shall I go ahead?"
- Keep responses concise but informative.
- If a tool call fails, explain the issue simply and suggest an alternative.
- For date/time references like "this Friday" or "tomorrow", calculate the actual date based on today's date which is provided in the context.
- Never fabricate business data. Only present information returned by your tools.
- NEVER claim CNLC users said something unless "cnlc_reviews" data is present in the tool results. If the field is missing, there are no CNLC reviews -- do not invent them.
- Only describe details that appear in the actual tool results. Do not guess or embellish.
- CRITICAL: Maintain full conversational context across turns. When the user refers to a business mentioned earlier (e.g., "book that one", "the first one", "Chantal's"), look back in the conversation to find the business name AND its numeric ID. Never ask the user to repeat information you already have from earlier in the conversation.
- When making a reservation, you need business_id, business_name, date, time, and party_size. If the user already mentioned some of these earlier, USE that information -- do not ask again.

When recommending businesses, follow this process:
1. Search for businesses matching the user's request. The search results already include CNLC user reviews (in "cnlc_reviews") and web reviews from other sites (in "web_reviews"). Do NOT call get_reviews_summary or search_web separately after a search -- that data is already included.
2. If the user asks about deals, coupons, or discounts, call find_deals for each relevant business to search the web for current offers. You can call find_deals multiple times in parallel for different businesses.
3. Pick the best results to present. For general recommendations, show around 3. For broader requests like "show me all" or "find the best deals", show as many as are relevant.
4. Present each business ONE AT A TIME using this format:

   Write a paragraph about the business: what it is, location, and what people say about it based on web_reviews snippets. Only mention CNLC reviews if the "cnlc_reviews" field is actually present in the data -- do NOT invent or assume CNLC reviews exist. Only mention deals if the "deals" field is present or you found deals via find_deals. Then, on its own line, write the marker {{CARD:business_id}} (replacing business_id with the actual numeric ID). This marker tells the UI to display the business card inline.

   Example:
   **Joe's Diner** is a beloved family restaurant in downtown Ottawa. Online reviewers praise the generous portions, cozy atmosphere, and friendly staff. They currently have a 15% off dinner deal on Groupon.
   {{CARD:42}}

5. After presenting all businesses, add a brief closing line asking if the user wants more details, to make a reservation, or to see other options.

Important: Always use the {{CARD:id}} marker on its own line after each business description. Do not skip this marker -- it is required for the UI to render properly. Do not dump all businesses at once without individual descriptions.
"""

# ---------------------------------------------------------------------------
# Tool declarations for Gemini function calling (new google.genai SDK)
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_businesses",
        description="Search for businesses by name, category, or location. Returns a list of matching businesses.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query (business name or keyword)"},
                "category": {"type": "string", "description": "Business category filter (e.g. restaurant, cafe, bakery, hairdresser, beauty, clothes, convenience, supermarket)"},
                "city": {"type": "string", "description": "City to search in (e.g. Ottawa, Toronto, Vancouver, Calgary, Edmonton, Winnipeg, Regina)"},
            },
        },
    ),
    types.FunctionDeclaration(
        name="get_business_details",
        description="Get full details of a specific business by its ID.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "business_id": {"type": "integer", "description": "The business ID"},
            },
            "required": ["business_id"],
        },
    ),
    types.FunctionDeclaration(
        name="get_reviews_summary",
        description="Get reviews for a business including average rating and top reviews.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "business_id": {"type": "integer", "description": "The business ID"},
            },
            "required": ["business_id"],
        },
    ),
    types.FunctionDeclaration(
        name="make_reservation",
        description="Create a reservation at a business. Always confirm details with the user before calling this.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "business_id": {"type": "integer", "description": "The business ID"},
                "business_name": {"type": "string", "description": "The business name"},
                "date": {"type": "string", "description": "Reservation date in YYYY-MM-DD format"},
                "time": {"type": "string", "description": "Reservation time in HH:MM format (24h)"},
                "party_size": {"type": "integer", "description": "Number of guests"},
                "notes": {"type": "string", "description": "Optional notes for the reservation"},
            },
            "required": ["business_id", "business_name", "date", "time", "party_size"],
        },
    ),
    types.FunctionDeclaration(
        name="get_user_reservations",
        description="Get all reservations for the current user.",
        parameters_json_schema={
            "type": "object",
            "properties": {},
        },
    ),
    types.FunctionDeclaration(
        name="cancel_reservation",
        description="Cancel a reservation. Always confirm with the user before calling this.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "reservation_id": {"type": "integer", "description": "The reservation ID to cancel"},
            },
            "required": ["reservation_id"],
        },
    ),
    types.FunctionDeclaration(
        name="find_deals",
        description="Search the web for active deals, coupons, and discounts for a specific business. Use this when the user asks about deals.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "business_id": {"type": "integer", "description": "The business ID"},
            },
            "required": ["business_id"],
        },
    ),
    types.FunctionDeclaration(
        name="save_business",
        description="Save a business to the user's collection. Always confirm with the user first.",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "business_id": {"type": "integer", "description": "The business ID to save"},
                "collection_name": {"type": "string", "description": "Name of the collection to save to (created if it doesn't exist). Defaults to 'Favorites'."},
            },
            "required": ["business_id"],
        },
    ),
    types.FunctionDeclaration(
        name="get_saved_businesses",
        description="Get all businesses the user has saved.",
        parameters_json_schema={
            "type": "object",
            "properties": {},
        },
    ),
    types.FunctionDeclaration(
        name="get_friend_activity",
        description="Get recent activity (reviews) from the user's friends.",
        parameters_json_schema={
            "type": "object",
            "properties": {},
        },
    ),
    types.FunctionDeclaration(
        name="get_friends_list",
        description="Get the user's friends list with usernames and profile info.",
        parameters_json_schema={
            "type": "object",
            "properties": {},
        },
    ),
    types.FunctionDeclaration(
        name="search_web",
        description="Search the web for additional information about a business (menus, atmosphere, hours, etc).",
        parameters_json_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
            },
            "required": ["query"],
        },
    ),
])


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _web_search_snippets(query: str, max_results: int = 3) -> list:
    """Run a quick DuckDuckGo search and return snippets. Returns [] on failure."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=max_results)
        return [
            {"title": r.get("title", ""), "snippet": (r.get("body") or "")[:200]}
            for r in (results or [])
        ]
    except Exception:
        return []


def _exec_search_businesses(args: dict) -> dict:
    businesses = load_businesses()
    results = businesses

    city = args.get("city")
    if city:
        results = [
            b for b in results
            if isinstance(b.get("address"), dict) and
            b["address"].get("city", "").lower() == city.lower()
        ]

    category = args.get("category")
    if category:
        results = business_manager.filter_by_category(results, category)

    query = args.get("query")
    if query:
        results = business_manager.search_by_name(results, query)

    results = results[:5]

    # Enrich each result with CNLC reviews, deals, and web info server-side
    # so Gemini doesn't need separate tool calls (saves API quota)
    enriched = []

    # Kick off web searches in parallel for the top 3 businesses
    from concurrent.futures import ThreadPoolExecutor
    web_futures = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        for b in results[:3]:
            name = b.get("name", "")
            biz_city = ""
            if isinstance(b.get("address"), dict):
                biz_city = b["address"].get("city", "")
            if name:
                web_futures[b.get("id")] = pool.submit(
                    _web_search_snippets, f"{name} {biz_city} reviews", 3
                )

    for b in results:
        biz_id = b.get("id")
        entry = {
            "id": biz_id,
            "name": b.get("name"),
            "category": b.get("category"),
            "address": b.get("address"),
            "phone": b.get("phone"),
            "website": b.get("website"),
            "image_url": b.get("image_url"),
            "opening_hours": b.get("opening_hours"),
        }

        # Attach CNLC reviews summary
        if biz_id:
            try:
                reviews = review_manager.get_reviews_for_business(biz_id)
                if reviews:
                    ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
                    avg = round(sum(ratings) / len(ratings), 1) if ratings else None
                    top = sorted(reviews, key=lambda r: r.get("helpfulCount", 0), reverse=True)[:2]
                    entry["cnlc_reviews"] = {
                        "avg_rating": avg,
                        "count": len(reviews),
                        "top": [
                            {"rating": r.get("rating"), "text": (r.get("review") or "")[:200]}
                            for r in top
                        ],
                    }
            except Exception:
                pass

            # Attach active deals (stored only -- scraping happens via find_deals tool)
            try:
                deals = deal_manager.get_deals(business_id=biz_id, active_only=True)
                if deals:
                    entry["deals"] = [
                        {
                            "title": d.get("title"),
                            "discountType": d.get("discountType"),
                            "discountValue": d.get("discountValue"),
                            "description": d.get("description"),
                        }
                        for d in deals[:3]
                    ]
            except Exception:
                pass

            # Attach web review snippets (from parallel search)
            future = web_futures.get(biz_id)
            if future:
                try:
                    snippets = future.result(timeout=5)
                    if snippets:
                        entry["web_reviews"] = snippets
                except Exception:
                    pass

        enriched.append(entry)

    return {
        "businesses": enriched,
        "count": len(enriched),
        "navigation_url": "businesses.html",
    }


def _exec_get_business_details(args: dict) -> dict:
    businesses = load_businesses()
    try:
        results = business_manager.search_by_id(businesses, args["business_id"])
        b = results[0]
        return {
            "business": {
                "id": b.get("id"),
                "name": b.get("name"),
                "category": b.get("category"),
                "address": b.get("address"),
                "phone": b.get("phone"),
                "website": b.get("website"),
                "opening_hours": b.get("opening_hours"),
                "cuisine": b.get("cuisine"),
                "image_url": b.get("image_url"),
            },
            "navigation_url": f"business-detail.html?id={args['business_id']}",
        }
    except ValueError:
        return {"error": "Business not found"}


def _exec_get_reviews_summary(args: dict) -> dict:
    reviews = review_manager.get_reviews_for_business(args["business_id"])
    if not reviews:
        return {"message": "No reviews found for this business", "avg_rating": None, "count": 0, "reviews": []}

    ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
    avg = round(sum(ratings) / len(ratings), 1) if ratings else None

    sorted_reviews = sorted(reviews, key=lambda r: r.get("helpfulCount", 0), reverse=True)
    top = sorted_reviews[:3]

    return {
        "avg_rating": avg,
        "count": len(reviews),
        "reviews": [
            {
                "username": r.get("username"),
                "rating": r.get("rating"),
                "text": (r.get("review") or "")[:300],
                "helpful_count": r.get("helpfulCount", 0),
            }
            for r in top
        ],
        "navigation_url": f"business-detail.html?id={args['business_id']}",
    }


def _exec_make_reservation(args: dict, user_id: int) -> dict:
    reservation = reservation_manager.create_reservation(
        user_id=user_id,
        business_id=args["business_id"],
        business_name=args["business_name"],
        date=args["date"],
        time=args["time"],
        party_size=args["party_size"],
        notes=args.get("notes"),
    )
    return {
        "reservation": reservation,
        "navigation_url": "reservations.html",
    }


def _exec_get_user_reservations(user_id: int) -> dict:
    reservations = reservation_manager.get_user_reservations(user_id)
    upcoming = [r for r in reservations if r.get("status") == "confirmed"]
    return {
        "reservations": upcoming[:10],
        "total": len(upcoming),
        "navigation_url": "reservations.html",
    }


def _exec_cancel_reservation(args: dict, user_id: int) -> dict:
    try:
        reservation = reservation_manager.cancel_reservation(args["reservation_id"], user_id)
        return {"cancelled": reservation, "navigation_url": "reservations.html"}
    except ValueError as e:
        return {"error": str(e)}


def _exec_find_deals(args: dict) -> dict:
    biz_id = args["business_id"]
    deals = deal_manager.get_deals(business_id=biz_id, active_only=True)

    # If no stored deals, scrape the web (same as the Deals page does)
    if not deals:
        businesses = load_businesses()
        biz = None
        try:
            biz = business_manager.search_by_id(businesses, biz_id)[0]
        except (ValueError, IndexError):
            pass

        if biz:
            biz_name = biz.get("name", "")
            biz_city = ""
            if isinstance(biz.get("address"), dict):
                biz_city = biz["address"].get("city", "")

            scraped = deal_manager.scrape_deals(biz_name, biz_city or "Canada")
            for s in scraped:
                deal_manager.create_deal(
                    business_id=biz_id,
                    title=s["title"],
                    description=s.get("description", ""),
                    discount_type=s.get("discountType", "other"),
                    discount_value=s.get("discountValue"),
                    source="scraped",
                    source_url=s.get("sourceUrl"),
                )
            # Re-fetch after saving
            deals = deal_manager.get_deals(business_id=biz_id, active_only=True)

    return {
        "deals": [
            {
                "dealId": d.get("dealId"),
                "title": d.get("title"),
                "description": d.get("description"),
                "discountType": d.get("discountType"),
                "discountValue": d.get("discountValue"),
                "expiresAt": d.get("expiresAt"),
            }
            for d in deals
        ],
        "count": len(deals),
        "navigation_url": "deals.html",
    }


def _exec_save_business(args: dict, user_id: int) -> dict:
    collection_name = args.get("collection_name", "Favorites")
    collections = saved_manager.get_user_collections(user_id)

    target = None
    for c in collections:
        if c["name"].lower() == collection_name.lower():
            target = c
            break

    if not target:
        target = saved_manager.create_collection(user_id, collection_name)

    try:
        saved = saved_manager.save_business(user_id, args["business_id"], target["collectionId"])
        return {"saved": saved, "collection": collection_name, "navigation_url": "saved.html"}
    except ValueError as e:
        return {"error": str(e)}


def _exec_get_saved_businesses(user_id: int) -> dict:
    from backend.core.saved_manager import _load_saved_businesses
    saved = _load_saved_businesses()
    user_saved = [s for s in saved if s.get("userId") == user_id]

    businesses = load_businesses()
    biz_map = {b["id"]: b for b in businesses}

    results = []
    for s in user_saved[:20]:
        biz = biz_map.get(s.get("businessId"))
        if biz:
            results.append({
                "id": biz.get("id"),
                "name": biz.get("name"),
                "category": biz.get("category"),
                "address": biz.get("address"),
            })

    return {"saved_businesses": results, "count": len(results), "navigation_url": "saved.html"}


def _exec_get_friend_activity(user_id: int) -> dict:
    activity = friend_manager.get_friend_activity(user_id, limit=10)
    return {
        "activity": [
            {
                "username": a.get("username"),
                "businessId": a.get("businessID"),
                "rating": a.get("rating"),
                "text": (a.get("review") or "")[:200],
            }
            for a in activity
        ],
        "count": len(activity),
        "navigation_url": "friends.html",
    }


def _exec_get_friends_list(user_id: int) -> dict:
    friends = friend_manager.get_friends(user_id)
    results = []
    for f in friends:
        friend_user = user_manager.get_user_by_id(f["friendUserId"])
        results.append({
            "userId": f["friendUserId"],
            "username": friend_user.get("username") if friend_user else "Unknown",
            "name": friend_user.get("name", "") if friend_user else "",
            "since": f.get("since", ""),
        })
    return {
        "friends": results,
        "count": len(results),
        "navigation_url": "friends.html",
    }


def _exec_search_web(args: dict) -> dict:
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = ddgs.text(args["query"], max_results=3)
        snippets = []
        for r in (results or []):
            body = (r.get("body") or "")[:200]
            snippets.append({"title": r.get("title", ""), "snippet": body})
        return {"results": snippets}
    except Exception as e:
        return {"error": f"Web search failed: {str(e)}"}


# Map of tool name -> executor
_TOOL_MAP = {
    "search_businesses": lambda args, uid: _exec_search_businesses(args),
    "get_business_details": lambda args, uid: _exec_get_business_details(args),
    "get_reviews_summary": lambda args, uid: _exec_get_reviews_summary(args),
    "make_reservation": lambda args, uid: _exec_make_reservation(args, uid),
    "get_user_reservations": lambda args, uid: _exec_get_user_reservations(uid),
    "cancel_reservation": lambda args, uid: _exec_cancel_reservation(args, uid),
    "find_deals": lambda args, uid: _exec_find_deals(args),
    "save_business": lambda args, uid: _exec_save_business(args, uid),
    "get_saved_businesses": lambda args, uid: _exec_get_saved_businesses(uid),
    "get_friend_activity": lambda args, uid: _exec_get_friend_activity(uid),
    "get_friends_list": lambda args, uid: _exec_get_friends_list(uid),
    "search_web": lambda args, uid: _exec_search_web(args),
}


# ---------------------------------------------------------------------------
# Conversation management
# ---------------------------------------------------------------------------

def _cleanup_stale_conversations():
    """Remove conversations older than TTL."""
    now = time.time()
    with _conv_lock:
        stale = [k for k, v in _conversations.items() if now - v["lastAccess"] > _CONV_TTL]
        for k in stale:
            del _conversations[k]


def _get_history(user_id: int, session_id: str) -> list:
    key = (user_id, session_id)
    with _conv_lock:
        entry = _conversations.get(key)
        if entry:
            entry["lastAccess"] = time.time()
            return list(entry["history"])
        return []


def _save_history(user_id: int, session_id: str, history: list):
    key = (user_id, session_id)
    # Trim to max length
    if len(history) > _MAX_HISTORY:
        history = history[-_MAX_HISTORY:]
    with _conv_lock:
        _conversations[key] = {"history": history, "lastAccess": time.time()}


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "...[truncated]"


def _compact_for_gemini(result: dict) -> dict:
    """Prepare a tool result dict for Gemini -- keep it structured but compact.

    The google.genai SDK sends function_response as a protobuf Struct, which
    only supports basic JSON types.  We strip verbose fields, shorten strings,
    and cap list lengths so Gemini receives clean structured data instead of a
    truncated JSON blob.
    """
    def _shorten(val, max_str=200, max_list=5, depth=0):
        if depth > 6:
            return str(val)[:max_str] if val else ""
        if isinstance(val, str):
            return val[:max_str]
        if isinstance(val, (int, float, bool)):
            return val
        if val is None:
            return ""
        if isinstance(val, list):
            return [_shorten(item, max_str, max_list, depth + 1) for item in val[:max_list]]
        if isinstance(val, dict):
            return {k: _shorten(v, max_str, max_list, depth + 1) for k, v in val.items()}
        return str(val)[:max_str]

    return _shorten(result)


# ---------------------------------------------------------------------------
# API key pool with automatic rotation
# ---------------------------------------------------------------------------

class _KeyPool:
    """Manages a pool of Gemini API keys with automatic rotation on quota exhaustion.

    Quota is per-project per-model, so multiple keys from the same Google
    account share one quota.  The real value of multiple keys is hedging
    across different Google accounts/projects.
    """

    # Models ordered by free-tier RPD (highest first).
    # Each model has its own separate daily quota.
    MODELS = [
        "gemini-2.5-flash-lite",   # ~1 000 RPD free tier
        "gemini-2.0-flash",        # ~250 RPD free tier
        "gemini-2.5-flash",        # ~20 RPD free tier
    ]

    def __init__(self):
        self._keys: list[str] = []
        # Track exhaustion per (key, model) pair
        self._exhausted: dict[tuple[str, str], float] = {}
        self._current_idx = 0
        self._current_model_idx = 0
        self._lock = threading.Lock()
        self._loaded = False

    def _load_keys(self):
        if self._loaded:
            return
        for var in ("GEMINI_API_KEYS", "GEMINI_API_KEY"):
            raw = os.environ.get(var, "").strip()
            if raw:
                keys = [k.strip() for k in raw.split(",") if k.strip()]
                if keys:
                    self._keys = keys
                    break
        self._loaded = True
        if self._keys:
            log.info("Loaded %d Gemini API key(s), %d model(s) available",
                     len(self._keys), len(self.MODELS))

    def get_client(self) -> tuple:
        """Return (genai.Client, key_label, model_name) for the next available slot.
        Returns (None, None, None) if every key x model combination is exhausted."""
        with self._lock:
            self._load_keys()
            if not self._keys:
                return None, None, None

            now = time.time()
            # Clear entries older than 1 hour
            self._exhausted = {k: t for k, t in self._exhausted.items() if now - t < 3600}

            # Try every (key, model) combination
            for _ in range(len(self.MODELS)):
                model = self.MODELS[self._current_model_idx % len(self.MODELS)]
                for _ in range(len(self._keys)):
                    key = self._keys[self._current_idx % len(self._keys)]
                    if (key, model) not in self._exhausted:
                        client = genai.Client(api_key=key)
                        key_label = key[:8] + "..."
                        return client, key_label, model
                    self._current_idx += 1
                # All keys exhausted for this model, try next model
                self._current_model_idx += 1
                self._current_idx = 0

            return None, None, None

    def mark_exhausted(self, key_label: str, model: str):
        """Mark a (key, model) pair as exhausted and advance."""
        with self._lock:
            for key in self._keys:
                if key.startswith(key_label.replace("...", "")):
                    self._exhausted[(key, model)] = time.time()
                    remaining = (len(self._keys) * len(self.MODELS)) - len(self._exhausted)
                    log.warning("Key %s exhausted for %s (%d slots remaining)",
                                key_label, model, remaining)
                    break
            self._current_idx += 1

    def has_keys(self) -> bool:
        self._load_keys()
        return len(self._keys) > 0

    def all_exhausted(self) -> bool:
        with self._lock:
            now = time.time()
            self._exhausted = {k: t for k, t in self._exhausted.items() if now - t < 3600}
            total_slots = len(self._keys) * len(self.MODELS)
            return len(self._exhausted) >= total_slots


_key_pool = _KeyPool()


# ---------------------------------------------------------------------------
# Gemini API call with retry
# ---------------------------------------------------------------------------

def _extract_retry_delay(err_str: str) -> int:
    """Try to extract the retry delay from a Gemini 429 error message."""
    import re
    match = re.search(r"retry in (\d+)", err_str)
    if match:
        return int(match.group(1))
    return 0


class DailyQuotaExhausted(Exception):
    """Raised when the Gemini daily quota is exhausted (not retryable with this key)."""
    def __init__(self, retry_seconds=0):
        self.retry_seconds = retry_seconds
        super().__init__(f"Daily quota exhausted. Retry in {retry_seconds}s.")


def _call_gemini_with_retry(client, model, contents, config, max_retries=3):
    """Call Gemini generate_content with backoff on rate limits."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            if not response.candidates:
                log.warning("Gemini returned empty candidates")
                raise ValueError("Empty response from Gemini")
            return response
        except DailyQuotaExhausted:
            raise
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "429" in err_str or "resource exhausted" in err_str or "quota" in err_str
            log.error("Gemini API error (attempt %d/%d): %s", attempt + 1, max_retries, e)

            # Daily quota exhaustion -- fail immediately so caller can rotate keys
            if is_rate_limit and "perday" in err_str.replace(" ", "").replace("_", ""):
                delay = _extract_retry_delay(err_str)
                raise DailyQuotaExhausted(retry_seconds=delay)

            if is_rate_limit and attempt < max_retries - 1:
                delay = _extract_retry_delay(err_str)
                wait = max(delay, 5 * (attempt + 1))  # at least 5s, 10s
                log.info("Rate limited, waiting %ds before retry", wait)
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("Gemini API retries exhausted")


# ---------------------------------------------------------------------------
# Main chat function
# ---------------------------------------------------------------------------

def chat(user_id: int, session_id: str, message: str) -> dict:
    """
    Process a user message through the AI agent.
    Automatically rotates API keys on daily quota exhaustion.

    Returns:
        dict with keys: message (str), cards (list), navigation (list)
    """
    _cleanup_stale_conversations()

    if not _key_pool.has_keys():
        return {
            "message": "The AI assistant is not configured. Please set GEMINI_API_KEYS or GEMINI_API_KEY.",
            "cards": [],
            "navigation": [],
            "business_map": {},
        }

    return _chat_with_rotation(user_id, session_id, message)


def _chat_with_rotation(user_id: int, session_id: str, message: str) -> dict:
    """Inner chat function that retries with a new API key/model on quota exhaustion."""

    client, key_label, model = _key_pool.get_client()
    if not client:
        return {
            "message": "All API keys have reached their daily usage limits. Please try again later or add more keys.",
            "cards": [],
            "navigation": [],
            "business_map": {},
        }

    log.info("Using Gemini key %s with model %s", key_label, model)

    today = datetime.utcnow().strftime("%A, %B %d, %Y")
    system_with_date = f"{SYSTEM_PROMPT}\n\nToday's date is {today}."

    config = types.GenerateContentConfig(
        tools=[TOOL_DECLARATIONS],
        system_instruction=system_with_date,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )

    # Restore conversation history and append user message
    history = _get_history(user_id, session_id)
    history.append(types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)],
    ))

    cards = []
    navigation = []
    business_map = {}  # id -> business data, for frontend {{CARD:id}} lookup

    try:
        response = _call_gemini_with_retry(client, model, history, config)
    except DailyQuotaExhausted as e:
        _key_pool.mark_exhausted(key_label, model)
        log.warning("Key %s exhausted on %s, rotating...", key_label, model)
        # Remove the user message we just added (will be re-added on retry)
        if history and history[-1].role == "user":
            history.pop()
            _save_history(user_id, session_id, history)
        return _chat_with_rotation(user_id, session_id, message)
    except Exception as e:
        log.error("Initial Gemini call failed: %s\n%s", e, traceback.format_exc())
        return {
            "message": "I'm having trouble connecting right now. Please try again in a moment.",
            "cards": [],
            "navigation": [],
            "business_map": {},
        }

    # Tool-calling loop
    iterations = 0
    while iterations < _MAX_TOOL_ITERS:
        iterations += 1

        if not response.function_calls:
            break

        # Append the model's response (containing function calls) to history
        model_content = response.candidates[0].content
        history.append(model_content)

        # Execute all function calls in the response
        tool_parts = []
        for fc in response.function_calls:
            fn_name = fc.name
            fn_args = dict(fc.args) if fc.args else {}

            executor = _TOOL_MAP.get(fn_name)
            if not executor:
                result = {"error": f"Unknown tool: {fn_name}"}
            else:
                try:
                    result = executor(fn_args, user_id)
                except Exception as e:
                    result = {"error": f"Tool '{fn_name}' failed: {str(e)}"}

            # Collect navigation events
            nav_url = result.pop("navigation_url", None) if isinstance(result, dict) else None
            if nav_url:
                navigation.append({"url": nav_url, "label": f"Checking {fn_name.replace('_', ' ')}..."})

            # Collect cards from tool results
            if isinstance(result, dict):
                if "businesses" in result and result["businesses"]:
                    for b in result["businesses"]:
                        cards.append({"type": "business", "data": b})
                        if b.get("id"):
                            business_map[b["id"]] = b
                if "business" in result:
                    cards.append({"type": "business", "data": result["business"]})
                    bid = result["business"].get("id")
                    if bid:
                        business_map[bid] = result["business"]
                if "reservation" in result:
                    cards.append({"type": "reservation", "data": result["reservation"]})
                if "deals" in result and result["deals"]:
                    cards.extend([{"type": "deal", "data": d} for d in result["deals"]])

            # Pass structured dict to Gemini (not a JSON string)
            compact = _compact_for_gemini(result) if isinstance(result, dict) else {"result": str(result)[:_MAX_TOOL_RESULT]}

            tool_parts.append(types.Part.from_function_response(
                name=fn_name,
                response=compact,
            ))

        # Append tool results to history
        history.append(types.Content(role="tool", parts=tool_parts))

        # Send tool results back to Gemini
        try:
            response = _call_gemini_with_retry(client, model, history, config)
        except DailyQuotaExhausted:
            _key_pool.mark_exhausted(key_label, model)
            # Try to get a fresh key/model and continue
            new_client, new_label, new_model = _key_pool.get_client()
            if new_client:
                log.info("Rotated to key %s model %s mid-conversation", new_label, new_model)
                client = new_client
                key_label = new_label
                model = new_model
                try:
                    response = _call_gemini_with_retry(client, model, history, config)
                except Exception:
                    fallback_msg = "I found some results but ran into a limit. Here's what I found so far."
                    history.append(types.Content(role="model", parts=[types.Part.from_text(text=fallback_msg)]))
                    _save_history(user_id, session_id, history)
                    return {"message": fallback_msg, "cards": cards, "navigation": navigation, "business_map": business_map}
            else:
                fallback_msg = "All API keys have reached their daily limits. Here's what I found so far."
                history.append(types.Content(role="model", parts=[types.Part.from_text(text=fallback_msg)]))
                _save_history(user_id, session_id, history)
                return {"message": fallback_msg, "cards": cards, "navigation": navigation, "business_map": business_map}
        except Exception as e:
            log.error("Gemini summary call failed: %s\n%s", e, traceback.format_exc())
            # Add a synthetic model response so history stays well-formed
            # (must end with model role, not tool role, for future calls)
            fallback_msg = "I found some results but had trouble summarizing them. Here's what I found so far."
            history.append(types.Content(
                role="model",
                parts=[types.Part.from_text(text=fallback_msg)],
            ))
            _save_history(user_id, session_id, history)
            return {
                "message": fallback_msg,
                "cards": cards,
                "navigation": navigation,
                "business_map": business_map,
            }

    # Append the final model response to history
    try:
        final_content = response.candidates[0].content
        history.append(final_content)
    except (IndexError, AttributeError):
        pass

    # Extract final text response
    final_text = ""
    try:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                final_text += part.text
    except (IndexError, AttributeError):
        final_text = "I processed your request but couldn't generate a summary."

    if not final_text:
        final_text = "I processed your request but couldn't generate a summary."

    # Save updated history
    _save_history(user_id, session_id, history)

    return {
        "message": final_text,
        "cards": cards,
        "navigation": navigation,
        "business_map": business_map,
    }
