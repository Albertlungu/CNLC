"""
./backend/core/agent_manager.py

AI agent powered by Gemini with function calling.
Orchestrates tool calls to existing core managers, manages conversation
state server-side, and returns structured responses for the frontend.
"""

import json
import os
import re
import time
import threading
from datetime import datetime
from typing import Optional

import google.generativeai as genai

from backend.core import business_manager, reservation_manager, review_manager, deal_manager, saved_manager, friend_manager
from backend.storage.json_handler import load_businesses

# ---------------------------------------------------------------------------
# Server-side conversation store  (userId -> {history, lastAccess})
# ---------------------------------------------------------------------------
_conversations: dict = {}
_conv_lock = threading.Lock()
_CONV_TTL = 3600        # 1 hour
_MAX_HISTORY = 50       # messages kept per conversation
_MAX_TOOL_ITERS = 10
_MAX_TOOL_RESULT = 5000  # chars

SYSTEM_PROMPT = """You are the CNLC assistant -- a helpful AI concierge for discovering and interacting with local businesses across Canada.

You have access to tools that let you search businesses, read reviews, make reservations, find deals, save favorites, and look up web information. Use them proactively to answer the user's questions.

Guidelines:
- When the user asks for a recommendation, search for matching businesses and present 2-4 options with key details (name, category, address, rating).
- Always CONFIRM with the user before making a reservation or saving a business. State the details and ask "Shall I go ahead?"
- When presenting businesses, include the business ID so the frontend can render cards.
- Keep responses concise but informative.
- If a tool call fails, explain the issue simply and suggest an alternative.
- You can chain multiple tool calls to build a complete answer (e.g., search businesses, then get reviews for the top result).
- For date/time references like "this Friday" or "tomorrow", calculate the actual date based on today's date which is provided in the context.
- Never fabricate business data. Only present information returned by your tools.
"""

# ---------------------------------------------------------------------------
# Tool declarations for Gemini function calling
# ---------------------------------------------------------------------------

TOOL_DECLARATIONS = [
    genai.protos.Tool(function_declarations=[
        genai.protos.FunctionDeclaration(
            name="search_businesses",
            description="Search for businesses by name, category, or location. Returns a list of matching businesses.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "query": genai.protos.Schema(type=genai.protos.Type.STRING, description="Search query (business name or keyword)"),
                    "category": genai.protos.Schema(type=genai.protos.Type.STRING, description="Business category filter (e.g. restaurant, cafe, bakery, hairdresser, beauty, clothes, convenience, supermarket)"),
                    "city": genai.protos.Schema(type=genai.protos.Type.STRING, description="City to search in (e.g. Ottawa, Toronto, Vancouver, Calgary, Edmonton, Winnipeg, Regina)"),
                },
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="get_business_details",
            description="Get full details of a specific business by its ID.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "business_id": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="The business ID"),
                },
                required=["business_id"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="get_reviews_summary",
            description="Get reviews for a business including average rating and top reviews.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "business_id": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="The business ID"),
                },
                required=["business_id"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="make_reservation",
            description="Create a reservation at a business. Always confirm details with the user before calling this.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "business_id": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="The business ID"),
                    "business_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="The business name"),
                    "date": genai.protos.Schema(type=genai.protos.Type.STRING, description="Reservation date in YYYY-MM-DD format"),
                    "time": genai.protos.Schema(type=genai.protos.Type.STRING, description="Reservation time in HH:MM format (24h)"),
                    "party_size": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="Number of guests"),
                    "notes": genai.protos.Schema(type=genai.protos.Type.STRING, description="Optional notes for the reservation"),
                },
                required=["business_id", "business_name", "date", "time", "party_size"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="get_user_reservations",
            description="Get all reservations for the current user.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={},
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="cancel_reservation",
            description="Cancel a reservation. Always confirm with the user before calling this.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "reservation_id": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="The reservation ID to cancel"),
                },
                required=["reservation_id"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="find_deals",
            description="Find active deals/coupons for a specific business.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "business_id": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="The business ID"),
                },
                required=["business_id"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="save_business",
            description="Save a business to the user's collection. Always confirm with the user first.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "business_id": genai.protos.Schema(type=genai.protos.Type.INTEGER, description="The business ID to save"),
                    "collection_name": genai.protos.Schema(type=genai.protos.Type.STRING, description="Name of the collection to save to (created if it doesn't exist). Defaults to 'Favorites'."),
                },
                required=["business_id"],
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="get_saved_businesses",
            description="Get all businesses the user has saved.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={},
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="get_friend_activity",
            description="Get recent activity (reviews) from the user's friends.",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={},
            ),
        ),
        genai.protos.FunctionDeclaration(
            name="search_web",
            description="Search the web for additional information about a business (menus, atmosphere, hours, etc).",
            parameters=genai.protos.Schema(
                type=genai.protos.Type.OBJECT,
                properties={
                    "query": genai.protos.Schema(type=genai.protos.Type.STRING, description="The search query"),
                },
                required=["query"],
            ),
        ),
    ])
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

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

    results = results[:15]
    return {
        "businesses": [
            {
                "id": b.get("id"),
                "name": b.get("name"),
                "category": b.get("category"),
                "address": b.get("address"),
                "phone": b.get("phone"),
                "website": b.get("website"),
                "image_url": b.get("image_url"),
                "opening_hours": b.get("opening_hours"),
            }
            for b in results
        ],
        "count": len(results),
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
    deals = deal_manager.get_deals(business_id=args["business_id"], active_only=True)
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
            return entry["history"]
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


# ---------------------------------------------------------------------------
# Gemini API call with retry
# ---------------------------------------------------------------------------

def _call_gemini_with_retry(chat, message_parts, max_retries=3):
    """Call Gemini with exponential backoff on rate limits."""
    for attempt in range(max_retries):
        try:
            response = chat.send_message(message_parts)
            # Validate response has content
            if not response.candidates:
                raise ValueError("Empty response from Gemini")
            return response
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = "429" in err_str or "resource exhausted" in err_str or "quota" in err_str
            if is_rate_limit and attempt < max_retries - 1:
                wait = (2 ** attempt)  # 1s, 2s, 4s
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

    Returns:
        dict with keys: message (str), cards (list), navigation (list)
    """
    _cleanup_stale_conversations()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "message": "The AI assistant is not configured. Please set the GEMINI_API_KEY.",
            "cards": [],
            "navigation": [],
        }

    genai.configure(api_key=api_key)

    today = datetime.utcnow().strftime("%A, %B %d, %Y")
    system_with_date = f"{SYSTEM_PROMPT}\n\nToday's date is {today}."

    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        tools=TOOL_DECLARATIONS,
        system_instruction=system_with_date,
    )

    # Restore conversation history
    history = _get_history(user_id, session_id)

    try:
        chat_session = model.start_chat(history=history)
    except Exception:
        # If history is corrupted, start fresh
        history = []
        chat_session = model.start_chat(history=[])

    cards = []
    navigation = []

    try:
        response = _call_gemini_with_retry(chat_session, message)
    except Exception as e:
        return {
            "message": "I'm having trouble connecting right now. Please try again in a moment.",
            "cards": [],
            "navigation": [],
        }

    # Tool-calling loop
    iterations = 0
    while iterations < _MAX_TOOL_ITERS:
        iterations += 1

        # Check if response has function calls
        candidate = response.candidates[0]
        has_function_call = False

        for part in candidate.content.parts:
            if part.function_call and part.function_call.name:
                has_function_call = True
                break

        if not has_function_call:
            break

        # Execute all function calls in the response
        tool_responses = []
        for part in candidate.content.parts:
            if not (part.function_call and part.function_call.name):
                continue

            fn_name = part.function_call.name
            fn_args = dict(part.function_call.args) if part.function_call.args else {}

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

            # Collect cards from business search results
            if isinstance(result, dict):
                if "businesses" in result and result["businesses"]:
                    cards.extend([{"type": "business", "data": b} for b in result["businesses"]])
                if "business" in result:
                    cards.append({"type": "business", "data": result["business"]})
                if "reservation" in result:
                    cards.append({"type": "reservation", "data": result["reservation"]})
                if "deals" in result and result["deals"]:
                    cards.extend([{"type": "deal", "data": d} for d in result["deals"]])

            # Truncate tool result before sending back
            result_str = _truncate(json.dumps(result, default=str), _MAX_TOOL_RESULT)

            tool_responses.append(
                genai.protos.Part(function_response=genai.protos.FunctionResponse(
                    name=fn_name,
                    response={"result": result_str},
                ))
            )

        # Send tool results back to Gemini
        try:
            response = _call_gemini_with_retry(chat_session, tool_responses)
        except Exception:
            # If Gemini fails mid-loop, return what we have
            _save_history(user_id, session_id, chat_session.history)
            return {
                "message": "I found some results but had trouble summarizing them. Here's what I found so far.",
                "cards": cards,
                "navigation": navigation,
            }

    # Extract final text response
    final_text = ""
    try:
        for part in response.candidates[0].content.parts:
            if part.text:
                final_text += part.text
    except (IndexError, AttributeError):
        final_text = "I processed your request but couldn't generate a summary."

    # Save updated history
    _save_history(user_id, session_id, chat_session.history)

    return {
        "message": final_text,
        "cards": cards,
        "navigation": navigation,
    }
